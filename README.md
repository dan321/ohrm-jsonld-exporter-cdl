# OHRM Converter

A Python CLI tool that converts OHRM (Online Heritage Records Management) database dumps into [RO-Crate](https://www.researchobject.org/ro-crate/) JSON-LD format.

No Docker or PostgreSQL installation required — the tool loads SQL dumps directly into a temporary SQLite database.

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

Point the tool at a directory containing one or more OHRM folders:

```bash
# Metadata only (default)
ohrm-converter ./path/to/ohrm-collection/ -o output/

# Full crate — copies source files into output alongside the generated metadata
ohrm-converter ./path/to/ohrm-collection/ -o output/ --full-crate
```

Each OHRM folder must contain an `ohrm/` subdirectory with `web/sql/` inside it (the standard OHRM dump structure). The tool discovers all valid OHRM folders in the input directory and converts each one.

By default, only `ro-crate-metadata.json` is written per dataset. With `--full-crate`, the entire source folder is copied into the output first, then the freshly generated metadata is written on top (replacing any existing `ro-crate-metadata.json` from the source).

Output (default):
```
output/
├── ULSS-ro-crate/
│   └── ro-crate-metadata.json
├── AABR-ro-crate/
│   └── ro-crate-metadata.json
└── ...
```

Output (`--full-crate`):
```
output/
├── ULSS-ro-crate/
│   ├── ro-crate-metadata.json    ← freshly generated
│   ├── web/
│   ├── objects/
│   ├── data/
│   └── ...                       ← all source files
└── ...
```

**Note:** The tool does not currently generate `ro-crate-preview.html`. This is planned for a future release.

## How It Works

1. **Load** — Reads the OHRM SQL dump files, cleans PostgreSQL-specific syntax, and loads them into a temporary SQLite database
2. **Export** — 13 per-table exporters map database rows to JSON-LD entities using the RO-Crate standard
3. **Assemble** — Deduplicates extracted entities (Person, Place, etc.), links relationships bidirectionally, and writes `ro-crate-metadata.json`
4. **Cleanup** — The temporary database is deleted automatically

## Development

```bash
# Install with dev dependencies
uv sync
uv pip install -e ".[dev]"

# Run tests
uv run pytest tests/ -v
```

## Repository Layout

- `ohrm_converter/` — Main Python package
  - `cli.py` — Typer CLI entry point
  - `loader.py` — SQL cleaning and SQLite loading
  - `crate.py` — RO-Crate assembly and relationship linking
  - `models/` — Pydantic models for the OHRM database schema
  - `exporters/` — 15 per-table exporters (DB rows → JSON-LD entities)
- `tests/` — pytest test suite
- `legacy/figshare.py` — Standalone Figshare upload script (legacy)
- `legacy/` — Original Node.js implementation (reference only)

## OHRM Tables Coverage

The converter exports all core data and relationship tables from the OHRM schema. The following tables are **not exported** as they contain web display configuration, lookup enums, or application metadata rather than heritage record data:

| Category | Tables | Reason |
|---|---|---|
| Web display config | `html` (100+ display columns), `htmladditional`, `htmlicon`, `htmlvariables` | Page layout, colours, stylesheets — not heritage data. `html.title`, `html.creator`, `html.description` are read for RO-Crate root metadata. |
| Lookup/enum tables | `typeofentity`, `typeofresource`, `typeofwork`, `typeofformat`, `typeofcontent`, `typeofarformats`, `relationships`, `resourcerelationships`, `subject`, `decades` | Reference values already embedded in data rows |
| Contacts | `contact`, `ecrship` | Contact people and entity↔contact links |
| Categories | `category`, `catership` | Category definitions and entity↔category links |
| Sponsorship | `sponsors`, `spons_entity`, `spons_entity_updates`, `spons_type` | Funding and sponsorship data |
| System config | `ohrmsystem` | OHRM system metadata |
| Features | `onthisday`, `dataentryprotocol` | Web feature config and data entry workflow |

If any of these tables contain data relevant to your use case, they can be added as new exporters following the existing pattern in `ohrm_converter/exporters/`.

## Figshare Upload (Optional)

The standalone `legacy/figshare.py` script can upload converted RO-Crates to Figshare. Install the optional dependencies first:

```bash
uv sync --extra figshare
```

See `legacy/figshare.py` for usage details.

## Licence

GPL-3.0 — see `LICENCE`.
