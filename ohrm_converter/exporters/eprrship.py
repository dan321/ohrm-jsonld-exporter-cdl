"""Entity-PubResource relationship exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import EPRRship

PROPERTY_MAPPINGS = {
    "eprstartdate": "startDate",
    "eprsdatemod": "startDateModifier",
    "eprstart": "startDateISOString",
    "eprenddate": "endDate",
    "epredatemod": "endDateModifier",
    "eprend": "endDateISOString",
    "eprcitation": "citation",
    "eprappenddate": "recordAppendDate",
    "eprlastmodd": "recordLastModified",
    "eprereference": "eprereference",
}
EXTRACT_ENTITIES = [
    Extraction(entity_type="Person", field="eprprepared", prop="preparedBy"),
    Extraction(entity_type="Place", field="eprplace", prop="place"),
]


def export_eprrships(rows: list[EPRRship]) -> list[dict]:
    """Export EPRRship rows to JSON-LD entity dicts."""
    results: list[dict] = []
    for row in rows:
        if not row.eid or not row.pubid:
            continue
        rel_type = row.relationship.replace(" ", "_") if row.relationship else ""
        entity: dict = {
            "@id": f"#{quote(row.pubid)}-{quote(row.eid)}",
            "@type": ["Relationship", rel_type] if rel_type else ["Relationship"],
            "identifier": f"{row.pubid}-{row.eid}",
            "description": row.description,
            "source": {"@id": f"#{quote(row.pubid)}"},
            "target": {"@id": f"#{quote(row.eid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
