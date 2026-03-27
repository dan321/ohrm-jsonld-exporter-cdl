"""Shared exporter utilities."""
from __future__ import annotations
from typing import NamedTuple
from urllib.parse import quote
from pydantic import BaseModel


class Extraction(NamedTuple):
    """Defines an entity to extract from a row."""
    entity_type: str
    field: str
    prop: str


def map_properties(
    row: BaseModel,
    entity: dict,
    mappings: dict[str, str],
) -> None:
    """Copy model fields to JSON-LD properties.

    mappings: dict of {db_field: jsonld_property}
    Matches Node.js behaviour: only sets property if the value is truthy.
    """
    for field, prop in mappings.items():
        value = getattr(row, field, None)
        if value:
            entity[prop] = value


def extract_entity(entity_type: str, value: str) -> dict:
    """Create a stub entity for Person, Place, State, Country, Nationality."""
    return {
        "@id": f"#{quote(str(value))}",
        "@type": entity_type,
        "name": value,
    }


def extract_entities_from_row(
    row: BaseModel,
    entity: dict,
    extractions: list[Extraction],
    collected: list[dict],
) -> None:
    """Extract related entities from a row and link them."""
    for ext in extractions:
        value = getattr(row, ext.field, None)
        if value:
            stub = extract_entity(ext.entity_type, value)
            collected.append(stub)
            entity[ext.prop] = {"@id": stub["@id"]}
