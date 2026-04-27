from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineContext:
    sf: Any | None = None
    records: dict[str, list[dict]] = field(default_factory=dict)
    id_maps: dict[str, dict[str, str]] = field(default_factory=dict)

    def set_records(self, key: str, records: list[dict]) -> None:
        self.records[key] = records

    def get_records(self, key: str) -> list[dict]:
        return self.records.get(key, [])

    def set_id_map(self, key: str, id_map: dict[str, str]) -> None:
        self.id_maps[key] = id_map

    def get_id_map(self, key: str) -> dict[str, str]:
        return self.id_maps.get(key, {})