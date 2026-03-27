"""ArcResource exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import extract_entities_from_row, map_properties
from ohrm_converter.models import ArcResource

PROPERTY_MAPPINGS = [
    ("repid", "repositoryId"), ("arrepref", "archiveIdentifier"),
    ("arrepreflink", "archiveLink"), ("arlanguage", "resourceLanguage"),
    ("arstartdate", "startDate"), ("arsdatemod", "startDateModifier"),
    ("arstart", "startDateISOString"), ("arenddate", "endDate"),
    ("aredatemod", "endDateModifier"), ("arend", "endDateISOString"),
    ("arquantityl", "linearMetres"), ("arquantityn", "numberOfItems"),
    ("arquantityt", "typeOfItems"), ("arformats", "formatOfItems"),
    ("araccess", "accessConditions"), "arotherfa",
    ("arref", "organisationalIdentifier"), ("arappenddate", "recordCreationDate"),
    ("arlastmodd", "recordLastModifiedDate"), ("arcreator", "resourceCreator"),
    ("arlevel", "levelOfCollection"), ("arprocessing", "processingNote"),
    ("arstatus", "outputStatus"),
]
EXTRACT_ENTITIES = [("Person", "arprepared", "preparedBy")]

def export_arcresources(rows: list[ArcResource]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        entity: dict = {
            "@id": f"#{quote(row.arcid)}", "@type": "ArchivalResource",
            "identifier": row.arcid, "name": row.artitle,
            "subTitle": row.arsubtitle, "description": row.ardescription,
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
