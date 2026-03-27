"""Entity-DObject relationship exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import EDORship

PROPERTY_MAPPINGS = {
    "edostartdate": "startDate",
    "edosdatemod": "startDateModifier",
    "edostart": "startDateISOString",
    "edoenddate": "endDate",
    "edoedatemod": "endDateModifier",
    "edoend": "endDateISOString",
    "edocitation": "citation",
    "edoappenddate": "recordAppendDate",
    "edolastmodd": "recordLastModified",
    "edoereference": "edoereference",
    "edogallery": "edogallery",
}
EXTRACT_ENTITIES = [
    Extraction(entity_type="Person", field="edoprepared", prop="preparedBy"),
    Extraction(entity_type="Place", field="edoplace", prop="place"),
]

def export_edorships(rows: list[EDORship]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        if not row.doid or not row.eid:
            continue
        rel_type = row.relationship.replace(" ", "_") if row.relationship else ""
        entity: dict = {
            "@id": f"#{quote(row.doid)}-{quote(row.eid)}",
            "@type": ["Relationship", rel_type] if rel_type else ["Relationship"],
            "identifier": f"{row.doid}-{row.eid}",
            "description": row.description,
            "source": {"@id": f"#{quote(row.doid)}"},
            "target": {"@id": f"#{quote(row.eid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
