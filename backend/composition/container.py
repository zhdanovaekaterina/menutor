"""ApplicationContainer — slim orchestrator calling domain sub-registries."""

from backend.composition._auth import _wire_auth
from backend.composition._categories import _wire_categories
from backend.composition._family import _wire_family
from backend.composition._import_export import _wire_import_export
from backend.composition._infrastructure import _create_infrastructure
from backend.composition._menus import _wire_menus
from backend.composition._preferences import _wire_preferences
from backend.composition._products import _wire_products
from backend.composition._recipes import _wire_recipes
from backend.composition._shopping import _wire_shopping


class ApplicationContainer:
    """Dependency graph. Created once at startup."""

    def __init__(self, db_url: str | None = None) -> None:
        infra = _create_infrastructure(db_url)

        for name, obj in _wire_auth(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_recipes(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_products(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_menus(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_categories(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_family(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_shopping(infra).items():
            setattr(self, name, obj)
        for name, obj in _wire_preferences(infra).items():
            setattr(self, name, obj)

        # import/export wiring needs generate_shopping_list already set
        for name, obj in _wire_import_export(infra, self.generate_shopping_list).items():  # type: ignore[attr-defined]
            setattr(self, name, obj)

        self._engine = infra.engine
        self._session = infra.session
