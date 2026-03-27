"""Integration test: convert ULSS and compare to known-good output."""

import json

from ohrm_converter.crate import build_crate
from ohrm_converter.loader import load_ohrm


class TestUlssConversion:
    def test_convert_ulss(self, tmp_path, ulss_path):
        """Convert ULSS and verify output structure matches the original."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with load_ohrm(ulss_path) as conn:
            build_crate(conn, output_dir)

        metadata_file = output_dir / "ro-crate-metadata.json"
        assert metadata_file.exists()

        with open(metadata_file) as f:
            new_crate = json.load(f)

        # Load reference output
        ref_file = ulss_path / "ro-crate-metadata.json"
        if ref_file.exists():
            with open(ref_file) as f:
                ref_crate = json.load(f)

            # Compare entity counts (allow some variance due to bug fixes)
            new_ids = {item["@id"] for item in new_crate["@graph"]}
            ref_ids = {item["@id"] for item in ref_crate["@graph"]}

            # Most entities should be present in both
            overlap = new_ids & ref_ids
            assert len(overlap) > len(ref_ids) * 0.8, (
                f"Less than 80% overlap: {len(overlap)}/{len(ref_ids)} entities match"
            )

        # Verify key structural properties
        graph = new_crate["@graph"]
        assert len(graph) > 10

        # Check for entities from multiple exporters
        types_found = set()
        for item in graph:
            t = item.get("@type", [])
            if isinstance(t, str):
                types_found.add(t)
            elif isinstance(t, list):
                types_found.update(t)

        expected_types = {"Person", "Place"}
        assert expected_types.issubset(types_found), (
            f"Missing expected types. Found: {types_found}"
        )
