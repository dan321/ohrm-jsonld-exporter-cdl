"""DObject exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import DObject, DObjectVersion

PROPERTY_MAPPINGS = {
    "dostartdate": "startDate",
    "dosdatemod": "startDateModifier",
    "dostart": "startDateISOString",
    "doenddate": "endDate",
    "doedatemod": "endDateModifier",
    "doend": "endDateISOString",
    "dophysdesc": "physicalDescription",
    "docreator": "resourceCreator",
    "docontrol": "controlCode",
    "doreference": "note",
    "dorights": "objectIPRights",
    "donotes": "processingNotes",
    "dostatus": "outputStatus",
    "doappenddate": "recordAppendDate",
    "dolastmodd": "recordLastModified",
    "dointerpretation": "dointerpretation",
}
EXTRACT_ENTITIES = [
    Extraction(entity_type="Person", field="doprepared", prop="preparedBy"),
    Extraction(entity_type="Place", field="doplace", prop="place"),
]

def export_dobjects(rows: list[DObject], versions: list[DObjectVersion]) -> list[dict]:
    results: list[dict] = []
    versions_by_doid: dict[str, list[DObjectVersion]] = {}
    for v in versions:
        if v.doid:
            versions_by_doid.setdefault(v.doid, []).append(v)
    for row in rows:
        has_file = [{"@id": quote(v.dov, safe="/:@")} for v in versions_by_doid.get(row.doid, []) if v.dov]
        entity: dict = {
            "@id": f"#{quote(row.doid)}", "@type": ["RepositoryObject", "DigitalObject", row.dotype],
            "identifier": row.doid, "name": row.dotitle,
            "description": row.dodescription, "hasFile": has_file,
        }
        if row.arcid:
            entity["linkedArchivalResource"] = {"@id": f"#{quote(row.arcid)}"}
        if row.pubid:
            entity["linkedPublishedResource"] = {"@id": f"#{quote(row.pubid)}"}
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
