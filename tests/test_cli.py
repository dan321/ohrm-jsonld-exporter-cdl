"""Tests for CLI."""
from typer.testing import CliRunner
from ohrm_converter.cli import app

runner = CliRunner()


class TestCli:
    def test_no_ohrms_found(self, tmp_path):
        result = runner.invoke(app, [str(tmp_path), "-o", str(tmp_path / "out")])
        assert result.exit_code == 1
        assert "No OHRM folders found" in result.output

    def test_converts_ohrm(self, tmp_path):
        # Create a minimal OHRM structure
        ohrm_dir = tmp_path / "input" / "TEST-ohrm"
        sql_dir = ohrm_dir / "ohrm" / "web" / "sql"
        sql_dir.mkdir(parents=True)
        (sql_dir / "createOHRM.sql").write_text(
            "CREATE TABLE entity (eid varchar(7) NOT NULL, ename varchar(255));\n"
            "CREATE TABLE html (title varchar(50), creator varchar(100), description text);\n"
            "CREATE TABLE htmlmetadata (name varchar(255), scheme varchar(50), lang varchar(50), content varchar(255), x_ref varchar(255));\n"
            "CREATE TABLE entityevent (eid varchar(7));\n"
            "CREATE TABLE entityname (eid varchar(7));\n"
            "CREATE TABLE arcresource (arcid varchar(9) NOT NULL);\n"
            "CREATE TABLE dobject (doid varchar(9) NOT NULL);\n"
            "CREATE TABLE dobjectversion (doid varchar(9));\n"
            "CREATE TABLE pubresource (pubid varchar(9) NOT NULL);\n"
            "CREATE TABLE function (fid varchar(8) NOT NULL);\n"
            "CREATE TABLE earrship (arcid varchar(9), eid varchar(7));\n"
            "CREATE TABLE edorship (doid varchar(9), eid varchar(7));\n"
            "CREATE TABLE efrship (eid varchar(7), fid varchar(50));\n"
            "CREATE TABLE relatedentity (eid varchar(7));\n"
            "CREATE TABLE relatedresource (rrno INTEGER NOT NULL);\n"
            "CREATE TABLE eprrship (eid varchar(7), pubid varchar(9));\n"
            "CREATE TABLE prreprship (pubid varchar(9), repid varchar(20));\n"
            "CREATE TABLE repository (repid varchar(255));\n"
        )
        (sql_dir / "updateTEST.sql").write_text(
            "INSERT INTO entity (eid, ename) VALUES ('E001', 'Test Entity');\n"
            "INSERT INTO html (title, creator) VALUES ('Test OHRM', 'Test Creator');\n"
        )
        (sql_dir / "initialiseTEST.sql").write_text(
            "\\i createOHRM.sql\n\\i updateTEST.sql\n"
        )

        output_dir = tmp_path / "output"
        result = runner.invoke(app, [str(tmp_path / "input"), "-o", str(output_dir)])
        assert result.exit_code == 0
        assert "Converting TEST-ohrm" in result.output
        assert (output_dir / "TEST-ohrm" / "ro-crate-metadata.json").exists()
