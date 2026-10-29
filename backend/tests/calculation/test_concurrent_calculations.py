"""
Concurrent Calculation Test Suite for PCF Calculator.

TASK-BE-P7-042: Concurrent Calculation Tests

This module tests the PCF calculator under concurrent execution.
"""

import asyncio
import time
import tracemalloc
from typing import Dict, Optional

import pytest

from backend.calculator.exceptions import EmissionFactorNotFoundError
from backend.calculator.pcf_calculator import (
    BOMItem,
    CalculationResult,
    PCFCalculator,
)
from backend.calculator.providers import EmissionFactorDTO, EmissionFactorProvider
from backend.calculator.cache import CachedEmissionFactorProvider


class MockEmissionFactorProvider(EmissionFactorProvider):
    def __init__(
        self,
        factors: Optional[Dict[str, float]] = None,
        delay_seconds: float = 0.0,
    ):
        self._factors = factors or {
            "steel": 2.5,
            "aluminum": 8.0,
            "plastic": 3.2,
            "electronics": 50.0,
            "copper": 4.5,
            "glass": 1.2,
            "rubber": 3.8,
            "cotton": 5.89,
            "polyester": 6.4,
        }
        self._delay = delay_seconds
        self.access_count = 0
        self.get_all_count = 0
        self._lock = asyncio.Lock()

    async def get_by_category(self, category: str) -> Optional[EmissionFactorDTO]:
        async with self._lock:
            self.access_count += 1
        if self._delay > 0:
            await asyncio.sleep(self._delay)
        if category not in self._factors:
            return None
        return EmissionFactorDTO(
            id=f"ef-mock-{category}",
            category=category,
            co2e_kg=self._factors[category],
            unit="kg",
            data_source="mock_test_data",
            uncertainty=0.1,
        )

    async def get_all(self) -> Dict[str, EmissionFactorDTO]:
        async with self._lock:
            self.get_all_count += 1
        if self._delay > 0:
            await asyncio.sleep(self._delay)
        return {
            category: EmissionFactorDTO(
                id=f"ef-mock-{category}",
                category=category,
                co2e_kg=co2e,
                unit="kg",
                data_source="mock_test_data",
                uncertainty=0.1,
            )
            for category, co2e in self._factors.items()
        }


@pytest.fixture
def mock_provider():
    return MockEmissionFactorProvider(
        factors={
            "steel": 2.5,
            "aluminum": 8.0,
            "plastic": 3.2,
            "electronics": 50.0,
            "copper": 4.5,
            "glass": 1.2,
            "rubber": 3.8,
            "cotton": 5.89,
            "polyester": 6.4,
        }
    )


@pytest.fixture
def mock_provider_with_delay():
    return MockEmissionFactorProvider(
        factors={
            "steel": 2.5,
            "aluminum": 8.0,
            "plastic": 3.2,
            "electronics": 50.0,
            "copper": 4.5,
        },
        delay_seconds=0.01,
    )


@pytest.fixture
def calculator(mock_provider):
    return PCFCalculator(ef_provider=mock_provider)


@pytest.fixture
def cached_provider(mock_provider):
    return CachedEmissionFactorProvider(mock_provider, ttl_seconds=60)


@pytest.fixture
def cached_calculator(cached_provider):
    return PCFCalculator(ef_provider=cached_provider)


async def calculate_with_timeout(
    calculator: PCFCalculator,
    product_id: str,
    bom_items: list,
    timeout: float = 5.0,
):
    return await asyncio.wait_for(
        calculator.calculate(product_id, bom_items),
        timeout=timeout,
    )


