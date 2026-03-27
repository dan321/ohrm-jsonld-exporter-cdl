"""Repository exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import map_properties
from ohrm_converter.models import Repository

PROPERTY_MAPPINGS = {
    "wurl": "url",
}


def export_repositories(rows: list[Repository]) -> list[dict]:
    """Export Repository rows to JSON-LD entity dicts."""
    results: list[dict] = []
    for row in rows:
        entity: dict = {
            "@id": f"#{quote(row.repid)}",
            "@type": "Repository",
            "identifier": row.repid,
            "name": row.rep,
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        results.append(entity)
    return results
