"""Function exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import map_properties
from ohrm_converter.models import Function

PROPERTY_MAPPINGS = {
    "fstartdate": "startDate",
    "fsdatemod": "dateModifier",
    "fstart": "startDateISOString",
    "fenddate": "endDate",
    "fedatemod": "dateModifier",
    "fend": "endDateISOString",
    "fdatequal": "dateQualifier",
    "fapplies": "fapplies",
    "fappenddate": "recordAppendDate",
    "flastmodd": "recordLastModified",
    "fnote": "processingNotes",
    "fparent": "fparent",
}

def export_functions(rows: list[Function]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        entity: dict = {
            "@id": f"#{quote(row.fid)}", "@type": ["Function"],
            "identifier": row.fid, "name": row.fname, "description": row.fdescription,
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        results.append(entity)
    return results
