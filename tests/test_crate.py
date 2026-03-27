"""Tests for RO-Crate assembly."""

import json

from ohrm_converter.crate import build_crate
from ohrm_converter.loader import load_ohrm


class TestBuildCrate:
    def test_produces_valid_json_ld(self, tmp_path, ulss_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with load_ohrm(ulss_path) as conn:
            build_crate(conn, output_dir)

        metadata_file = output_dir / "ro-crate-metadata.json"
        assert metadata_file.exists()

        with open(metadata_file) as f:
            crate = json.load(f)

        assert "@context" in crate
        assert "@graph" in crate
        assert len(crate["@graph"]) > 1

    def test_root_dataset_has_metadata(self, tmp_path, ulss_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with load_ohrm(ulss_path) as conn:
            build_crate(conn, output_dir)

        with open(output_dir / "ro-crate-metadata.json") as f:
            crate = json.load(f)

        root = None
        for item in crate["@graph"]:
            if item.get("@id") == "./":
                root = item
                break

        assert root is not None
        assert "title" in root or "name" in root

    def test_contains_entities(self, tmp_path, ulss_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with load_ohrm(ulss_path) as conn:
            build_crate(conn, output_dir)

        with open(output_dir / "ro-crate-metadata.json") as f:
            crate = json.load(f)

        types_present = set()
        for item in crate["@graph"]:
            item_type = item.get("@type", [])
            if isinstance(item_type, str):
                types_present.add(item_type)
            elif isinstance(item_type, list):
                types_present.update(item_type)

        assert "Person" in types_present or "Function" in types_present
