"""
Product, search and category routes on the domain layer (issue #19).

Repositories run on a real session. Services run on stub repositories, so the tree
and relevance rules are tested without a database. Routes run against a replaced
service, which proves they read nothing else.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from backend.api.dependencies import get_category_service, get_product_service
from backend.domain.entities.category import Category, CategoryNode, CategoryTree
from backend.domain.entities.errors import CategoryNotFoundError, ProductNotFoundError
from backend.domain.entities.product import (
    BOMItem,
    CategorySummary,
    Product as DomainProduct,
    ProductPage,
    ProductSearchCriteria,
    ProductSearchResult,
    ProductWithBOM,
    ScoredProduct,
)
from backend.domain.repositories.interfaces import CategoryRepository, ProductRepository
from backend.domain.services.category_service import CategoryService
from backend.domain.services.product_service import ProductService, score_relevance
from backend.infrastructure.repositories.sqlalchemy_category_repository import (
    SQLAlchemyCategoryRepository,
)
from backend.infrastructure.repositories.sqlalchemy_product_repository import (
    SQLAlchemyProductRepository,
)
from backend.models import BillOfMaterials, Product, ProductCategory

PRODUCTS = "/api/v1/products"
SEARCH = "/api/v1/products/search"
CATEGORIES = "/api/v1/products/categories"
CREATED = datetime(2026, 1, 2, tzinfo=timezone.utc)


def _product(id_="p", name="Widget", **fields):
    return DomainProduct(id=id_, code=id_.upper(), name=name, unit="kg", **fields)


@pytest.fixture
def catalog(db_session):
    parent = ProductCategory(id="wire-cat", code="WIRE-CAT", name="Wire", level=0, industry_sector="electronics")
    child = ProductCategory(id="wire-sub", code="WIRE-SUB", name="Sub", level=1, parent_id="wire-cat")
    db_session.add_all([parent, child])
    db_session.commit()
    finished = Product(
        id="wire-a", code="WIRE-A", name="Aaa wire finished", unit="unit", is_finished_product=True,
        category_id="wire-cat", manufacturer="Acme", country_of_origin="US",
    )
    component = Product(
        id="wire-b", code="WIRE-B", name="Bbb wire component", unit="kg", is_finished_product=False,
        category_id="wire-sub",
    )
    db_session.add_all([finished, component])
    db_session.commit()
    db_session.add(
        BillOfMaterials(
            id="wire-bom", parent_product_id="wire-a", child_product_id="wire-b",
            quantity=2.5, unit="kg", notes="note",
        )
    )
    db_session.commit()


class TestProductRepository:
    def test_list_all_filters_and_counts(self, db_session, catalog):
        repo = SQLAlchemyProductRepository(db_session)

        finished = repo.list_all(limit=1000, is_finished_product=True)
        components = repo.list_all(limit=1000, is_finished_product=False)

        assert "wire-a" in {p.id for p in finished.items}
        assert "wire-a" not in {p.id for p in components.items}
        assert finished.total == len(finished.items)

    def test_list_all_total_ignores_the_page(self, db_session, catalog):
        page = SQLAlchemyProductRepository(db_session).list_all(limit=1)

        assert len(page.items) == 1
        assert page.total >= 2

    def test_list_all_is_ordered_by_name(self, db_session, catalog):
        names = [p.name for p in SQLAlchemyProductRepository(db_session).list_all(limit=1000).items]

        assert names == sorted(names) or names.index("Aaa wire finished") < names.index("Bbb wire component")

    def test_get_with_bom_maps_every_field(self, db_session, catalog):
        found = SQLAlchemyProductRepository(db_session).get_with_bom("wire-a")

        item = found.bom_items[0]
        assert found.product.is_finished_product is True
        assert found.product.created_at is not None
        assert (item.id, item.component_id, item.component_name) == ("wire-bom", "wire-b", "Bbb wire component")
        assert (item.quantity, item.unit, item.notes) == (2.5, "kg", "note")

    def test_search_returns_the_linked_category(self, db_session, catalog):
        page = SQLAlchemyProductRepository(db_session).search(ProductSearchCriteria(query="aaa wire"))

        assert [p.id for p in page.items] == ["wire-a"]
        assert page.items[0].category_info == CategorySummary(
            id="wire-cat", code="WIRE-CAT", name="Wire", industry_sector="electronics"
        )
        assert page.items[0].manufacturer == "Acme"

    def test_list_does_not_load_categories(self, db_session, catalog):
        page = SQLAlchemyProductRepository(db_session).list_all(limit=1000)

        assert all(p.category_info is None for p in page.items)


class TestCategoryRepository:
    def test_get_by_id(self, db_session, catalog):
        repo = SQLAlchemyCategoryRepository(db_session)

        assert repo.get_by_id("wire-sub").parent_id == "wire-cat"
        assert repo.get_by_id("wire-none") is None

    def test_list_all_filters_by_industry(self, db_session, catalog):
        found = SQLAlchemyCategoryRepository(db_session).list_all(industry="electronics")

        assert "wire-cat" in {c.id for c in found}
        assert "wire-sub" not in {c.id for c in found}

    def test_count_products(self, db_session, catalog):
        repo = SQLAlchemyCategoryRepository(db_session)

        assert repo.count_products("wire-cat") == 1
        assert repo.count_products("wire-none") == 0


class TestScoreRelevance:
    def test_no_text_means_no_scores(self):
        assert score_relevance([_product()], None) == [(_product(), None)]

    @pytest.mark.parametrize(
        "name, description, code, expected",
        [
            ("Steel bar", None, "X", 0.8),
            ("Bar of steel", None, "X", 0.5),
            ("Bar", "steel", "X", 0.1),
            ("Bar", None, "STEEL-1", 0.1),
            ("Steel", "steel", "STEEL-1", 1.0),
            ("Bar", None, "X", 0.0),
        ],
    )
    def test_scores(self, name, description, code, expected):
        product = DomainProduct(id="p", code=code, name=name, unit="kg", description=description)

        assert score_relevance([product], "STEEL")[0][1] == pytest.approx(expected)


class TestProductServiceSearch:
    def test_scores_results_against_the_text(self):
        repo = MagicMock(spec=ProductRepository)
        repo.search.return_value = ProductPage(items=[_product(name="Steel")], total=9)
        criteria = ProductSearchCriteria(query="steel")

        result = ProductService(repo).search_products(criteria)

        repo.search.assert_called_once_with(criteria)
        assert result.total == 9
        assert result.items[0].relevance_score == pytest.approx(0.8)


class TestCategoryService:
    CATEGORIES = [
        Category(id="root", code="R", name="Root", level=0),
        Category(id="mid", code="M", name="Mid", level=1, parent_id="root"),
        Category(id="leaf", code="L", name="Leaf", level=2, parent_id="mid"),
    ]

    @pytest.fixture
    def repo(self):
        repo = MagicMock(spec=CategoryRepository)
        repo.list_all.return_value = self.CATEGORIES
        repo.count_products.side_effect = {"root": 1, "mid": 2, "leaf": 4}.get
        return repo

    def test_builds_the_whole_tree(self, repo):
        tree = CategoryService(repo).get_tree(None, max_depth=10)

        assert tree.total_categories == 3
        assert tree.max_depth == 2
        assert tree.categories[0].children[0].children[0].id == "leaf"

    def test_counts_nothing_unless_asked(self, repo):
        tree = CategoryService(repo).get_tree(None, max_depth=10)

        assert tree.categories[0].product_count is None
        repo.count_products.assert_not_called()

    def test_counts_include_descendants(self, repo):
        tree = CategoryService(repo).get_tree(None, max_depth=10, include_product_count=True)

        assert tree.categories[0].product_count == 7
        assert tree.categories[0].children[0].product_count == 6

    def test_depth_limit(self, repo):
        tree = CategoryService(repo).get_tree(None, max_depth=2)

        assert tree.total_categories == 2
        assert tree.categories[0].children[0].children == []

    def test_subtree(self, repo):
        tree = CategoryService(repo).get_tree("root", max_depth=10)

        assert [node.id for node in tree.categories] == ["mid"]

    def test_passes_the_industry_filter(self, repo):
        CategoryService(repo).get_tree(None, max_depth=10, industry="apparel")

        repo.list_all.assert_called_once_with(industry="apparel")

    def test_empty_tree(self, repo):
        repo.list_all.return_value = []

        tree = CategoryService(repo).get_tree(None, max_depth=10)

        assert (tree.categories, tree.total_categories, tree.max_depth) == ([], 0, 0)

    def test_get_category_missing(self, repo):
        repo.get_by_id.return_value = None

        with pytest.raises(CategoryNotFoundError):
            CategoryService(repo).get_category("none")


class TestRoutesUseTheServices:
    @pytest.fixture
    def products(self, client):
        from backend.main import app

        fake = MagicMock(spec=ProductService)
        app.dependency_overrides[get_product_service] = lambda: fake
        return fake

    @pytest.fixture
    def categories(self, client):
        from backend.main import app

        fake = MagicMock(spec=CategoryService)
        app.dependency_overrides[get_category_service] = lambda: fake
        return fake

    def test_list(self, client, products):
        products.list_products.return_value = ProductPage(
            items=[_product("only-in-fake", created_at=CREATED, is_finished_product=True)], total=42
        )

        body = client.get(f"{PRODUCTS}?limit=7&offset=1&is_finished=true").json()

        assert body["total"] == 42
        assert body["items"][0]["id"] == "only-in-fake"
        assert body["items"][0]["created_at"] == CREATED.isoformat()
        products.list_products.assert_called_once_with(limit=7, offset=1, is_finished_product=True)

    def test_detail(self, client, products):
        products.get_product_with_bom.return_value = ProductWithBOM(
            product=_product("only-in-fake"),
            bom_items=[
                BOMItem(component_id="c", quantity=1.5, unit=None, id="b", component_name="Part", notes="n")
            ],
        )

        body = client.get(f"{PRODUCTS}/only-in-fake").json()

        assert body["id"] == "only-in-fake"
        assert body["bill_of_materials"][0]["child_product_name"] == "Part"
        assert body["bill_of_materials"][0]["unit"] is None

    def test_detail_missing_keeps_its_message(self, client, products):
        products.get_product_with_bom.side_effect = ProductNotFoundError(product_id="x")

        response = client.get(f"{PRODUCTS}/x")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"
        assert response.json()["error"]["message"] == "Product not found"

    def test_search(self, client, products, categories):
        products.search_products.return_value = ProductSearchResult(
            items=[
                ScoredProduct(
                    product=_product(
                        "only-in-fake",
                        category_info=CategorySummary(id="c", code="C", name="Cat", industry_sector="energy"),
                    ),
                    relevance_score=0.8,
                )
            ],
            total=3,
        )

        body = client.get(f"{SEARCH}?q=wi&limit=1").json()

        assert body["items"][0]["id"] == "only-in-fake"
        assert body["items"][0]["relevance_score"] == 0.8
        assert body["items"][0]["category"]["code"] == "C"
        assert body["has_more"] is True
        assert products.search_products.call_args.args[0].query == "wi"

    def test_search_falls_back_to_the_category_text(self, client, products, categories):
        products.search_products.return_value = ProductSearchResult(
            items=[ScoredProduct(product=_product(category="raw_materials"), relevance_score=None)],
            total=1,
        )

        category = client.get(SEARCH).json()["items"][0]["category"]

        assert category == {
            "id": "", "code": "raw_materials", "name": "Raw Materials", "industry_sector": "raw_materials",
        }

    def test_search_unknown_category_is_422(self, client, products, categories):
        categories.get_category.side_effect = CategoryNotFoundError(category_id="x")

        response = client.get(f"{SEARCH}?category_id=x")

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "INVALID_CATEGORY"
        products.search_products.assert_not_called()

    def test_categories(self, client, categories):
        categories.get_tree.return_value = CategoryTree(
            categories=[
                CategoryNode(
                    id="only-in-fake", code="C", name="Cat", level=0, product_count=5,
                    children=[CategoryNode(id="kid", code="K", name="Kid", level=1)],
                )
            ],
            total_categories=2,
            max_depth=1,
        )

        body = client.get(f"{CATEGORIES}?depth=3&industry=electronics&include_product_count=true").json()

        assert body["categories"][0]["id"] == "only-in-fake"
        assert body["categories"][0]["children"][0]["id"] == "kid"
        assert (body["total_categories"], body["max_depth"]) == (2, 1)
        categories.get_tree.assert_called_once_with(
            root_parent_id=None, max_depth=3, include_product_count=True, industry="electronics"
        )

    def test_categories_unknown_parent_is_404(self, client, categories):
        categories.get_category.side_effect = CategoryNotFoundError(category_id="x")

        response = client.get(f"{CATEGORIES}?parent_id=x")

        assert response.status_code == 404
        assert response.json()["error"]["message"] == "Category not found"
