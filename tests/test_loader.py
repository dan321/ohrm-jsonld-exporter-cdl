"""Tests for the SQL loader."""

from pathlib import Path

import pytest

from ohrm_converter.loader import clean_sql, load_ohrm, resolve_sql_files


class TestCleanSql:
    def test_strips_backslash_i_directives(self):
        sql = "\\i createOHRM.sql\n\\i updateULSS.sql\n"
        result = clean_sql(sql)
        assert "\\i" not in result

    def test_converts_escaped_string_syntax(self):
        sql = "INSERT INTO CATEGORY (name) VALUES (E'Full\\-time');"
        result = clean_sql(sql)
        assert "E'" not in result
        assert "'Full-time'" in result

    def test_normalises_int8_type(self):
        sql = "CREATE TABLE test (id int8 NOT NULL);"
        result = clean_sql(sql)
        assert "INTEGER" in result
        assert "int8" not in result

    def test_normalises_float8_type(self):
        sql = "CREATE TABLE test (val float8);"
        result = clean_sql(sql)
        assert "REAL" in result
        assert "float8" not in result

    def test_normalises_boolean_type(self):
        sql = "CREATE TABLE test (flag boolean);"
        result = clean_sql(sql)
        assert "INTEGER" in result
        assert "boolean" not in result

    def test_converts_boolean_values(self):
        sql = "INSERT INTO test (flag) VALUES ('True');"
        result = clean_sql(sql)
        assert result.strip() == "INSERT INTO test (flag) VALUES (1);"

    def test_converts_false_values(self):
        sql = "INSERT INTO test (flag) VALUES ('False');"
        result = clean_sql(sql)
        assert result.strip() == "INSERT INTO test (flag) VALUES (0);"

    def test_handles_drop_table(self):
        sql = "DROP TABLE entity;"
        result = clean_sql(sql)
        assert "DROP TABLE IF EXISTS entity;" in result

    def test_preserves_normal_sql(self):
        sql = "INSERT INTO entity (eid, ename) VALUES ('E001', 'Test');"
        result = clean_sql(sql)
        assert "INSERT INTO entity (eid, ename) VALUES ('E001', 'Test');" in result


class TestResolveSqlFiles:
    def test_resolves_init_script_includes(self, tmp_path):
        sql_dir = tmp_path / "sql"
        sql_dir.mkdir()
        (sql_dir / "createOHRM.sql").write_text(
            "CREATE TABLE entity (eid varchar(7));"
        )
        (sql_dir / "updateULSS.sql").write_text(
            "INSERT INTO entity (eid) VALUES ('E001');"
        )
        (sql_dir / "initialiseULSS.sql").write_text(
            "\\i createOHRM.sql\n\\i updateULSS.sql\n"
        )

        files = resolve_sql_files(sql_dir, "ULSS")
        assert len(files) == 2
        assert files[0].name == "createOHRM.sql"
        assert files[1].name == "updateULSS.sql"


class TestLoadOhrm:
    def test_loads_ohrm_into_sqlite(self, tmp_path):
        ohrm_dir = tmp_path / "TEST"
        sql_dir = ohrm_dir / "ohrm" / "web" / "sql"
        sql_dir.mkdir(parents=True)
        (sql_dir / "createOHRM.sql").write_text(
            "CREATE TABLE entity (eid varchar(7) NOT NULL, ename varchar(255));"
        )
        (sql_dir / "updateTEST.sql").write_text(
            "INSERT INTO entity (eid, ename) VALUES ('E001', 'Test Entity');"
        )
        (sql_dir / "initialiseTEST.sql").write_text(
            "\\i createOHRM.sql\n\\i updateTEST.sql\n"
        )

        with load_ohrm(ohrm_dir) as conn:
            cursor = conn.execute("SELECT eid, ename FROM entity")
            rows = cursor.fetchall()
            assert len(rows) == 1
            assert rows[0]["eid"] == "E001"
            assert rows[0]["ename"] == "Test Entity"

    def test_temp_db_is_cleaned_up(self, tmp_path):
        ohrm_dir = tmp_path / "TEST"
        sql_dir = ohrm_dir / "ohrm" / "web" / "sql"
        sql_dir.mkdir(parents=True)
        (sql_dir / "createOHRM.sql").write_text(
            "CREATE TABLE entity (eid varchar(7));"
        )
        (sql_dir / "updateTEST.sql").write_text("")
        (sql_dir / "initialiseTEST.sql").write_text(
            "\\i createOHRM.sql\n\\i updateTEST.sql\n"
        )

        db_path = None
        with load_ohrm(ohrm_dir) as conn:
            cursor = conn.execute("PRAGMA database_list")
            db_path = Path(cursor.fetchone()["file"])
            assert db_path.exists()

        assert not db_path.exists()


class TestLoadUlss:
    def test_loads_ulss_ohrm(self, ulss_path):
        with load_ohrm(ulss_path) as conn:
            # Tables known to have data in the ULSS dump
            tables = {"entity", "category", "function", "pubresource", "entityname"}
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                count = cursor.fetchone()["cnt"]
                assert count > 0, f"Table {table} is empty"
