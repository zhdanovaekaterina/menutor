"""Tests for RecipeIngredientSchema XOR validation and new schema types."""

import pytest
from pydantic import ValidationError

from backend.api.schemas.recipe import (
    FlattenedProductResponse,
    RecipeIngredientSchema,
    ValidateSubRecipeRequest,
    ValidateSubRecipeResponse,
)


class TestRecipeIngredientSchemaValidation:
    def test_ingredient_schema_product_valid(self) -> None:
        schema = RecipeIngredientSchema(
            product_id=1,
            sub_recipe_id=None,
            quantity_amount=200.0,
            quantity_unit="g",
        )
        assert schema.product_id == 1
        assert schema.sub_recipe_id is None

    def test_ingredient_schema_sub_recipe_valid(self) -> None:
        schema = RecipeIngredientSchema(
            product_id=None,
            sub_recipe_id=5,
            quantity_amount=1.0,
            quantity_unit="serv",
        )
        assert schema.sub_recipe_id == 5
        assert schema.product_id is None

    def test_ingredient_schema_both_set_invalid(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            RecipeIngredientSchema(
                product_id=1,
                sub_recipe_id=5,
                quantity_amount=100.0,
                quantity_unit="g",
            )
        assert "ИЛИ" in str(exc_info.value)

    def test_ingredient_schema_neither_set_invalid(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            RecipeIngredientSchema(
                product_id=None,
                sub_recipe_id=None,
                quantity_amount=100.0,
                quantity_unit="g",
            )
        assert "ИЛИ" in str(exc_info.value)

    def test_ingredient_schema_backward_compat_no_sub_recipe_field(self) -> None:
        """Old requests without sub_recipe_id key default to None — XOR passes."""
        data = {"product_id": 3, "quantity_amount": 150.0, "quantity_unit": "ml"}
        schema = RecipeIngredientSchema.model_validate(data)
        assert schema.product_id == 3
        assert schema.sub_recipe_id is None

    def test_ingredient_schema_sub_recipe_name_is_optional(self) -> None:
        schema = RecipeIngredientSchema(
            sub_recipe_id=7,
            sub_recipe_name="Соус",
            quantity_amount=1.0,
            quantity_unit="serv",
        )
        assert schema.sub_recipe_name == "Соус"


class TestValidateSubRecipeSchemas:
    def test_validate_request_with_parent(self) -> None:
        req = ValidateSubRecipeRequest(parent_recipe_id=1, sub_recipe_id=2)
        assert req.parent_recipe_id == 1
        assert req.sub_recipe_id == 2

    def test_validate_request_without_parent(self) -> None:
        req = ValidateSubRecipeRequest(sub_recipe_id=2)
        assert req.parent_recipe_id is None

    def test_validate_response_valid(self) -> None:
        resp = ValidateSubRecipeResponse(valid=True)
        assert resp.valid is True
        assert resp.error is None

    def test_validate_response_invalid_with_error(self) -> None:
        resp = ValidateSubRecipeResponse(valid=False, error="Циклическая зависимость")
        assert resp.valid is False
        assert resp.error == "Циклическая зависимость"


class TestFlattenedProductResponse:
    def test_flattened_product_response(self) -> None:
        resp = FlattenedProductResponse(
            product_id=1,
            product_name="Мука",
            quantity_amount=200.0,
            quantity_unit="g",
        )
        assert resp.product_id == 1
        assert resp.product_name == "Мука"
        assert resp.quantity_amount == 200.0
        assert resp.quantity_unit == "g"
