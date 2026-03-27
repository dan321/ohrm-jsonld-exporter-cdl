"""RelatedEntity exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import RelatedEntity

PROPERTY_MAPPINGS = {
    "restartdate": "startDate",
    "resdatemod": "startDateModifier",
    "restart": "startDateISOString",
    "reenddate": "endDate",
    "reedatemod": "endDateModifer",
    "reend": "endDateISOString",
    "redatequal": "dateQualifier",
    "renote": "processingNotes",
    "rerating": "relationshipStrength",
    "reappenddate": "recordAppendDate",
    "relastmodd": "recordLastModified",
    "reorder": "reorder",
}
EXTRACT_ENTITIES = [Extraction(entity_type="Person", field="reprepared", prop="preparedBy")]

def export_relatedentities(rows: list[RelatedEntity]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        if not row.eid or not row.reid:
            continue
        rel_type = row.rerelationship.replace(" ", "_") if row.rerelationship else ""
        entity: dict = {
            "@id": f"#{quote(row.eid)}-{quote(row.reid)}",
            "@type": ["Relationship", rel_type] if rel_type else ["Relationship"],
            "identifier": f"{row.eid}-{row.reid}",
            "name": row.rerelationship,
            "description": row.redescription,
            "source": {"@id": f"#{quote(row.reid)}"},
            "target": {"@id": f"#{quote(row.eid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
