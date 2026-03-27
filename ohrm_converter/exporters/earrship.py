"""Entity-ArchivalResource relationship exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import EARRship

PROPERTY_MAPPINGS = {
    "earstartdate": "startDate",
    "earsdatemod": "startDateModifier",
    "earstart": "startDateISOString",
    "earenddate": "endDate",
    "earedatemod": "endDateModifer",
    "earend": "endDateISOString",
    "earcitation": "citation",
    "earappenddate": "recordAppendDate",
    "earlastmodd": "recordLastModified",
    "earereference": "earereference",
}
EXTRACT_ENTITIES = [
    Extraction(entity_type="Person", field="earprepared", prop="preparedBy"),
    Extraction(entity_type="Place", field="earplace", prop="place"),
]

def export_earrships(rows: list[EARRship]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        if not row.arcid or not row.eid:
            continue
        rel_type = row.relationship.replace(" ", "_") if row.relationship else ""
        entity: dict = {
            "@id": f"#{quote(row.arcid)}-{quote(row.eid)}",
            "@type": ["Relationship", rel_type] if rel_type else ["Relationship"],
            "identifier": f"{row.arcid}-{row.eid}",
            "description": row.description,
            "source": {"@id": f"#{quote(row.arcid)}"},
            "target": {"@id": f"#{quote(row.eid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
