#!/usr/bin/env python3
"""Validate OHRM converter output against PostgreSQL ground truth.

Loads the same OHRM SQL dump into both PostgreSQL (via psql — zero cleaning,
native E-string and \\i support) and our SQLite loader, then compares row counts
and sampled row values for every table in TABLES.

Usage:
    python scripts/pg_validate.py /path/to/OHRM-ro-crate [options]

Requires:
    - PostgreSQL accessible via psql (fix auth if using Postgres.app)
    - psycopg2: uv sync --extra validate
"""

from __future__ import annotations

import argparse
import getpass
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ohrm_converter.loader import (
    TABLES,
    _derive_ohrm_name,
    _find_ohrm_subdir,
    load_ohrm,
)

_PSQL_CANDIDATES = [
    "/Applications/Postgres.app/Contents/Versions/latest/bin/psql",
    "/usr/local/bin/psql",
    "/usr/bin/psql",
    "psql",
]


def _find_psql() -> str:
    for candidate in _PSQL_CANDIDATES:
        if candidate == "psql" or Path(candidate).exists():
            return candidate
    return "psql"


def _find_init_script(sql_dir: Path, ohrm_name: str) -> Path:
    """Find initialise{NAME}.sql with case-insensitive fallback."""
    candidate = sql_dir / f"initialise{ohrm_name}.sql"
    if candidate.exists():
        return candidate
    for f in sql_dir.iterdir():
        if f.name.lower() == f"initialise{ohrm_name.lower()}.sql":
            return f
    raise FileNotFoundError(f"No init script for {ohrm_name} in {sql_dir}")


