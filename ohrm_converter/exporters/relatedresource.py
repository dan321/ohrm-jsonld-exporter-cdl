"""RelatedResource exporter."""
from __future__ import annotations
import re
from urllib.parse import quote
from ohrm_converter.exporters.base import map_properties
from ohrm_converter.models import RelatedResource

PROPERTY_MAPPINGS = {
    "rrstartdate": "startDate",
    "rrsdatemod": "startDateModifier",
    "rrstart": "startDateISOString",
    "rrenddate": "endDate",
    "rredatemod": "endDateModifier",
    "rrend": "endDateISOString",
    "rrdatequal": "dateQualifier",
    "rrnote": "processingNotes",
    "rrrating": "relationshipStrength",
    "rrappenddate": "recordAppendDate",
    "rrlastmodd": "recordLastModified",
}

def export_relatedresources(rows: list[RelatedResource]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        if not row.rid or not row.rrid:
            continue
        entity_type: list[str] = ["Relationship"]
        if row.rtype:
            entity_type.append(re.sub(r"\s", "", row.rtype))
        entity: dict = {
            "@id": f"#{quote(row.rid)}-{quote(row.rrid)}",
            "@type": entity_type,
            "identifier": f"{row.rid}-{row.rrid}",
            "name": f"#{quote(row.rid)}-{quote(row.rrid)}",
            "description": row.rrdescription,
            "source": {"@id": f"#{quote(row.rid)}"},
            "target": {"@id": f"#{quote(row.rrid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        results.append(entity)
    return results
