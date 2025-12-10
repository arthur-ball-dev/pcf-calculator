"""
ProductCategory model - Hierarchical product categorization

TASK-DB-P5-002: Extended Database Schema

Represents a hierarchical product category structure with support
for self-referential parent/children relationships.

Attributes:
    id: UUID primary key
    code: Unique category code
    name: Category name
    parent_id: FK to parent category (self-referential)
    level: Level in hierarchy (0 = root)
    industry_sector: Industry sector classification
    search_vector: TSVECTOR for full-text search (PostgreSQL)
    created_at: Creation timestamp

Relationships:
    parent: Parent ProductCategory
    children: Child ProductCategory objects
    products: Products in this category
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.models.base import Base, generate_uuid


class ProductCategory(Base):
    """
    ProductCategory model - Hierarchical product categorization.

    Supports a 5+ level hierarchy with self-referential relationships.
    Includes full-text search capability via search_vector (PostgreSQL).
    """
    __tablename__ = "product_categories"

    # Primary key - UUID hex string
    id = Column(
        String(32),
        primary_key=True,
        default=generate_uuid
    )

    # Unique category code (e.g., "ELEC", "COMP", "LAPT")
    code = Column(String(20), nullable=False, unique=True)

    # Category name
    name = Column(String(255), nullable=False)

    # Self-referential FK to parent category
    parent_id = Column(
        String(32),
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True
    )

    # Level in hierarchy (0 = root)
    level = Column(Integer, nullable=False, default=0)

    # Industry sector classification
    industry_sector = Column(String(100), nullable=True)

    # Full-text search vector (nullable Text for SQLite compatibility)
    # In PostgreSQL, this would be TSVECTOR with a GIN index
    search_vector = Column(Text, nullable=True)

    # Audit timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Self-referential relationship - parent
    parent = relationship(
        "ProductCategory",
        remote_side=[id],
        back_populates="children",
        foreign_keys=[parent_id]
    )

    # Self-referential relationship - children
    children = relationship(
        "ProductCategory",
        back_populates="parent",
        foreign_keys=[parent_id]
    )

    # Relationship to products in this category
    products = relationship(
        "Product",
        back_populates="product_category",
        foreign_keys="[Product.category_id]"
    )

    # Table indexes
    __table_args__ = (
        Index('idx_category_parent', 'parent_id'),
        Index('idx_category_industry', 'industry_sector'),
        Index('idx_category_level', 'level'),
        # GIN index for search_vector would be added in PostgreSQL migration
    )

    def __repr__(self) -> str:
        return f"<ProductCategory(code='{self.code}', name='{self.name}', level={self.level})>"
