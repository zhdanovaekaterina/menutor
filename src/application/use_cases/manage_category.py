from src.domain.ports.product_category_repository import ProductCategoryRepository
from src.domain.ports.recipe_category_repository import RecipeCategoryRepository
from src.domain.value_objects.category import Category


class ListAllProductCategories:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Category]:
        return self._repo.find_all()


class CreateProductCategory:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    def execute(self, name: str) -> int:
        return self._repo.save(name)


class EditProductCategory:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int, name: str) -> int:
        return self._repo.save(name, category_id)


class DeleteProductCategory:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int) -> None:
        self._repo.delete(category_id)


class CheckProductCategoryUsed:
    def __init__(self, repo: ProductCategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int) -> bool:
        return self._repo.has_products(category_id)


class ListAllRecipeCategories:
    def __init__(self, repo: RecipeCategoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Category]:
        return self._repo.find_all()


class CreateRecipeCategory:
    def __init__(self, repo: RecipeCategoryRepository) -> None:
        self._repo = repo

    def execute(self, name: str) -> int:
        return self._repo.save(name)


class EditRecipeCategory:
    def __init__(self, repo: RecipeCategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int, name: str) -> int:
        return self._repo.save(name, category_id)


class DeleteRecipeCategory:
    def __init__(self, repo: RecipeCategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int) -> None:
        self._repo.delete(category_id)


class CheckRecipeCategoryUsed:
    def __init__(self, repo: RecipeCategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int) -> bool:
        return self._repo.has_recipes(category_id)
