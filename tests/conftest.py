"""Shared test fixtures."""

from pathlib import Path

import pytest

ULSS_PATH = Path.home() / "Documents" / "rocrate_files" / "downloads" / "ULSS-ro-crate"


@pytest.fixture
def ulss_path():
    """Path to the ULSS test OHRM."""
    if not ULSS_PATH.exists():
        pytest.skip("ULSS test data not available")
    return ULSS_PATH
