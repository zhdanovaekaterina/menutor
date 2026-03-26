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

    def execute(self, name: str, color: str | None = None) -> int:
        return self._repo.save(name, color=color)


class EditCategory:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self, category_id: int, name: str, color: str | None = None) -> int:
        return self._repo.save(name, category_id, color=color)


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


class MoveCategoryAndDelete:
    def __init__(self, repo: CategoryRepository) -> None:
        self._repo = repo

    def execute(self, from_id: int, to_id: int) -> None:
        self._repo.move_and_delete(from_id, to_id)


class CategoryBundle:
    """Groups all category use cases for one category type."""

    def __init__(self, repo: CategoryRepository) -> None:
        self.list_all = ListAllCategories(repo)
        self.create = CreateCategory(repo)
        self.edit = EditCategory(repo)
        self.delete = DeleteCategory(repo)
        self.hard_delete = HardDeleteCategory(repo)
        self.activate = ActivateCategory(repo)
        self.check_used = CheckCategoryUsed(repo)
        self.move_and_delete = MoveCategoryAndDelete(repo)
