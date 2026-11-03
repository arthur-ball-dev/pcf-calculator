"""
Route modules reach the database only through domain services (issue #19).

auth.py and health.py are exempt: authentication has its own backend/auth layer, and
the readiness probe's job is to run a raw query. The routes under api/routes/admin are
not scanned; they were out of scope for #19 and still use the ORM directly.
"""

import ast
from pathlib import Path

import pytest

ROUTES_DIR = Path(__file__).resolve().parents[2] / "api" / "routes"
EXEMPT = {"__init__.py", "auth.py", "health.py"}
DATABASE_CALLS = {"query", "add", "add_all", "commit", "delete", "execute", "flush", "refresh", "rollback"}
ALLOWED_MODEL_IMPORTS = {"backend.models.user"}


def violations(code: str) -> list[str]:
    """List direct database use in a route module's source."""
    found = []
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.ImportFrom) and node.module:
            is_model = node.module == "backend.models" or node.module.startswith("backend.models.")
            if is_model and node.module not in ALLOWED_MODEL_IMPORTS:
                found.append(f"line {node.lineno}: imports {node.module}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            receiver = node.func.value
            if node.func.attr in DATABASE_CALLS and not (
                isinstance(receiver, ast.Name) and receiver.id == "router"
            ):
                found.append(f"line {node.lineno}: calls .{node.func.attr}()")
    return found


ROUTE_MODULES = sorted(p for p in ROUTES_DIR.glob("*.py") if p.name not in EXEMPT)


def test_the_scan_covers_the_expected_modules():
    assert {p.name for p in ROUTE_MODULES} == {
        "calculations.py",
        "emission_factors.py",
        "product_categories.py",
        "product_search.py",
        "products.py",
    }


@pytest.mark.parametrize("module", ROUTE_MODULES, ids=lambda p: p.name)
def test_route_module_uses_no_orm(module):
    assert violations(module.read_text()) == []


@pytest.mark.parametrize(
    "code",
    [
        "from backend.models import Product",
        "from backend.models.product import Product",
        "def route(db):\n    db.query(Product).all()",
        "def route(session):\n    session.execute(statement)",
        "def route(db):\n    db.commit()",
    ],
)
def test_the_check_catches_direct_database_use(code):
    assert violations(code) != []


@pytest.mark.parametrize(
    "code",
    [
        "from backend.models.user import User",
        "@router.delete('/x')\ndef route():\n    pass",
        "def route(service):\n    service.delete_factor('x')",
        "def route(tasks):\n    tasks.add_task(run)",
    ],
)
def test_the_check_allows_normal_route_code(code):
    assert violations(code) == []