class TestParallelCalculations:
    @pytest.mark.asyncio
    async def test_parallel_calculations_independent(self, calculator):
        bom_1 = [BOMItem(material="steel", quantity=10.0, unit="kg")]
        bom_2 = [BOMItem(material="aluminum", quantity=5.0, unit="kg")]
        bom_3 = [BOMItem(material="plastic", quantity=20.0, unit="kg")]
        results = await asyncio.gather(
            calculator.calculate("product-1", bom_1),
            calculator.calculate("product-2", bom_2),
            calculator.calculate("product-3", bom_3),
        )
        result_1, result_2, result_3 = results
        assert result_1.breakdown[0].material == "steel"
        assert result_1.breakdown[0].quantity == 10.0
        assert result_1.total_co2e == pytest.approx(25.0, rel=0.01)
        assert result_2.breakdown[0].material == "aluminum"
        assert result_2.breakdown[0].quantity == 5.0
        assert result_2.total_co2e == pytest.approx(40.0, rel=0.01)
        assert result_3.breakdown[0].material == "plastic"
        assert result_3.breakdown[0].quantity == 20.0
        assert result_3.total_co2e == pytest.approx(64.0, rel=0.01)
        assert result_1.total_co2e != result_2.total_co2e
        assert result_2.total_co2e != result_3.total_co2e

    @pytest.mark.asyncio
    async def test_parallel_calculations_multi_item_bom(self, calculator):
        bom_1 = [
            BOMItem(material="steel", quantity=5.0, unit="kg"),
            BOMItem(material="plastic", quantity=2.0, unit="kg"),
        ]
        bom_2 = [
            BOMItem(material="aluminum", quantity=3.0, unit="kg"),
            BOMItem(material="copper", quantity=1.0, unit="kg"),
        ]
        results = await asyncio.gather(
            calculator.calculate("product-a", bom_1),
            calculator.calculate("product-b", bom_2),
        )
        result_1, result_2 = results
        expected_1 = (5.0 * 2.5) + (2.0 * 3.2)
        assert result_1.total_co2e == pytest.approx(expected_1, rel=0.01)
        assert len(result_1.breakdown) == 2
        expected_2 = (3.0 * 8.0) + (1.0 * 4.5)
        assert result_2.total_co2e == pytest.approx(expected_2, rel=0.01)
        assert len(result_2.breakdown) == 2


class TestHighConcurrency:
    @pytest.mark.asyncio
    async def test_high_concurrency_stress_50_requests(self, calculator):
        boms = [
            [BOMItem(material="steel", quantity=float(i + 1), unit="kg")]
            for i in range(50)
        ]
        results = await asyncio.gather(
            *[
                calculator.calculate(f"product-{i}", bom)
                for i, bom in enumerate(boms)
            ],
            return_exceptions=True,
        )
        assert len(results) == 50
        assert all(not isinstance(r, Exception) for r in results)
        for i, result in enumerate(results):
            expected_quantity = float(i + 1)
            assert result.breakdown[0].quantity == expected_quantity
            expected_co2e = expected_quantity * 2.5
            assert result.total_co2e == pytest.approx(expected_co2e, rel=0.01)

    @pytest.mark.asyncio
    async def test_high_concurrency_100_requests(self, calculator):
        materials = ["steel", "aluminum", "plastic", "copper", "glass"]
        boms = [
            [BOMItem(material=materials[i % len(materials)], quantity=1.0, unit="kg")]
            for i in range(100)
        ]
        results = await asyncio.wait_for(
            asyncio.gather(
                *[
                    calculator.calculate(f"stress-{i}", bom)
                    for i, bom in enumerate(boms)
                ],
                return_exceptions=True,
            ),
            timeout=30.0,
        )
        assert len(results) == 100
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"


