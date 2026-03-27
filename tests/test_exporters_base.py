"""Tests for base exporter utilities."""
from ohrm_converter.exporters.base import extract_entity, map_properties
from ohrm_converter.models import Entity

class TestMapProperties:
    def test_maps_string_field_same_name(self):
        row = Entity(eid="E001", epub=1)
        entity: dict = {}
        map_properties(row, entity, {"epub": "epub"})
        assert entity["epub"] == 1

    def test_maps_renamed_field(self):
        row = Entity(eid="E001", ecountrycode="AU")
        entity: dict = {}
        map_properties(row, entity, {"ecountrycode": "countryCode"})
        assert entity["countryCode"] == "AU"

    def test_skips_none_values(self):
        row = Entity(eid="E001")
        entity: dict = {}
        map_properties(row, entity, {"ecountrycode": "countryCode"})
        assert "countryCode" not in entity

    def test_skips_empty_strings(self):
        row = Entity(eid="E001", ecountrycode="")
        entity: dict = {}
        map_properties(row, entity, {"ecountrycode": "countryCode"})
        assert "countryCode" not in entity

    def test_preserves_zero_values(self):
        row = Entity(eid="E001", erating=0.0)
        entity: dict = {}
        map_properties(row, entity, {"erating": "rating"})
        assert entity["rating"] == 0.0

class TestExtractEntity:
    def test_creates_stub_entity(self):
        result = extract_entity("Person", "John Smith")
        assert result["@id"] == "#John%20Smith"
        assert result["@type"] == "Person"
        assert result["name"] == "John Smith"

    def test_url_encodes_special_characters(self):
        result = extract_entity("Place", "St. Mary's")
        assert result["name"] == "St. Mary's"
