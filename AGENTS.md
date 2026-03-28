# AGENTS.md

> This file helps AI coding agents understand the repository.
> It is agent-agnostic and should be kept in version control.

## Project Overview

OHRM Converter — a Python CLI tool that converts OHRM (Online Heritage Records Management) database dumps into RO-Crate JSON-LD format. It loads PostgreSQL SQL dumps into a temporary SQLite database, runs per-table exporters to build an RO-Crate graph, and outputs `ro-crate-metadata.json`. No Docker or PostgreSQL installation required.

## Tech Stack

- **Language:** Python 3.12
- **Package manager:** uv
- **Build backend:** hatchling
- **CLI:** Typer
- **Data models:** Pydantic
- **RO-Crate:** ro-crate-py
- **Database:** SQLite (stdlib, temporary — loads from PostgreSQL SQL dumps)

## Directory Structure

```
ohrm-jsonld-exporter-cdl/
├── pyproject.toml                # hatchling build, CLI entry point, dependencies
├── .python-version               # Python 3.12
├── uv.lock
├── ohrm_converter/               # Main package
│   ├── __init__.py
│   ├── cli.py                    # Typer CLI — batch OHRM discovery and conversion
│   ├── config.py                 # RO-Crate 1.1 spec constants
│   ├── loader.py                 # SQL cleaning (Postgres→SQLite) + temp DB lifecycle
│   ├── crate.py                  # RO-Crate assembly, dedup, relationship linking
│   ├── models/                   # Pydantic models (one per OHRM table)
│   │   ├── entity.py             # Entity, EntityEvent, EntityName
│   │   ├── resource.py           # ArcResource, DObject, DObjectVersion, PubResource
│   │   ├── function.py           # Function
│   │   ├── relationship.py       # EARRship, EDORship, EFRship, RelatedEntity, RelatedResource
│   │   └── metadata.py           # Html, HtmlMetadata
│   └── exporters/                # One exporter per table → JSON-LD entities
│       ├── base.py               # Shared: map_properties(), extract_entity()
│       ├── entity.py
│       ├── arcresource.py
│       ├── dobject.py
│       ├── dobjectversion.py
│       ├── entityevent.py
│       ├── entityname.py
│       ├── function.py
│       ├── pubresource.py
│       ├── relatedentity.py
│       ├── relatedresource.py
│       ├── earrship.py
│       ├── edorship.py
│       └── efrship.py
├── tests/                        # pytest test suite
├── scripts/
│   ├── batch_test.py             # Batch converter run + comparison against reference output
│   └── pg_validate.py            # Row-level validation of SQLite output against PostgreSQL
├── figshare.py                   # Standalone Figshare upload script (optional)
└── legacy/                       # Original Node.js implementation (reference only)
```

## Module Guide

- **`cli.py`** — Typer CLI entry point: discovers OHRM folders, orchestrates batch conversion
- **`loader.py`** — Cleans PostgreSQL SQL syntax for SQLite, loads into temp DB, provides `fetch_all()` helper
- **`crate.py`** — Runs all exporters, deduplicates extracted entities, links relationships bidirectionally, writes RO-Crate output
- **`models/`** — Pydantic BaseModel classes matching the fixed OHRM database schema
- **`exporters/`** — 13 exporters mapping DB rows to JSON-LD entities via property mappings and entity extraction
- **`figshare.py`** — Standalone Figshare upload client (not part of the converter package)

## Getting Started

```bash
# Install
uv sync

# Convert all OHRMs in a directory
ohrm-converter ./path/to/ohrm-collection/ -o output/

# Run tests
uv run pytest tests/ -v
```

## Testing

- **Framework:** pytest
- **Location:** `tests/`
- **Run:** `uv run pytest tests/ -v`
- **Coverage:** unit tests for loader, models, all 13 exporters, CLI; integration test against ULSS reference data

## Key Commands

| Command | Description |
|---------|-------------|
| `uv sync` | Install dependencies |
| `uv sync --extra dev` | Install with dev/test dependencies |
| `uv sync --extra validate` | Install with psycopg2 for pg_validate |
| `ohrm-converter <input> -o <output>` | Convert OHRM dumps to RO-Crate JSON-LD (metadata only) |
| `ohrm-converter <input> -o <output> --full-crate` | Copy source files into output, producing complete RO-Crates |
| `uv run pytest tests/ -v` | Run full test suite |
| `python scripts/batch_test.py <downloads/>` | Batch convert and compare against reference output |
| `python scripts/pg_validate.py <ohrm-path>` | Validate SQLite output against PostgreSQL row-for-row |

## Documentation

- `README.md` — Setup instructions, usage, project background
- `LICENCE` — GPL-3.0
- `docs/superpowers/specs/` — Design specification (gitignored)

## Architecture Notes

The converter follows a single-pass pipeline:

1. **Load:** `loader.py` finds the OHRM's `ohrm/web/sql/` directory, resolves `\i` includes, cleans PostgreSQL syntax (type names, escape sequences, boolean values), and loads everything into a temporary SQLite database. Key edge cases in `clean_sql()`: use `split('\n')` not `splitlines()` (Unicode line separators such as U+2028 can appear inside string literals), read files with `encoding='utf-8-sig'` (some OHRM init scripts have a UTF-8 BOM that breaks `\i` detection), and always emit `CREATE TABLE IF NOT EXISTS` (the same table can appear in both the schema file and data files). **Loader assumption:** include resolution assumes dispatcher-only parent files (`\i` directives only) and pure-SQL leaf files — any non-`\i` SQL in a file that also contains `\i` directives will be silently skipped. All known OHRM dumps follow this structure.

2. **Export:** 13 exporters each read their table via `fetch_all()`, map rows to JSON-LD entity dicts using `map_properties()`, and extract stub entities (Person, Place, State, Country, Nationality) for deduplication.

3. **Assemble:** `crate.py` collects all exporter output, deduplicates extracted entities by `@id`, adds everything to an `ROCrate` instance, links relationships bidirectionally (`sourceOf`/`targetOf`), removes orphaned relationships, and writes `ro-crate-metadata.json`.

4. **Cleanup:** The temporary SQLite database is deleted when the context manager exits.

Root dataset metadata (title, creator, description, URL) is read from the `html` and `htmlmetadata` tables within the OHRM data itself — no external configuration required.
