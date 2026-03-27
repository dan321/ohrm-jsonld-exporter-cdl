"""Shared test fixtures."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def ulss_path():
    """Path to the ULSS test OHRM.

    Set the OHRM_TEST_DATA environment variable to the path of an OHRM
    directory (e.g. containing ULSS-ro-crate/). Skips if not set or missing.
    """
    raw = os.environ.get("OHRM_TEST_DATA")
    if not raw:
        pytest.skip("OHRM_TEST_DATA environment variable not set")
    path = Path(raw)
    if not path.exists():
        pytest.skip(f"OHRM_TEST_DATA path does not exist: {path}")
    return path
