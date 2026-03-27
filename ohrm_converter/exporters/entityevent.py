"""EntityEvent exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import Entity, EntityEvent

PROPERTY_MAPPINGS = {
    "eestartdate": "startDate",
    "eesdatemod": "dateModifier",
    "eestart": "startDateISOString",
    "eeenddate": "endDate",
    "eeedatemod": "endDateModifier",
    "eeend": "endDateISOString",
    "eedatequal": "dateQualifier",
    "eenote": "processingNotes",
    "eerating": "eerating",
    "eeappenddate": "recordAppendDate",
    "eelastmodd": "recordLastModified",
    "otdid": "otdid",
}
EXTRACT_ENTITIES = [
    Extraction(entity_type="Place", field="eelocation", prop="location"),
    Extraction(entity_type="Person", field="eeprepared", prop="preparedBy"),
]

def export_entityevents(rows: list[EntityEvent], entities: list[Entity]) -> list[dict]:
    results: list[dict] = []
    entity_types: dict[str, list[str]] = {}
    for e in entities:
        if e.eid and e.etype:
            entity_types[e.eid] = [v.strip().replace(" ", "_") for v in e.etype.split("-")]
    for row in rows:
        if not row.eid:
            continue
        base_type = entity_types.get(row.eid, [])
        event_type = list(base_type)
        if row.eetype:
            event_type.append(row.eetype)
        entity: dict = {
            "@id": f"#{quote(row.eid)}_event", "@type": event_type,
            "description": row.eedescription, "entity": {"@id": f"#{quote(row.eid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
