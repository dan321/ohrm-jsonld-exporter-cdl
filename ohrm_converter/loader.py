"""SQL loader: cleans PostgreSQL dumps and loads into temporary SQLite."""

from __future__ import annotations

import re
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from pydantic import BaseModel as PydanticBaseModel

TABLES = frozenset({
    "entity", "entityevent", "entityname",
    "arcresource", "dobject", "dobjectversion", "pubresource",
    "function",
    "earrship", "edorship", "efrship", "eprrship", "relatedentity", "relatedresource",
    "prreprship", "repository",
    "html", "htmlmetadata",
})


def clean_sql(sql: str) -> str:
    """Clean PostgreSQL-specific syntax for SQLite compatibility."""
    lines = []
    for line in sql.splitlines():
        stripped = line.strip()

        # Skip \i include directives (resolved separately)
        if stripped.startswith("\\i "):
            continue

        # DROP TABLE -> DROP TABLE IF EXISTS (quote name for safety)
        if stripped.upper().startswith("DROP TABLE"):
            table_name = stripped.split()[-1].rstrip(";")
            lines.append(f'DROP TABLE IF EXISTS "{table_name}";')
            continue

        # Quote table names with special characters (hyphens etc.) in SQL statements
        line = re.sub(
            r"((?:CREATE\s+TABLE|INSERT\s+INTO)\s+)([A-Za-z0-9_-]+[^A-Za-z0-9_\s(][A-Za-z0-9_-]*)",
            lambda m: f'{m.group(1)}"{m.group(2)}"',
            line,
            flags=re.IGNORECASE,
        )

        # Type normalisation
        line = re.sub(r"\bint[248]\b", "INTEGER", line, flags=re.IGNORECASE)
        line = re.sub(r"\bfloat8\b", "REAL", line, flags=re.IGNORECASE)
        line = re.sub(r"\bboolean\b", "INTEGER", line, flags=re.IGNORECASE)

        # E'escaped\-strings' -> 'unescaped-strings'
        # Escaped single quotes (\') become doubled quotes ('') for SQLite,
        # all other backslash sequences are simply unescaped.
        def _unescape_pg_string(m: re.Match) -> str:
            inner = m.group(1)
            # Convert escaped single quotes to SQLite doubled quotes
            inner = inner.replace("\\'", "''")
            # Protect literal double-backslash (\\) before handling escapes.
            # In PostgreSQL E-strings, \\\\ is a literal backslash.
            _PLACEHOLDER = "\x00"
            inner = inner.replace("\\\\", _PLACEHOLDER)
            # Convert recognised escape sequences to actual characters
            inner = inner.replace("\\n", "\n")
            inner = inner.replace("\\r", "\r")
            inner = inner.replace("\\t", "\t")
            # Strip remaining backslash escapes (e.g. \- → -)
            inner = re.sub(r"\\(.)", r"\1", inner)
            # Restore literal backslashes
            inner = inner.replace(_PLACEHOLDER, "\\")
            return "'" + inner + "'"

        line = re.sub(r"E'((?:[^'\\]|\\.)*?)'", _unescape_pg_string, line)

        # Boolean string values -> integers
        line = line.replace("'True'", "1").replace("'False'", "0")

        lines.append(line)

    return "\n".join(lines)


def resolve_sql_files(sql_dir: Path, ohrm_name: str) -> list[Path]:
    """Parse the init script and return ordered list of SQL files to execute."""
    init_file = sql_dir / f"initialise{ohrm_name}.sql"
    if not init_file.exists():
        # Case-insensitive fallback search
        for f in sql_dir.iterdir():
            if f.name.lower() == f"initialise{ohrm_name.lower()}.sql":
                init_file = f
                break
        else:
            raise FileNotFoundError(
                f"No init script found for {ohrm_name} in {sql_dir}"
            )

    files: list[Path] = []
    _collect_includes(init_file, sql_dir, files, set())
    return files


def _collect_includes(
    script: Path,
    sql_dir: Path,
    files: list[Path],
    seen: set[Path],
) -> None:
    """Recursively collect SQL files referenced by \\i directives."""
    for line in script.read_text().splitlines():
        line = line.strip()
        if line.startswith("\\i "):
            filename = line[3:].strip()
            sql_file = sql_dir / filename
            if sql_file.exists() and sql_file not in seen:
                seen.add(sql_file)
                # If the included file itself contains \i directives,
                # resolve those recursively instead of adding it directly
                text = sql_file.read_text()
                has_includes = any(
                    l.strip().startswith("\\i ")
                    for l in text.splitlines()
                )
                if has_includes:
                    _collect_includes(sql_file, sql_dir, files, seen)
                else:
                    files.append(sql_file)


def _find_ohrm_subdir(ohrm_path: Path) -> Path:
    """Find the 'ohrm' subdirectory (case-insensitive)."""
    for entry in ohrm_path.iterdir():
        if entry.is_dir() and entry.name.lower() == "ohrm":
            return entry
    raise FileNotFoundError(f"No 'ohrm' subdirectory found in {ohrm_path}")


def _derive_ohrm_name(ohrm_path: Path) -> str:
    """Derive the OHRM name from the init script filename."""
    sql_dir = _find_ohrm_subdir(ohrm_path) / "web" / "sql"
    for f in sql_dir.iterdir():
        if f.name.lower().startswith("initialise") and f.name.endswith(".sql"):
            return f.stem[len("initialise"):]
    raise FileNotFoundError(f"No initialise*.sql found in {sql_dir}")


@contextmanager
def load_ohrm(ohrm_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Load an OHRM SQL dump into a temporary SQLite database."""
    ohrm_name = _derive_ohrm_name(ohrm_path)
    ohrm_subdir = _find_ohrm_subdir(ohrm_path)
    sql_dir = ohrm_subdir / "web" / "sql"
    sql_files = resolve_sql_files(sql_dir, ohrm_name)

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = Path(tmp.name)
    tmp.close()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row

        for sql_file in sql_files:
            raw_sql = sql_file.read_text(encoding="utf-8", errors="replace")
            cleaned = clean_sql(raw_sql)
            conn.executescript(cleaned)

        conn.commit()
        yield conn
    finally:
        conn.close()
        db_path.unlink(missing_ok=True)


def fetch_all[T: PydanticBaseModel](
    conn: sqlite3.Connection, table: str, model: type[T],
) -> list[T]:
    """Fetch all rows from a table and return as Pydantic model instances."""
    if table not in TABLES:
        raise ValueError(f"Unknown table: {table}")
    cursor = conn.execute(f"SELECT * FROM {table}")  # noqa: S608
    return [model(**dict(row)) for row in cursor.fetchall()]
