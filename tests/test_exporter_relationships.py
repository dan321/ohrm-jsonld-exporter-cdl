"""Tests for relationship exporters."""
from ohrm_converter.exporters.earrship import export_earrships
from ohrm_converter.exporters.edorship import export_edorships
from ohrm_converter.exporters.efrship import export_efrships
from ohrm_converter.exporters.relatedentity import export_relatedentities
from ohrm_converter.exporters.relatedresource import export_relatedresources
from ohrm_converter.models import EARRship, EDORship, EFRship, RelatedEntity, RelatedResource

class TestRelatedEntity:
    def test_basic_export(self):
        rows = [RelatedEntity(eid="E001", reid="E002", rerelationship="Successor of")]
        result = export_relatedentities(rows)
        main = [e for e in result if e.get("identifier") == "E001-E002"]
        assert len(main) == 1
        assert main[0]["@type"] == ["Relationship", "Successor_of"]
        assert main[0]["source"] == {"@id": "#E002"}
        assert main[0]["target"] == {"@id": "#E001"}

    def test_skips_missing_keys(self):
        rows = [RelatedEntity(eid="E001")]
        result = export_relatedentities(rows)
        assert len(result) == 0

class TestRelatedResource:
    def test_basic_export(self):
        rows = [RelatedResource(rrno=1, rid="A001", rrid="P001", rtype="References")]
        result = export_relatedresources(rows)
        assert len(result) == 1
        assert result[0]["source"] == {"@id": "#A001"}

    def test_skips_missing_keys(self):
        rows = [RelatedResource(rrno=1, rid="A001")]
        result = export_relatedresources(rows)
        assert len(result) == 0

class TestEARRship:
    def test_basic_export(self):
        rows = [EARRship(arcid="A001", eid="E001", relationship="Creator of")]
        result = export_earrships(rows)
        main = [e for e in result if e.get("identifier") == "A001-E001"]
        assert len(main) == 1
        assert main[0]["@type"] == ["Relationship", "Creator_of"]

    def test_skips_missing_keys(self):
        rows = [EARRship(arcid="A001")]
        result = export_earrships(rows)
        assert len(result) == 0

class TestEDORship:
    def test_basic_export(self):
        rows = [EDORship(doid="D001", eid="E001", relationship="Subject of")]
        result = export_edorships(rows)
        main = [e for e in result if e.get("identifier") == "D001-E001"]
        assert len(main) == 1
        assert main[0]["source"] == {"@id": "#D001"}

class TestEFRship:
    def test_basic_export(self):
        rows = [EFRship(eid="E001", fid="F001")]
        result = export_efrships(rows)
        main = [e for e in result if e.get("identifier") == "E001-F001"]
        assert len(main) == 1
        assert main[0]["@type"] == ["Relationship"]

    def test_extracts_place_state_country(self):
        rows = [EFRship(eid="E001", fid="F001", efplace="Melbourne", efplacestate="VIC", efplacecountry="Australia")]
        result = export_efrships(rows)
        places = [e for e in result if e.get("@type") == "Place"]
        states = [e for e in result if e.get("@type") == "State"]
        countries = [e for e in result if e.get("@type") == "Country"]
        assert len(places) == 1
        assert len(states) == 1
        assert len(countries) == 1