class TestCacheThreadSafety:
    @pytest.mark.asyncio
    async def test_shared_cache_thread_safety(self, mock_provider):
        cached_provider = CachedEmissionFactorProvider(mock_provider, ttl_seconds=60)
        calculator = PCFCalculator(ef_provider=cached_provider)
        bom = [BOMItem(material="steel", quantity=1.0, unit="kg")]
        results = await asyncio.gather(
            *[calculator.calculate(f"cache-test-{i}", bom) for i in range(20)]
        )
        first_total = results[0].total_co2e
        assert all(r.total_co2e == first_total for r in results)
        metrics = cached_provider.get_metrics()
        assert metrics["hits"] >= 15

    @pytest.mark.asyncio
    async def test_cache_consistency_different_materials(self, mock_provider):
        cached_provider = CachedEmissionFactorProvider(mock_provider, ttl_seconds=60)
        calculator = PCFCalculator(ef_provider=cached_provider)
        boms = [
            [BOMItem(material="steel", quantity=1.0, unit="kg")],
            [BOMItem(material="aluminum", quantity=1.0, unit="kg")],
            [BOMItem(material="plastic", quantity=1.0, unit="kg")],
            [BOMItem(material="copper", quantity=1.0, unit="kg")],
        ]
        tasks = []
        for i in range(5):
            for j, bom in enumerate(boms):
                tasks.append(calculator.calculate(f"multi-{i}-{j}", bom))
        results = await asyncio.gather(*tasks)
        assert len(results) == 20
        steel_results = [r for r in results if r.breakdown[0].material == "steel"]
        aluminum_results = [r for r in results if r.breakdown[0].material == "aluminum"]
        assert len(steel_results) == 5
        assert len(aluminum_results) == 5
        assert all(r.total_co2e == steel_results[0].total_co2e for r in steel_results)
        assert all(
            r.total_co2e == aluminum_results[0].total_co2e for r in aluminum_results
        )


class TestErrorIsolation:
    @pytest.mark.asyncio
    async def test_error_isolation_missing_material(self, calculator):
        bom_valid = [BOMItem(material="steel", quantity=10.0, unit="kg")]
        bom_invalid = [BOMItem(material="nonexistent_xyz", quantity=10.0, unit="kg")]
        results = await asyncio.gather(
            calculator.calculate("valid-1", bom_valid),
            calculator.calculate("invalid", bom_invalid),
            calculator.calculate("valid-2", bom_valid),
            return_exceptions=True,
        )
        assert isinstance(results[0], CalculationResult)
        assert isinstance(results[2], CalculationResult)
        assert isinstance(results[1], EmissionFactorNotFoundError)
        assert "nonexistent_xyz" in str(results[1])
        assert results[0].breakdown[0].material == "steel"
        assert results[2].breakdown[0].material == "steel"
        assert results[0].total_co2e == results[2].total_co2e

    @pytest.mark.asyncio
    async def test_error_isolation_multiple_failures(self, calculator):
        valid_bom = [BOMItem(material="aluminum", quantity=5.0, unit="kg")]
        invalid_bom_1 = [BOMItem(material="unknown_a", quantity=1.0, unit="kg")]
        invalid_bom_2 = [BOMItem(material="unknown_b", quantity=2.0, unit="kg")]
        results = await asyncio.gather(
            calculator.calculate("v1", valid_bom),
            calculator.calculate("i1", invalid_bom_1),
            calculator.calculate("v2", valid_bom),
            calculator.calculate("i2", invalid_bom_2),
            calculator.calculate("v3", valid_bom),
            return_exceptions=True,
        )
        successes = [r for r in results if isinstance(r, CalculationResult)]
        failures = [r for r in results if isinstance(r, Exception)]
        assert len(successes) == 3
        assert len(failures) == 2
        for success in successes:
            assert success.total_co2e == pytest.approx(40.0, rel=0.01)


class TestInitializationConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_calculations_same_calculator(self, mock_provider):
        calculator = PCFCalculator(ef_provider=mock_provider)
        bom = [BOMItem(material="steel", quantity=5.0, unit="kg")]
        results = await asyncio.gather(
            calculator.calculate("init-1", bom),
            calculator.calculate("init-2", bom),
            calculator.calculate("init-3", bom),
            calculator.calculate("init-4", bom),
            calculator.calculate("init-5", bom),
        )
        assert len(results) == 5
        assert all(r.total_co2e > 0 for r in results)
        assert all(r.breakdown[0].material == "steel" for r in results)

    @pytest.mark.asyncio
    async def test_new_calculator_per_request(self, mock_provider):
        async def create_and_calculate(provider, product_id: str, quantity: float):
            calc = PCFCalculator(ef_provider=provider)
            bom = [BOMItem(material="aluminum", quantity=quantity, unit="kg")]
            return await calc.calculate(product_id, bom)
        results = await asyncio.gather(
            *[
                create_and_calculate(mock_provider, f"new-calc-{i}", float(i + 1))
                for i in range(10)
            ]
        )
        assert len(results) == 10
        for i, result in enumerate(results):
            expected = (i + 1) * 8.0
            assert result.total_co2e == pytest.approx(expected, rel=0.01)


