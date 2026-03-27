"""Tests for the entity exporter."""
from ohrm_converter.exporters.entity import export_entities
from ohrm_converter.models import Entity, EntityEvent, EntityName


class TestExportEntities:
    def test_basic_entity_export(self):
        entities_in = [Entity(eid="E001", ename="Test Org", etype="Organisation-Government")]
        result = export_entities(entities_in, [], [])
        main = [e for e in result if e.get("identifier") == "E001"]
        assert len(main) == 1
        assert main[0]["@id"] == "#E001"
        assert main[0]["@type"] == ["Organisation", "Government"]
        assert main[0]["name"] == "Test Org"

    def test_extracts_person_entity(self):
        entities_in = [Entity(eid="E001", ename="Test", etype="Person", eprepared="John Smith")]
        result = export_entities(entities_in, [], [])
        persons = [e for e in result if e.get("@type") == "Person"]
        assert len(persons) == 1
        assert persons[0]["name"] == "John Smith"
        main = [e for e in result if e.get("identifier") == "E001"][0]
        assert main["preparedBy"] == {"@id": "#John%20Smith"}

    def test_links_also_known_as(self):
        entities_in = [Entity(eid="E001", ename="Test", etype="Person")]
        names = [EntityName(eid="E001", enalternate="Alt Name", enalternatetype="Nickname")]
        result = export_entities(entities_in, [], names)
        main = [e for e in result if e.get("identifier") == "E001"][0]
        assert main["alsoKnownAs"] == [{"@id": "#E001_alsoKnownAs"}]

    def test_links_related_events(self):
        entities_in = [Entity(eid="E001", ename="Test", etype="Person")]
        events = [EntityEvent(eid="E001", eetype="Birth")]
        result = export_entities(entities_in, events, [])
        main = [e for e in result if e.get("identifier") == "E001"][0]
        assert main["relatedEvents"] == [{"@id": "#E001_event"}]

    def test_type_splitting(self):
        entities_in = [Entity(eid="E001", ename="Test", etype="Organisation - Local Government")]
        result = export_entities(entities_in, [], [])
        main = [e for e in result if e.get("identifier") == "E001"][0]
        assert main["@type"] == ["Organisation", "Local_Government"]
