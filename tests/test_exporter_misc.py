"""Tests for function, entityevent, entityname exporters."""
from ohrm_converter.exporters.entityevent import export_entityevents
from ohrm_converter.exporters.entityname import export_entitynames
from ohrm_converter.exporters.function import export_functions
from ohrm_converter.models import Entity, EntityEvent, EntityName, Function

class TestFunction:
    def test_basic_export(self):
        rows = [Function(fid="F001", fname="Records Management", fdescription="Desc")]
        result = export_functions(rows)
        assert len(result) == 1
        assert result[0]["@type"] == ["Function"]
        assert result[0]["name"] == "Records Management"

class TestEntityEvent:
    def test_inherits_entity_type(self):
        entities = [Entity(eid="E001", ename="X", etype="Person")]
        events = [EntityEvent(eid="E001", eetype="Birth", eedescription="Born")]
        result = export_entityevents(events, entities)
        main = [e for e in result if "@type" in e and "Birth" in e["@type"]]
        assert len(main) == 1
        assert main[0]["@type"] == ["Person", "Birth"]
        assert main[0]["entity"] == {"@id": "#E001"}

class TestEntityName:
    def test_basic_export(self):
        rows = [EntityName(eid="E001", enalternate="Alt", enalternatetype="Nickname")]
        result = export_entitynames(rows)
        main = [e for e in result if e.get("@id") == "#E001_alsoKnownAs"]
        assert len(main) == 1
        assert main[0]["@type"] == ["Nickname"]
        assert main[0]["alsoKnownAs"] == {"@id": "#E001"}
