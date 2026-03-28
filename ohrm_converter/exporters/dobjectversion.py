"""DObjectVersion exporter."""
from __future__ import annotations
import re
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import DObjectVersion

PROPERTY_MAPPINGS = {
    "dovformat": "format",
    "dovdefault": "primaryVersion",
    "dovattributes": "dovattributes",
    "dovstartdate": "startDate",
    "dovsdatemod": "startDateModifier",
    "dovstart": "startDateISOString",
    "dovenddate": "endDate",
    "dovedatemod": "endDateModifier",
    "dovend": "endDateISOString",
    "dovphysdesc": "physicalDescription",
    "dovcreator": "resourceCreator",
    "dovcontrol": "controlCode",
    "dovreference": "note",
    "dovnotes": "processingNotes",
    "dovstatus": "outputStatus",
    "dovappenddate": "recordAppendDate",
    "dovlastmodd": "recordLastModified",
    "dovimagedisplay": "dovimagedisplay",
    "dovorder": "dovorder",
    "dovportrait": "imageOrientation",
}
EXTRACT_ENTITIES = [Extraction(entity_type="Place", field="dovplace", prop="place")]
VIEWER_PATH_RE = re.compile(r"image_viewer_paged\.htm\?")

def export_dobjectversions(rows: list[DObjectVersion]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        dov_id = row.dov
        if not dov_id or not row.doid:
            continue
        parent_type = "File"
        if row.dovtype == "multipage image":
            match = VIEWER_PATH_RE.search(dov_id)
            if match:
                stub = dov_id[:match.start()]
                codes = dov_id[match.end():]
                subdir = codes.split(",")[0]
                dov_id = stub + subdir
                parent_type = "Dataset"
            else:
                continue
        entity: dict = {
            "@id": quote(dov_id, safe="/:@"), "@type": [parent_type, "DigitalObjectVersion", row.dovtype],
            "dobjectIdentifier": row.doid, "name": row.dovtitle or dov_id,
            "description": row.dovdescription, "dobject": {"@id": f"#{quote(row.doid)}"},
        }
        if row.arcid:
            entity["linkedArchivalResource"] = {"@id": f"#{quote(row.arcid)}"}
        if row.pubid:
            entity["linkedPublishedResource"] = {"@id": f"#{quote(row.pubid)}"}
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
