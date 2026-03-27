"""PubResource exporter."""
from __future__ import annotations
import re
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import PubResource

PROPERTY_MAPPINGS = {
    "online": "online",
    "author": "author",
    "x_year": "publicationYear",
    "secondaryauthor": "secondaryAuthor",
    "secondarytitle": "secondaryTitle",
    "publisher": "publisher",
    "volume": "volume",
    "numberofvolumes": "numberOfVolumes",
    "number": "number",
    "pagenos": "numberOfPages",
    "edition": "edition",
    "x_date": "publicationDate",
    "isbn_issn": "isbn_issn",
    "source": "referenceSource",
    "abstract": "abstract",
    "notes": "notes",
    "classification": "classification",
    "url": "url",
    "urltype": "urlType",
    "urldate": "dateAccessed",
    "format": "format",
    "x_language": "contentLanguage",
    "contains": "contains",
    "pubappenddate": "recordAppendDate",
    "publastmodd": "recordLastModified",
    "descriptionofwork": "descriptionOfWork",
    "catid": "catalogueId",
    "processing": "processingNotes",
    "status": "outputStatus",
}
EXTRACT_ENTITIES = [
    Extraction(entity_type="Person", field="prepared", prop="preparedBy"),
    Extraction(entity_type="Place", field="placepublished", prop="place"),
]

def export_pubresources(rows: list[PubResource]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        entity_type = ["PublishedResource"]
        if row.type:
            entity_type.append(re.sub(r"\s", "", row.type))
        if row.typeofwork:
            entity_type.append(row.typeofwork.replace(" ", "", 1))
        entity: dict = {
            "@id": f"#{quote(row.pubid)}", "@type": entity_type,
            "identifier": row.pubid, "name": row.title,
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)
        results.append(entity)
    return results
