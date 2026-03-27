"""Entity-Function relationship exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import EFRship

PROPERTY_MAPPINGS = {
    "rating": "rating",
    "efstartdate": "startDate",
    "efsdatemod": "startDateModifier",
    "efstart": "startDateISOString",
    "efenddate": "endDate",
    "efedatemod": "endDateModifier",
    "efend": "endDateISOString",
    "efcitation": "citation",
    "efnote": "processingNotes",
    "efappenddate": "recordAppendDate",
    "eflastmodd": "recordLastModified",
    "ordering": "ordering",
}
EXTRACT_ENTITIES = [
    Extraction(entity_type="Person", field="efprepared", prop="preparedBy"),
    Extraction(entity_type="Place", field="efplace", prop="place"),
    Extraction(entity_type="State", field="efplacestate", prop="state"),
    Extraction(entity_type="Country", field="efplacecountry", prop="country"),
]

def export_efrships(rows: list[EFRship]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        if not row.eid or not row.fid:
            continue
        entity: dict = {
            "@id": f"#{quote(row.eid)}-{quote(row.fid)}",
            "@type": ["Relationship"],
            "identifier": f"{row.eid}-{row.fid}",
            "description": row.description,
            "source": {"@id": f"#{quote(row.eid)}"},
            "target": {"@id": f"#{quote(row.fid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
