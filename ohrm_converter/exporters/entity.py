"""Entity exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import Extraction, extract_entities_from_row, map_properties
from ohrm_converter.models import Entity, EntityEvent, EntityName

PROPERTY_MAPPINGS = {
    "ecountrycode": "countryCode",
    "eorgcode": "organisationCode",
    "esubname": "subName",
    "elegalno": "legalNumber",
    "estartdate": "startDate",
    "esdatemod": "startDateModifier",
    "estart": "startDateISOString",
    "eenddate": "endDate",
    "eedatemod": "endDateModifier",
    "eend": "endDateISOString",
    "edatequal": "dateQualifier",
    "elegalstatus": "legalStatus",
    "efunction": "function",
    "esumnote": "summaryNote",
    "efullnote": "fullNote",
    "egender": "gender",
    "ereference": "reference",
    "enote": "processingNotes",
    "eappenddate": "recordAppendDate",
    "elastmodd": "recordLastModified",
    "elogo": "logo",
    "eurl": "url",
    "earchives": "archives",
    "epub": "epub",
    "eonline": "online",
    "egallery": "gallery",
    "eowner": "owner",
    "erating": "rating",
    "estatus": "status",
    "x_efunction": "x_efunction",
}

EXTRACT_ENTITIES = [
    Extraction(entity_type="Person", field="eprepared", prop="preparedBy"),
    Extraction(entity_type="Place", field="ebthplace", prop="birthPlace"),
    Extraction(entity_type="State", field="ebthstate", prop="birthState"),
    Extraction(entity_type="Country", field="ebthcountry", prop="birthCountry"),
    Extraction(entity_type="Place", field="edthplace", prop="deathPlace"),
    Extraction(entity_type="State", field="edthstate", prop="deathState"),
    Extraction(entity_type="Country", field="edthcountry", prop="deathCountry"),
    Extraction(entity_type="Nationality", field="enationality", prop="nationality"),
]


def export_entities(
    rows: list[Entity],
    events: list[EntityEvent],
    names: list[EntityName],
) -> list[dict]:
    """Export Entity rows to JSON-LD entity dicts."""
    results: list[dict] = []

    # Build lookup maps for cross-references
    events_by_eid: dict[str, list[EntityEvent]] = {}
    for ev in events:
        if ev.eid:
            events_by_eid.setdefault(ev.eid, []).append(ev)

    names_by_eid: dict[str, list[EntityName]] = {}
    for nm in names:
        if nm.eid:
            names_by_eid.setdefault(nm.eid, []).append(nm)

    for row in rows:
        # Build @type from etype field
        entity_type = []
        if row.etype:
            entity_type = [v.strip().replace(" ", "_") for v in row.etype.split("-")]

        # Cross-references
        also_known_as = [
            {"@id": f"#{quote(nm.eid)}_alsoKnownAs"}
            for nm in names_by_eid.get(row.eid, [])
        ]
        related_events = [
            {"@id": f"#{quote(ev.eid)}_event"}
            for ev in events_by_eid.get(row.eid, [])
        ]

        entity: dict = {
            "@id": f"#{quote(row.eid)}",
            "@type": entity_type,
            "identifier": row.eid,
            "name": row.ename,
        }

        if also_known_as:
            entity["alsoKnownAs"] = also_known_as
        if related_events:
            entity["relatedEvents"] = related_events

        map_properties(row, entity, PROPERTY_MAPPINGS)
        extract_entities_from_row(row, entity, EXTRACT_ENTITIES, results)

        results.append(entity)

    return results
