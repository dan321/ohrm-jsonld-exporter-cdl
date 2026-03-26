# AGENTS.md

> This file helps AI coding agents understand the repository.
> It is agent-agnostic and should be kept in version control.

## Project Overview

OHRM JSON-LD Exporter — a tool that dumps an OHRM (Open Heritage Records Management) PostgreSQL database to JSON-LD format using the RO-Crate standard. A Node.js CLI reads the database via Sequelize, runs per-table exporters to build an RO-Crate graph, and outputs `ro-crate-metadata.json`. A Python automation layer orchestrates batch conversion and uploads results to Figshare.

## Tech Stack

- **Languages:** JavaScript (Node.js 18), Python 3.12
- **ORM:** Sequelize 6
- **Package manager:** npm (Node.js), uv (Python)
- **Database:** PostgreSQL 13
- **Containerisation:** Docker Compose
- **Key Node.js deps:** `ro-crate`, `ro-crate-html`, `sequelize`, `sequelize-auto`, `pg`, `yargs`, `lodash`, `fs-extra`
- **Key Python deps:** `docker`, `pyyaml`, `requests`

## Directory Structure

```
ohrm-jsonld-exporter-cdl/
├── index.js                 # Main CLI entry point
├── configuration.js         # DB connection, domain prefix, RO-Crate defaults
├── convert-and-upload.py    # Python: batch convert + Figshare upload
├── figshare.py              # Figshare API integration (chunked upload)
├── docker-compose.yml       # PostgreSQL + Node.js exporter services
├── package.json             # Node.js manifest
├── pyproject.toml            # Python project and dependency definition
├── exporters/               # One exporter class per OHRM table
│   ├── index.js             # Re-exports all exporters
│   ├── entity.js            # Entity exporter
│   ├── arcresource.js       # Archival resource exporter
│   ├── dobject.js           # Digital object exporter
│   └── ...                  # ~15 more domain exporters
├── models/                  # Sequelize models (auto-generated from DB)
│   ├── init-models.js       # Model initialisation
│   └── ...                  # ~45 models matching OHRM schema
└── README.md
```

## Module Guide

- **`index.js`** — CLI application: connects to DB, runs all exporters, assembles RO-Crate, writes JSON-LD output
- **`exporters/`** — Per-table exporters, each with an `export()` method that maps DB rows to JSON-LD entities
- **`models/`** — Sequelize ORM models reflecting the OHRM database schema
- **`configuration.js`** — Centralised config: DB params (from env vars), domain prefix, RO-Crate context/descriptor
- **`convert-and-upload.py`** — Python orchestration: discovers OHRMs, invokes Node.js conversion via Docker, uploads to Figshare
- **`figshare.py`** — Figshare API client: article creation, chunked file uploads, authentication

## Getting Started

```bash
# Start Docker services (PostgreSQL + exporter container)
docker compose up -d

# Load an OHRM database dump into the DB container
docker exec -it ohrm-jsonld-exporter-db-1 /bin/bash
# Inside container: psql -U postgres < /srv/data/<dump>.sql

# Run conversion (stdout)
docker exec -it ohrm-jsonld-exporter-exporter-1 bash
node .

# Run conversion (to file)
export DB_DATABASE='dhra'
node . -o ./data/dhra-jsonld

# Python batch workflow (outside Docker)
uv sync
uv run python convert-and-upload.py -d <ohrm_dir> -a <figshare_endpoint> -t <token>
```

## Testing

- **No formal test framework** — `package.json` has no test runner configured
- **Manual testing:** load sample OHRM databases into Docker, run the exporter, inspect `ro-crate-metadata.json` output

## Key Commands

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start PostgreSQL + exporter containers |
| `node .` | Convert current DB to JSON-LD (stdout) |
| `node . -o ./data/<dir>` | Convert and write to output directory |
| `node . -d <dbname>` | Convert a specific database |
| `python convert-and-upload.py` | Batch convert + upload to Figshare |

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DB_DATABASE` | PostgreSQL database name |
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | PostgreSQL host (default: `db` in Docker) |

## Documentation

- `README.md` — Setup instructions, Docker workflow, CLI usage, Python automation guide
- `LICENCE` — GPL-3.0

## Architecture Notes

The system follows a two-phase pipeline:

1. **Export (Node.js):** `index.js` initialises Sequelize models against the OHRM PostgreSQL schema, then iterates through each exporter in `exporters/`. Each exporter queries its table, maps rows to Schema.org-typed JSON-LD entities, and adds them to an `ROCrate` instance. After all exporters run, cross-entity relationships are linked, and the crate is serialised as `ro-crate-metadata.json`.

2. **Orchestration (Python):** `convert-and-upload.py` scans a directory of OHRM database dumps, spins up Docker containers for each, runs the Node.js exporter, packages the output, and uploads to Figshare via the API client in `figshare.py`.

The domain prefix (`https://ctac.esrc.unimelb.edu.au`) is hardcoded in `configuration.js` and used to mint entity URIs.