class TestMemoryStability:
    @pytest.mark.asyncio
    async def test_memory_stability_sustained_load(self, mock_provider):
        tracemalloc.start()
        calculator = PCFCalculator(ef_provider=mock_provider)
        bom = [BOMItem(material="steel", quantity=10.0, unit="kg")]
        for batch in range(10):
            results = await asyncio.gather(
                *[calculator.calculate(f"mem-{batch}-{i}", bom) for i in range(10)]
            )
            assert len(results) == 10
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert peak < 50 * 1024 * 1024, f"Peak memory {peak / 1024 / 1024:.2f} MB exceeds limit"
        assert current < 25 * 1024 * 1024, f"Current memory {current / 1024 / 1024:.2f} MB exceeds limit"

    @pytest.mark.asyncio
    async def test_memory_with_cache_under_load(self, mock_provider):
        tracemalloc.start()
        cached_provider = CachedEmissionFactorProvider(mock_provider, ttl_seconds=60)
        calculator = PCFCalculator(ef_provider=cached_provider)
        materials = ["steel", "aluminum", "plastic", "copper", "glass"]
        for batch in range(20):
            boms = [
                [BOMItem(material=materials[i % len(materials)], quantity=1.0, unit="kg")]
                for i in range(10)
            ]
            results = await asyncio.gather(
                *[
                    calculator.calculate(f"cache-mem-{batch}-{i}", bom)
                    for i, bom in enumerate(boms)
                ]
            )
            assert len(results) == 10
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert peak < 50 * 1024 * 1024, f"Peak memory with cache {peak / 1024 / 1024:.2f} MB"


class TestDeadlockPrevention:
    @pytest.mark.asyncio
    async def test_no_deadlock_complex_bom(self, calculator):
        complex_bom = [
            BOMItem(material="steel", quantity=10.0, unit="kg"),
            BOMItem(material="aluminum", quantity=5.0, unit="kg"),
            BOMItem(material="electronics", quantity=2.0, unit="kg"),
            BOMItem(material="plastic", quantity=15.0, unit="kg"),
        ]
        results = await asyncio.gather(
            *[
                calculate_with_timeout(calculator, f"complex-{i}", complex_bom, timeout=5.0)
                for i in range(10)
            ]
        )
        assert len(results) == 10
        assert all(len(r.breakdown) == 4 for r in results)

    @pytest.mark.asyncio
    async def test_no_deadlock_with_cached_provider(self, mock_provider):
        cached_provider = CachedEmissionFactorProvider(mock_provider, ttl_seconds=60)
        calculator = PCFCalculator(ef_provider=cached_provider)
        boms = [
            [
                BOMItem(material="steel", quantity=float(i), unit="kg"),
                BOMItem(material="aluminum", quantity=float(i + 1), unit="kg"),
            ]
            for i in range(1, 21)
        ]
        results = await asyncio.wait_for(
            asyncio.gather(
                *[calculator.calculate(f"lock-{i}", bom) for i, bom in enumerate(boms)]
            ),
            timeout=10.0,
        )
        assert len(results) == 20

    @pytest.mark.asyncio
    async def test_no_deadlock_rapid_cache_clear(self, mock_provider):
        cached_provider = CachedEmissionFactorProvider(mock_provider, ttl_seconds=60)
        calculator = PCFCalculator(ef_provider=cached_provider)
        bom = [BOMItem(material="steel", quantity=1.0, unit="kg")]
        async def calculate_and_clear():
            for _ in range(5):
                await calculator.calculate("rapid", bom)
                cached_provider.clear_cache()
                await asyncio.sleep(0.001)
        await asyncio.wait_for(
            asyncio.gather(*[calculate_and_clear() for _ in range(5)]),
            timeout=10.0,
        )


class TestConcurrentEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_bom_concurrent(self, calculator):
        empty_bom = []
        valid_bom = [BOMItem(material="steel", quantity=5.0, unit="kg")]
        results = await asyncio.gather(
            calculator.calculate("empty-1", empty_bom),
            calculator.calculate("valid-1", valid_bom),
            calculator.calculate("empty-2", empty_bom),
            calculator.calculate("valid-2", valid_bom),
        )
        assert results[0].total_co2e == 0.0
        assert results[2].total_co2e == 0.0
        assert results[1].total_co2e == results[3].total_co2e

    @pytest.mark.asyncio
    async def test_zero_quantity_concurrent(self, calculator):
        zero_bom = [BOMItem(material="steel", quantity=0.0, unit="kg")]
        normal_bom = [BOMItem(material="steel", quantity=10.0, unit="kg")]
        results = await asyncio.gather(
            calculator.calculate("zero", zero_bom),
            calculator.calculate("normal", normal_bom),
        )
        assert results[0].total_co2e == 0.0
        assert results[1].total_co2e == pytest.approx(25.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_same_product_id_concurrent(self, calculator):
        bom_small = [BOMItem(material="steel", quantity=1.0, unit="kg")]
        bom_large = [BOMItem(material="steel", quantity=100.0, unit="kg")]
        results = await asyncio.gather(
            calculator.calculate("same-id", bom_small),
            calculator.calculate("same-id", bom_large),
        )
        totals = sorted([r.total_co2e for r in results])
        assert totals[0] == pytest.approx(2.5, rel=0.01)
        assert totals[1] == pytest.approx(250.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_very_large_quantity_concurrent(self, calculator):
        boms = [
            [BOMItem(material="steel", quantity=1e6, unit="kg")],
            [BOMItem(material="aluminum", quantity=1e6, unit="kg")],
            [BOMItem(material="plastic", quantity=1e6, unit="kg")],
        ]
        results = await asyncio.gather(
            *[calculator.calculate(f"large-{i}", bom) for i, bom in enumerate(boms)]
        )
        assert results[0].total_co2e == pytest.approx(2.5e6, rel=0.01)
        assert results[1].total_co2e == pytest.approx(8.0e6, rel=0.01)
        assert results[2].total_co2e == pytest.approx(3.2e6, rel=0.01)

    @pytest.mark.asyncio
    async def test_provider_delay_does_not_block(self, mock_provider_with_delay):
        calculator = PCFCalculator(ef_provider=mock_provider_with_delay)
        boms = [[BOMItem(material="steel", quantity=1.0, unit="kg")] for _ in range(10)]
        start_time = time.time()
        results = await asyncio.gather(
            *[calculator.calculate(f"delay-{i}", bom) for i, bom in enumerate(boms)]
        )
        elapsed = time.time() - start_time
        assert len(results) == 10
        assert elapsed < 0.1, f"Calculations took {elapsed:.3f}s, expected < 0.1s"


class TestConcurrencyConsistency:
    @pytest.mark.asyncio
    async def test_consistency_multiple_runs(self, calculator):
        bom = [
            BOMItem(material="steel", quantity=5.0, unit="kg"),
            BOMItem(material="plastic", quantity=3.0, unit="kg"),
        ]
        expected_total = (5.0 * 2.5) + (3.0 * 3.2)
        for run in range(5):
            results = await asyncio.gather(
                *[calculator.calculate(f"consistency-{run}-{i}", bom) for i in range(10)]
            )
            for result in results:
                assert result.total_co2e == pytest.approx(expected_total, rel=0.001)

    @pytest.mark.asyncio
    async def test_no_flaky_failures(self, calculator):
        bom = [BOMItem(material="copper", quantity=2.0, unit="kg")]
        results = await asyncio.gather(
            *[calculator.calculate(f"flaky-{i}", bom) for i in range(100)],
            return_exceptions=True,
        )
        failures = [r for r in results if isinstance(r, Exception)]
        assert len(failures) == 0, f"Unexpected failures: {failures}"
