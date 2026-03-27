"""Shared exporter utilities."""
from __future__ import annotations
from urllib.parse import quote
from pydantic import BaseModel

type PropertyMapping = str | tuple[str, str]

def map_properties(
    row: BaseModel,
    entity: dict,
    mappings: list[PropertyMapping],
) -> None:
    """Copy model fields to JSON-LD properties.
    Matches Node.js behaviour: only sets property if the value is truthy.
    """
    for mapping in mappings:
        if isinstance(mapping, tuple):
            field, prop = mapping
        else:
            field = prop = mapping
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
    extractions: list[tuple[str, str, str]],
    collected: list[dict],
) -> None:
    """Extract related entities from a row and link them.
    extractions: list of (entity_type, field_name, jsonld_property) tuples
    """
    for entity_type, field, prop in extractions:
        value = getattr(row, field, None)
        if value:
            stub = extract_entity(entity_type, value)
            collected.append(stub)
            entity[prop] = {"@id": stub["@id"]}
