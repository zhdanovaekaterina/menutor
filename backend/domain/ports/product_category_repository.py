from backend.domain.ports.category_repository import CategoryRepository


class ProductCategoryRepository(CategoryRepository):
    """Marker subclass for product categories — enables type-safe DI."""
