"""
Product Service - Domain Business Logic

TASK-BE-P7-019: Domain Layer Separation

Contains business logic for product-related operations.
Depends only on repository interfaces, not implementations.

No SQLAlchemy or infrastructure imports allowed.
"""

from typing import Any, List, Optional, Sequence, Tuple, TypeVar

from backend.domain.entities.product import (
    Product,
    ProductPage,
    ProductSearchCriteria,
    ProductSearchResult,
    ProductWithBOM,
    ScoredProduct,
)
from backend.domain.entities.errors import ProductNotFoundError
from backend.domain.repositories.interfaces import ProductRepository


T = TypeVar("T", bound=Any)


def score_relevance(products: Sequence[T], query: Optional[str]) -> List[Tuple[T, Optional[float]]]:
    """
    Score search results against the search text, from 0 to 1.

    A name match counts most, more when the name starts with the text; description
    and code matches add a little. Without search text every score is None.
    """
    if not query:
        return [(p, None) for p in products]

    query_lower = query.lower()
    scored: List[Tuple[T, Optional[float]]] = []

    for p in products:
        score = 0.0
        if p.name and query_lower in p.name.lower():
            score += 0.5
            if p.name.lower().startswith(query_lower):
                score += 0.3
        if p.description and query_lower in p.description.lower():
            score += 0.1
        if p.code and query_lower in p.code.lower():
            score += 0.1
        scored.append((p, min(score, 1.0)))

    return scored


class ProductService:
    """
    Domain service for product operations.

    Encapsulates business logic and coordinates with repository.
    Uses dependency injection for the repository.
    """

    def __init__(self, product_repo: ProductRepository):
        """
        Initialize the service with a repository.

        Args:
            product_repo: Repository implementing ProductRepository interface.
        """
        self._product_repo = product_repo

    def get_product(self, product_id: str) -> Product:
        """
        Get a product by ID.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            Product domain entity.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        product = self._product_repo.get_by_id(product_id)
        if product is None:
            raise ProductNotFoundError(product_id=product_id)
        return product

    def get_product_with_bom(self, product_id: str) -> ProductWithBOM:
        """
        Get a product with its Bill of Materials.

        Args:
            product_id: The unique identifier of the product.

        Returns:
            ProductWithBOM containing product and BOM items.

        Raises:
            ProductNotFoundError: If the product does not exist.
        """
        result = self._product_repo.get_with_bom(product_id)
        if result is None:
            raise ProductNotFoundError(product_id=product_id)
        return result

    def list_products(
        self,
        limit: int = 100,
        offset: int = 0,
        is_finished_product: Optional[bool] = None,
    ) -> ProductPage:
        """
        List products with pagination.

        Args:
            limit: Maximum number of products to return.
            offset: Number of products to skip.
            is_finished_product: Only finished products, or only components.

        Returns:
            One page of products and the total matching count.
        """
        return self._product_repo.list_all(
            limit=limit, offset=offset, is_finished_product=is_finished_product
        )

    def search_products(self, criteria: ProductSearchCriteria) -> ProductSearchResult:
        """
        Search products and score the results against the search text.

        Args:
            criteria: Validated filters and pagination.

        Returns:
            One page of scored results and the total matching count.
        """
        page = self._product_repo.search(criteria)
        return ProductSearchResult(
            items=[
                ScoredProduct(product=product, relevance_score=score)
                for product, score in score_relevance(page.items, criteria.query)
            ],
            total=page.total,
        )
