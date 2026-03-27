"""PubResource-Repository relationship exporter."""
from __future__ import annotations
from urllib.parse import quote
from ohrm_converter.exporters.base import map_properties
from ohrm_converter.models import PRREPRship

PROPERTY_MAPPINGS = {
    "prrepref": "repositoryReference",
    "prrepappenddate": "recordAppendDate",
    "prreplastmodd": "recordLastModified",
}


def export_prreprships(rows: list[PRREPRship]) -> list[dict]:
    """Export PRREPRship rows to JSON-LD entity dicts."""
    results: list[dict] = []
    for row in rows:
        if not row.pubid or not row.repid:
            continue
        entity: dict = {
            "@id": f"#{quote(row.pubid)}-{quote(row.repid)}",
            "@type": ["Relationship"],
            "identifier": f"{row.pubid}-{row.repid}",
            "description": row.prrepdescription,
            "source": {"@id": f"#{quote(row.pubid)}"},
            "target": {"@id": f"#{quote(row.repid)}"},
        }
        map_properties(row, entity, PROPERTY_MAPPINGS)
        results.append(entity)
    return results
