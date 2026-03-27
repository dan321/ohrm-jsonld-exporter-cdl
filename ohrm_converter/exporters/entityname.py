"""EntityName exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import extract_entities_from_row, map_properties
from ohrm_converter.models import EntityName

PROPERTY_MAPPINGS = [
    ("enstartdate", "startDate"), ("ensdatemod", "dateModifier"),
    ("enstart", "startDateISOString"), ("enenddate", "endDate"),
    ("enedatemod", "endDateModifier"), ("enend", "endDateISOString"),
    ("endatequal", "dateQualifier"), ("ennote", "processingNotes"),
]
EXTRACT_ENTITIES = [("Place", "enplace", "place")]

def export_entitynames(rows: list[EntityName]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        if not row.eid:
            continue
        entity: dict = {
            "@id": f"#{quote(row.eid)}_alsoKnownAs",
            "@type": [row.enalternatetype] if row.enalternatetype else [],
            "name": row.enalternate,
            "alsoKnownAs": {"@id": f"#{quote(row.eid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
