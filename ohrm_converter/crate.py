"""RO-Crate assembly — combines exporter outputs into JSON-LD."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from rocrate.rocrate import ROCrate

from ohrm_converter.exporters import (
    export_arcresources, export_dobjects, export_dobjectversions,
    export_earrships, export_edorships, export_efrships,
    export_entities, export_entityevents, export_entitynames,
    export_functions, export_pubresources,
    export_relatedentities, export_relatedresources,
)
from ohrm_converter.loader import fetch_all
from ohrm_converter.models import (
    ArcResource, DObject, DObjectVersion, EARRship, EDORship, EFRship,
    Entity, EntityEvent, EntityName, Function, Html, HtmlMetadata,
    PubResource, RelatedEntity, RelatedResource,
)

# Types that get deduplicated across all exporters
EXTRACTED_ENTITY_TYPES = frozenset({"Person", "Place", "State", "Country", "Nationality", "Contact"})

# Exporter results → root dataset property names (in execution order)
ROOT_DATASET_PROPERTIES = [
    "archivalResources",
    "digitalObjects",
    "digitalObjectVersions",
    "entityArchivalRelationships",
    "entityDobjectRelationships",
    "entityFunctionRelationships",
    "entities",
    "entityEvent",
    "entityName",
    "entityFunction",
    "publishedResources",
    "entityRelationships",
    "resourceRelationships",
]


def _read_root_metadata(conn: sqlite3.Connection) -> dict:
    """Read title, creator, description from the html table."""
    rows = fetch_all(conn, "html", Html)
    if rows:
        row = rows[0]
        return {
            "title": row.title or "OHRM Dataset",
            "description": row.description,
            "creator": row.creator,
        }
    return {"title": "OHRM Dataset"}


def _read_dataset_url(conn: sqlite3.Connection) -> str | None:
    """Read DC.Identifier URL from htmlmetadata table if present."""
    rows = fetch_all(conn, "htmlmetadata", HtmlMetadata)
    for row in rows:
        if row.name == "DC.Identifier" and row.scheme == "URL" and row.content:
            return row.content
    return None


def _run_all_exporters(conn: sqlite3.Connection) -> list[list[dict]]:
    """Run all 13 exporters and return results in order."""
    entity_rows = fetch_all(conn, "entity", Entity)
    event_rows = fetch_all(conn, "entityevent", EntityEvent)
    name_rows = fetch_all(conn, "entityname", EntityName)
    arc_rows = fetch_all(conn, "arcresource", ArcResource)
    dobj_rows = fetch_all(conn, "dobject", DObject)
    dov_rows = fetch_all(conn, "dobjectversion", DObjectVersion)
    pub_rows = fetch_all(conn, "pubresource", PubResource)
    func_rows = fetch_all(conn, "function", Function)
    earr_rows = fetch_all(conn, "earrship", EARRship)
    edor_rows = fetch_all(conn, "edorship", EDORship)
    efr_rows = fetch_all(conn, "efrship", EFRship)
    re_rows = fetch_all(conn, "relatedentity", RelatedEntity)
    rr_rows = fetch_all(conn, "relatedresource", RelatedResource)

    return [
        export_arcresources(arc_rows),
        export_dobjects(dobj_rows, dov_rows),
        export_dobjectversions(dov_rows),
        export_earrships(earr_rows),
        export_edorships(edor_rows),
        export_efrships(efr_rows),
        export_entities(entity_rows, event_rows, name_rows),
        export_entityevents(event_rows, entity_rows),
        export_entitynames(name_rows),
        export_functions(func_rows),
        export_pubresources(pub_rows),
        export_relatedentities(re_rows),
        export_relatedresources(rr_rows),
    ]


def _dedup_by_id(entities: list[dict]) -> list[dict]:
    """Deduplicate entities by @id, keeping first occurrence."""
    seen: set[str] = set()
    result: list[dict] = []
    for e in entities:
        eid = e.get("@id")
        if eid and eid not in seen:
            seen.add(eid)
            result.append(e)
    return result


def _safe_add_jsonld(crate: ROCrate, entity: dict) -> str:
    """Add a JSON-LD entity to the crate, skipping if already present.

    Returns the entity @id. Works around ro-crate-py's add_jsonld which
    mutates the input dict (pops @id) and raises ValueError on duplicates.
    """
    entity_id = entity.get("@id", "")
    if crate.dereference(entity_id):
        return entity_id
    # add_jsonld will pop @id from the dict — pass a shallow copy
    crate.add_jsonld(dict(entity))
    return entity_id


def build_crate(conn: sqlite3.Connection, output_path: Path) -> None:
    """Build an RO-Crate from the database and write to output_path."""
    crate = ROCrate()

    # Set root metadata
    metadata = _read_root_metadata(conn)
    for key, value in metadata.items():
        if value:
            crate.root_dataset[key] = value

    dataset_url = _read_dataset_url(conn)
    if dataset_url:
        crate.root_dataset["url"] = dataset_url

    # Run all exporters
    exporter_results = _run_all_exporters(conn)

    # Separate extracted entities (Person, Place, etc.) from main entities
    type_maps: dict[str, list[dict]] = {t: [] for t in EXTRACTED_ENTITY_TYPES}

    for idx, exporter_entities in enumerate(exporter_results):
        prop_name = ROOT_DATASET_PROPERTIES[idx]
        main_entities: list[str] = []

        for entity in exporter_entities:
            entity_type = entity.get("@type", [])
            if isinstance(entity_type, str):
                entity_type_list = [entity_type]
            else:
                entity_type_list = entity_type

            # Check if this is an extracted entity type (single-type like "Person")
            if (
                len(entity_type_list) == 1
                and entity_type_list[0] in EXTRACTED_ENTITY_TYPES
            ):
                type_maps[entity_type_list[0]].append(entity)
            else:
                entity_id = _safe_add_jsonld(crate, entity)
                main_entities.append(entity_id)

        # Set root dataset property
        if main_entities:
            crate.root_dataset[prop_name] = [
                {"@id": eid} for eid in main_entities
            ]

    # Deduplicate and add extracted entities
    for entity_type, entities in type_maps.items():
        deduped = _dedup_by_id(entities)
        deduped_ids: list[str] = []
        for entity in deduped:
            eid = _safe_add_jsonld(crate, entity)
            deduped_ids.append(eid)
        if deduped_ids:
            crate.root_dataset[entity_type] = [
                {"@id": eid} for eid in deduped_ids
            ]

    # Link relationships bidirectionally
    for entity in list(crate.get_entities()):
        props = dict(entity.properties())
        entity_type = props.get("@type", [])
        if isinstance(entity_type, str):
            entity_type = [entity_type]
        if "Relationship" not in entity_type:
            continue

        source_ref = props.get("source")
        target_ref = props.get("target")

        if not source_ref or not target_ref:
            continue

        # source/target can be a dict or a ContextEntity reference
        if isinstance(source_ref, dict):
            source_id = source_ref.get("@id")
        else:
            source_id = source_ref.id if hasattr(source_ref, 'id') else str(source_ref)

        if isinstance(target_ref, dict):
            target_id = target_ref.get("@id")
        else:
            target_id = target_ref.id if hasattr(target_ref, 'id') else str(target_ref)

        if not source_id or not target_id:
            continue

        src_entity = crate.dereference(source_id)
        tgt_entity = crate.dereference(target_id)

        if not src_entity or not tgt_entity:
            # Orphaned relationship — remove it
            crate.delete(entity)
            continue

        # Add back-references
        src_props = dict(src_entity.properties())
        src_source_of = src_props.get("sourceOf", [])
        if not isinstance(src_source_of, list):
            src_source_of = [src_source_of]
        src_source_of.append({"@id": entity.id})
        src_entity["sourceOf"] = src_source_of

        tgt_props = dict(tgt_entity.properties())
        tgt_target_of = tgt_props.get("targetOf", [])
        if not isinstance(tgt_target_of, list):
            tgt_target_of = [tgt_target_of]
        tgt_target_of.append({"@id": entity.id})
        tgt_entity["targetOf"] = tgt_target_of

        # Build descriptive name
        rel_types = [t for t in entity_type if t != "Relationship"]
        rel_name = " ".join(rel_types) if rel_types else "Relationship"
        src_name = src_props.get("name", source_id)
        tgt_name = tgt_props.get("name", target_id)
        entity["name"] = f"{src_name} -> {rel_name} -> {tgt_name}"

    # Write output
    output_path.mkdir(parents=True, exist_ok=True)
    crate.write(output_path)
