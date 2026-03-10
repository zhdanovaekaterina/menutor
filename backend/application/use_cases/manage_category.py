from backend.domain.ports.category_repository import CategoryRepository
from backend.domain.value_objects.category import Category


class ListAllCategories:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Category]:
        return self._repo.find_all()


class CreateCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self, name: str) -> int:
        return self._repo.save(name)


class EditCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int, name: str) -> int:
        return self._repo.save(name, category_id)


class DeleteCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int) -> None:
        self._repo.delete(category_id)


class HardDeleteCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int) -> None:
        self._repo.hard_delete(category_id)


class ActivateCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int) -> None:
        self._repo.activate(category_id)


class CheckCategoryUsed:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int) -> bool:
        return self._repo.is_used(category_id)


# Backwards-compatible aliases
ListAllProductCategories = ListAllCategories
CreateProductCategory = CreateCategory
EditProductCategory = EditCategory
DeleteProductCategory = DeleteCategory
CheckProductCategoryUsed = CheckCategoryUsed

ListAllRecipeCategories = ListAllCategories
CreateRecipeCategory = CreateCategory
EditRecipeCategory = EditCategory
DeleteRecipeCategory = DeleteCategory
CheckRecipeCategoryUsed = CheckCategoryUsed
