"""
Category Service - Domain Business Logic

Builds the category tree and its product counts.
Depends only on repository interfaces, not implementations.

No SQLAlchemy or infrastructure imports allowed.
"""

from typing import List, Optional

from backend.domain.entities.category import Category, CategoryNode, CategoryTree
from backend.domain.entities.errors import CategoryNotFoundError
from backend.domain.repositories.interfaces import CategoryRepository


def _find_max_depth(nodes: List[CategoryNode], current: int = 0) -> int:
    """Find the maximum depth of a tree."""
    if not nodes:
        return current
    max_child_depth = current
    for node in nodes:
        if node.children:
            max_child_depth = max(max_child_depth, _find_max_depth(node.children, current + 1))
    return max_child_depth


def _count_nodes(nodes: List[CategoryNode]) -> int:
    """Count every node in a tree."""
    return len(nodes) + sum(_count_nodes(node.children) for node in nodes if node.children)


class CategoryService:
    """Domain service for product categories."""

    def __init__(self, category_repo: CategoryRepository):
        """
        Initialize the service with a repository.

        Args:
            category_repo: Repository implementing CategoryRepository interface.
        """
        self._category_repo = category_repo

    def get_category(self, category_id: str) -> Category:
        """
        Get a category by ID.

        Raises:
            CategoryNotFoundError: If the category does not exist.
        """
        category = self._category_repo.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id=category_id)
        return category

    def get_tree(
        self,
        root_parent_id: Optional[str],
        max_depth: int,
        include_product_count: bool = False,
        industry: Optional[str] = None,
    ) -> CategoryTree:
        """
        Build the category tree.

        Args:
            root_parent_id: Return the subtree under this category; None for the whole tree.
            max_depth: Maximum depth of the tree.
            include_product_count: Count each category's products, descendants included.
            industry: Only categories in this industry sector.

        Returns:
            The tree with its total category count and maximum depth.
        """
        categories = self._category_repo.list_all(industry=industry)
        tree = self._build_nodes(categories, root_parent_id, 0, max_depth, include_product_count)
        return CategoryTree(
            categories=tree,
            total_categories=_count_nodes(tree),
            max_depth=_find_max_depth(tree),
        )

    def _build_nodes(
        self,
        categories: List[Category],
        parent_id: Optional[str],
        current_depth: int,
        max_depth: int,
        include_product_count: bool,
    ) -> List[CategoryNode]:
        nodes = []
        for category in (c for c in categories if c.parent_id == parent_id):
            product_count = None
            if include_product_count:
                product_count = self._count_products(category.id, categories)

            children: List[CategoryNode] = []
            if current_depth < max_depth - 1:
                children = self._build_nodes(
                    categories, category.id, current_depth + 1, max_depth, include_product_count
                )

            nodes.append(
                CategoryNode(
                    id=category.id,
                    code=category.code,
                    name=category.name,
                    level=category.level,
                    industry_sector=category.industry_sector,
                    product_count=product_count,
                    children=children,
                )
            )
        return nodes

    def _count_products(self, category_id: str, categories: List[Category]) -> int:
        """Count products in a category and all its descendants."""
        count = self._category_repo.count_products(category_id)
        for child in (c for c in categories if c.parent_id == category_id):
            count += self._count_products(child.id, categories)
        return count