def _create_temp_db(
    db_name: str, psql: str, pg_user: str, pg_host: str, pg_port: int,
) -> None:
    result = subprocess.run(
        [psql, "-U", pg_user, "-h", pg_host, "-p", str(pg_port),
         "-d", "postgres", "-c", f"CREATE DATABASE {db_name}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"CREATE DATABASE failed:\n{result.stderr.strip()}")


def _drop_temp_db(
    db_name: str, psql: str, pg_user: str, pg_host: str, pg_port: int,
) -> None:
    subprocess.run(
        [psql, "-U", pg_user, "-h", pg_host, "-p", str(pg_port),
         "-d", "postgres", "-c", f"DROP DATABASE IF EXISTS {db_name}"],
        capture_output=True, text=True,
    )


def _load_via_psql(
    db_name: str, sql_dir: Path, init_script: Path,
    psql: str, pg_user: str, pg_host: str, pg_port: int,
) -> subprocess.CompletedProcess:
    # cwd=sql_dir so \\i directives in the init script resolve correctly
    return subprocess.run(
        [psql, "-U", pg_user, "-h", pg_host, "-p", str(pg_port),
         "-d", db_name, "-f", init_script.name],
        capture_output=True, text=True, cwd=str(sql_dir),
    )


def _normalise(val: object) -> str | None:
    """Normalise a DB value to a comparable string."""
    if val is None:
        return None
    if isinstance(val, bool):
        return "1" if val else "0"
    return str(val)


def compare_tables(
    pg_conn,
    sqlite_conn,
    tables: frozenset[str],
) -> list[str]:
    """Compare each table between PG and SQLite. Returns list of mismatched table names."""
    from collections import Counter

    import psycopg2.extras  # imported here so import error is caught in main

    mismatches: list[str] = []

    for table in sorted(tables):
        # ── PostgreSQL side ──────────────────────────────────────────────────
        try:
            with pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f'SELECT * FROM "{table}"')  # noqa: S608
                pg_rows = [dict(r) for r in cur.fetchall()]
        except Exception as exc:
            print(f"  {table:<22} PG error: {exc}")
            pg_conn.rollback()
            continue

        # ── SQLite side ──────────────────────────────────────────────────────
        try:
            sq_cur = sqlite_conn.execute(f'SELECT * FROM "{table}"')  # noqa: S608
            sq_col_names = [d[0] for d in sq_cur.description]
            sq_rows = [dict(zip(sq_col_names, row)) for row in sq_cur.fetchall()]
        except Exception as exc:
            print(f"  {table:<22} SQLite error: {exc}")
            continue

        pg_count = len(pg_rows)
        sq_count = len(sq_rows)

        if pg_count != sq_count:
            print(f"  {table:<22} COUNT  PG={pg_count}  SQLite={sq_count}  ✗")
            mismatches.append(table)
            continue

        if pg_count == 0:
            print(f"  {table:<22} (empty)")
            continue

        # ── Multiset comparison (order-independent) ──────────────────────────
        # PG and SQLite may return identical rows in different order when the
        # sort key has ties, so we compare as multisets using Counter.
        common_cols = sorted(set(pg_rows[0].keys()) & set(sq_rows[0].keys()))

        def _row_tuple(row_dict: dict) -> tuple:
            return tuple(_normalise(row_dict.get(c)) for c in common_cols)

        pg_counter = Counter(_row_tuple(r) for r in pg_rows)
        sq_counter = Counter(_row_tuple(r) for r in sq_rows)

        if pg_counter != sq_counter:
            pg_only = pg_counter - sq_counter
            sq_only = sq_counter - pg_counter
            print(f"  {table:<22} {len(pg_only)} row(s) differ  ✗")
            for row_t in list(pg_only.keys())[:2]:
                row_d = dict(zip(common_cols, row_t))
                print(f"    PG-only:     {row_d}")
            for row_t in list(sq_only.keys())[:2]:
                row_d = dict(zip(common_cols, row_t))
                print(f"    SQLite-only: {row_d}")
            mismatches.append(table)
        else:
            print(f"  {table:<22} {pg_count} rows  ✓")

    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate OHRM converter output against PostgreSQL ground truth.",
    )
    parser.add_argument("ohrm_path", type=Path, help="Path to OHRM RO-Crate directory")
    parser.add_argument("--pg-user", default=getpass.getuser(), help="PostgreSQL user")
    parser.add_argument("--pg-host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--pg-port", type=int, default=5432, help="PostgreSQL port")
    parser.add_argument("--psql", default=None, help="Path to psql binary")
    args = parser.parse_args()

    psql = args.psql or _find_psql()
    ohrm_path = args.ohrm_path.expanduser().resolve()
    ohrm_name = _derive_ohrm_name(ohrm_path)
    sql_dir = _find_ohrm_subdir(ohrm_path) / "web" / "sql"
    init_script = _find_init_script(sql_dir, ohrm_name)
    db_name = f"ohrm_validate_{ohrm_name.lower()}"

    # ── Check psycopg2 ───────────────────────────────────────────────────────
    try:
        import psycopg2
    except ImportError:
        print(
            "psycopg2 not found. Install with:\n  uv sync --extra validate",
            file=sys.stderr,
        )
        return 1

    # ── Test PG connectivity ─────────────────────────────────────────────────
    print(f"Connecting to PostgreSQL as {args.pg_user}@{args.pg_host}:{args.pg_port}...")
    try:
        test = psycopg2.connect(
            host=args.pg_host, port=args.pg_port, user=args.pg_user,
            dbname="postgres", connect_timeout=5,
        )
        test.close()
    except Exception as exc:
        print(f"Cannot connect to PostgreSQL: {exc}", file=sys.stderr)
        print(
            "Fix Postgres.app auth (edit pg_hba.conf or restart server),\n"
            "or pass --pg-user / --pg-host.",
            file=sys.stderr,
        )
        return 1

    # ── Create temp DB ───────────────────────────────────────────────────────
    print(f"Creating temporary database '{db_name}'...")
    try:
        _create_temp_db(db_name, psql, args.pg_user, args.pg_host, args.pg_port)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    try:
        # ── Load via psql ────────────────────────────────────────────────────
        print(f"Loading {ohrm_name} into PostgreSQL via psql...")
        result = _load_via_psql(
            db_name, sql_dir, init_script,
            psql, args.pg_user, args.pg_host, args.pg_port,
        )
        if result.returncode != 0:
            print(f"psql exited {result.returncode} (some errors expected for PG-only syntax):")
            for line in result.stderr.splitlines()[:8]:
                print(f"  {line}")

        pg_conn = psycopg2.connect(
            host=args.pg_host, port=args.pg_port, user=args.pg_user,
            dbname=db_name, connect_timeout=10,
        )

        # ── Load via SQLite ──────────────────────────────────────────────────
        print(f"Loading {ohrm_name} into SQLite...")
        with load_ohrm(ohrm_path) as sqlite_conn:
            print("\nComparing tables:\n")
            mismatches = compare_tables(pg_conn, sqlite_conn, TABLES)

        pg_conn.close()

        print()
        if mismatches:
            print(f"RESULT: {len(mismatches)} table(s) with mismatches: {', '.join(sorted(mismatches))}")
            return 1

        print(f"RESULT: All {len(TABLES)} tables match.")
        return 0

    finally:
        print(f"\nDropping temporary database '{db_name}'...")
        _drop_temp_db(db_name, psql, args.pg_user, args.pg_host, args.pg_port)


if __name__ == "__main__":
    sys.exit(main())
