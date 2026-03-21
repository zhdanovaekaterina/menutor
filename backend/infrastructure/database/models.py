"""SQLAlchemy ORM models for the infrastructure layer.

These are infrastructure-only: domain entities stay pure.
Repositories map between these rows and domain entities.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    nickname = Column(String, nullable=False, default="", server_default="")
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    refresh_tokens = relationship(
        "RefreshTokenRow",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshTokenRow(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False, server_default="0")

    user = relationship("UserRow", back_populates="refresh_tokens")


class UnitRow(Base):
    __tablename__ = "units"

    name = Column(String, primary_key=True)
    unit_group = Column(String, nullable=False)


class RecipeCategoryRow(Base):
    __tablename__ = "recipe_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    active = Column(Integer, nullable=False, default=1, server_default="1")


class ProductCategoryRow(Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    active = Column(Integer, nullable=False, default=1, server_default="1")


class ProductRow(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False)
    brand = Column(String, nullable=False, default="", server_default="")
    supplier = Column(String, nullable=False, default="", server_default="")
    recipe_unit = Column(String, ForeignKey("units.name"), nullable=False)
    purchase_unit = Column(String, ForeignKey("units.name"), nullable=False)
    price_per_purchase_unit = Column(Float, nullable=False, default=0.0, server_default="0")
    conversion_factor = Column(Float, nullable=False, default=1.0, server_default="1.0")


class RecipeRow(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("recipe_categories.id"), nullable=False)
    dietary_tags = Column(String, nullable=False, default="[]", server_default="[]")
    servings = Column(Integer, nullable=False, default=1, server_default="1")
    weight = Column(Integer, nullable=False, default=0, server_default="0")
    total_pieces = Column(Integer, nullable=True)
    pieces_per_portion = Column(Integer, nullable=True)

    ingredients = relationship(
        "RecipeIngredientRow",
        back_populates="recipe",
        cascade="all, delete-orphan",
        foreign_keys="RecipeIngredientRow.recipe_id",
    )
    steps = relationship(
        "CookingStepRow",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )


class RecipeIngredientRow(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        CheckConstraint(
            "(product_id IS NOT NULL AND sub_recipe_id IS NULL) OR "
            "(product_id IS NULL AND sub_recipe_id IS NOT NULL)",
            name="check_ingredient_xor",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(
        Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    sub_recipe_id = Column(
        Integer, ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )
    amount = Column(Float, nullable=False)
    unit = Column(String, ForeignKey("units.name"), nullable=False)
    ingredient_order = Column(
        Integer, nullable=False, default=0, server_default="0"
    )

    recipe = relationship(
        "RecipeRow", back_populates="ingredients", foreign_keys=[recipe_id]
    )


class CookingStepRow(Base):
    __tablename__ = "cooking_steps"

    recipe_id = Column(
        Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True
    )
    step_order = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)

    recipe = relationship("RecipeRow", back_populates="steps")


class FamilyMemberRow(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    portion_multiplier = Column(Float, nullable=False, default=1.0, server_default="1.0")
    dietary_restrictions = Column(String, nullable=False, default="", server_default="")
    comment = Column(String, nullable=False, default="", server_default="")


class MenuRow(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)

    slots = relationship(
        "MenuSlotRow",
        back_populates="menu",
        cascade="all, delete-orphan",
    )


class MenuSlotRow(Base):
    __tablename__ = "menu_slots"
    __table_args__ = (
        CheckConstraint(
            "(recipe_id IS NOT NULL AND product_id IS NULL) OR "
            "(recipe_id IS NULL AND product_id IS NOT NULL)",
            name="check_slot_xor",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    menu_id = Column(
        Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False
    )
    day = Column(Integer, nullable=False)
    meal_type = Column(String, nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    servings_override = Column(Float, nullable=True)
    pieces_override = Column(Integer, nullable=True)
    slot_position = Column(Integer, nullable=False, default=0, server_default="0")

    menu = relationship("MenuRow", back_populates="slots")


class ShoppingListRow(Base):
    __tablename__ = "shopping_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, nullable=False)
    source_menu_id = Column(
        Integer, ForeignKey("menus.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    items = relationship(
        "ShoppingListItemRow",
        back_populates="shopping_list",
        cascade="all, delete-orphan",
    )


class ShoppingListItemRow(Base):
    __tablename__ = "shopping_list_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shopping_list_id = Column(
        Integer, ForeignKey("shopping_lists.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    quantity_amount = Column(Float, nullable=False)
    quantity_unit = Column(String, nullable=False)
    buy_quantity_amount = Column(Float, nullable=False)
    buy_quantity_unit = Column(String, nullable=False)
    buy_quantity_overridden = Column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    recipe_quantity_amount = Column(Float, nullable=True)
    recipe_quantity_unit = Column(String, nullable=True)
    cost_amount = Column(Float, nullable=False)
    cost_currency = Column(
        String, nullable=False, default="RUB", server_default="RUB"
    )
    purchased = Column(Boolean, nullable=False, default=False, server_default="0")
    item_order = Column(Integer, nullable=False, default=0, server_default="0")

    shopping_list = relationship("ShoppingListRow", back_populates="items")
