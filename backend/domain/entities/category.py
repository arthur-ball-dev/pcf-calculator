"""
Category Domain Entities

Product categories and the hierarchical tree built from them.
No SQLAlchemy or infrastructure dependencies allowed.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Category:
    """A product category, as stored."""

    id: str
    code: str
    name: str
    level: int
    parent_id: Optional[str] = None
    industry_sector: Optional[str] = None


@dataclass(frozen=True)
class CategoryNode:
    """A category in a tree, with its children and optional product count."""

    id: str
    code: str
    name: str
    level: int
    industry_sector: Optional[str] = None
    product_count: Optional[int] = None
    children: List["CategoryNode"] = field(default_factory=list)


@dataclass(frozen=True)
class CategoryTree:
    """A category tree with its totals."""

    categories: List[CategoryNode]
    total_categories: int
    max_depth: int
