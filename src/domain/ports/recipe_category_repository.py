from src.domain.ports.category_repository import CategoryRepository


class RecipeCategoryRepository(CategoryRepository):
    """Marker subclass for recipe categories — enables type-safe DI."""
