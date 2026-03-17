from backend.domain.ports.entity_exporter import EntityExporter
from backend.domain.ports.entity_importer import EntityImporter


class ExportRegistry:
    def __init__(self) -> None:
        self._exporters: dict[tuple[str, str], EntityExporter] = {}

    def register(self, entity_type: str, format: str, exporter: EntityExporter) -> None:
        self._exporters[(entity_type, format)] = exporter

    def get(self, entity_type: str, format: str) -> EntityExporter | None:
        return self._exporters.get((entity_type, format))

    def formats_for(self, entity_type: str) -> list[str]:
        return [fmt for (et, fmt) in self._exporters if et == entity_type]


class ImportRegistry:
    def __init__(self) -> None:
        self._importers: dict[tuple[str, str], EntityImporter] = {}

    def register(self, entity_type: str, format: str, importer: EntityImporter) -> None:
        self._importers[(entity_type, format)] = importer

    def get(self, entity_type: str, format: str) -> EntityImporter | None:
        return self._importers.get((entity_type, format))

    def formats_for(self, entity_type: str) -> list[str]:
        return [fmt for (et, fmt) in self._importers if et == entity_type]
