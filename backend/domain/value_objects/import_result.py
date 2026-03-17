from dataclasses import dataclass, field


@dataclass(frozen=True)
class ImportResult:
    created: int
    updated: int
    errors: list[str] = field(default_factory=list)
