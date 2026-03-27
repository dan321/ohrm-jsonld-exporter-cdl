#!/usr/bin/env python3
"""Batch test: unzip, convert, and compare OHRM crates against reference output.

Usage:
    python scripts/batch_test.py /path/to/downloads/

The downloads directory should contain *-ro-crate.zip files (and optionally
already-unzipped *-ro-crate/ folders). The script will:

1. Unzip any .zip files that don't already have a matching directory
2. Run ohrm-converter on all discovered OHRM folders
3. Compare each output against the reference ro-crate-metadata.json (if present)
4. Print a summary table and flag any failures

Converted output goes to a temporary directory and is cleaned up afterwards
unless --keep-output is passed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ComparisonResult:
    name: str
    status: str
    new_count: int = 0
    ref_count: int = 0
    overlap: int = 0
    real_missing: int = 0
    new_only: int = 0
    error: str | None = None


def unzip_crates(downloads_dir: Path, work_dir: Path) -> list[Path]:
    """Unzip *-ro-crate.zip files into work_dir and return all OHRM folders."""
    for zip_path in sorted(downloads_dir.glob("*-ro-crate.zip")):
        folder_name = zip_path.stem  # e.g. "AHPI-ro-crate"
        target = work_dir / folder_name

        # Skip if already unzipped in work_dir
        if target.exists():
            continue

        # Check if already unzipped in downloads_dir
        existing = downloads_dir / folder_name
        if existing.is_dir() and (existing / "ohrm").exists():
            # Symlink instead of copying
            target.symlink_to(existing)
            continue

        # Unzip using system command (handles edge cases better than Python zipfile)
        target.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["unzip", "-qo", str(zip_path), "-d", str(target)],
            capture_output=True, text=True,
        )
        if result.returncode not in (0, 1):  # unzip returns 1 for warnings
            print(f"  WARNING: Failed to unzip {zip_path.name}: {result.stderr.strip()}", file=sys.stderr)
            shutil.rmtree(target, ignore_errors=True)
            continue

    # Also symlink any already-unzipped folders from downloads_dir
    for folder in sorted(downloads_dir.iterdir()):
        if not folder.is_dir() or not folder.name.endswith("-ro-crate"):
            continue
        target = work_dir / folder.name
        if not target.exists():
            has_ohrm = any(
                child.is_dir() and child.name.lower() == "ohrm"
                for child in folder.iterdir()
            )
            if has_ohrm:
                target.symlink_to(folder)

    # Return all valid OHRM folders in work_dir
    ohrms = []
    for folder in sorted(work_dir.iterdir()):
        if not folder.is_dir():
            continue
        has_ohrm = any(
            child.is_dir() and child.name.lower() == "ohrm"
            for child in folder.iterdir()
        )
        if has_ohrm:
            ohrms.append(folder)
    return ohrms


def run_converter(work_dir: Path, output_dir: Path) -> dict[str, str | None]:
    """Run ohrm-converter on the work directory. Returns {name: error_or_none}."""
    venv_converter = Path(__file__).parent.parent / ".venv" / "bin" / "ohrm-converter"
    cmd = str(venv_converter) if venv_converter.exists() else "ohrm-converter"
    result = subprocess.run(
        [cmd, str(work_dir), "-o", str(output_dir)],
        capture_output=True,
        text=True,
    )

    # Parse output to find errors
    statuses: dict[str, str | None] = {}
    current_name = None
    for line in result.stdout.splitlines():
        if line.startswith("Converting "):
            current_name = line.removeprefix("Converting ").rstrip(".")
        elif line.strip().startswith("ERROR:") and current_name:
            statuses[current_name] = line.strip().removeprefix("ERROR: ")
        elif line.strip().startswith("->") and current_name:
            statuses[current_name] = None

    if result.returncode != 0 and not statuses:
        print(f"Converter failed: {result.stderr}", file=sys.stderr)

    return statuses


def compare_output(
    ohrm_dir: Path, output_dir: Path, name: str,
) -> ComparisonResult:
    """Compare converter output against reference for a single OHRM."""
    new_file = output_dir / name / "ro-crate-metadata.json"

    if not new_file.exists():
        return ComparisonResult(name=name, status="NO OUTPUT")

    with open(new_file) as f:
        new_crate = json.load(f)
    new_count = len(new_crate["@graph"])

    ref_file = ohrm_dir / "ro-crate-metadata.json"
    if not ref_file.exists():
        return ComparisonResult(name=name, status="NO REF", new_count=new_count)

    with open(ref_file) as f:
        ref_crate = json.load(f)

    ref_ids = {item["@id"] for item in ref_crate["@graph"]}
    new_ids = {item["@id"] for item in new_crate["@graph"]}
    overlap = ref_ids & new_ids
    ref_only = ref_ids - new_ids

    # Packaging entities (added by rochtml, not our exporters)
    packaging = {
        eid for eid in ref_only
        if not eid.startswith("#") and eid not in ("./", "ro-crate-metadata.json")
    }
    real_missing = ref_only - packaging
    new_only = new_ids - ref_ids

    return ComparisonResult(
        name=name,
        status="OK",
        new_count=new_count,
        ref_count=len(ref_crate["@graph"]),
        overlap=len(overlap),
        real_missing=len(real_missing),
        new_only=len(new_only),
    )


def print_summary(results: list[ComparisonResult]) -> int:
    """Print summary table and return exit code (1 if any failures)."""
    print()
    print(f"{'OHRM':<25} {'Status':<12} {'New':>6} {'Ref':>6} {'Match':>8} {'Miss':>5} {'Extra':>6}")
    print("-" * 72)

    failures = 0
    for r in results:
        if r.status == "OK":
            pct = f"{r.overlap / r.ref_count * 100:.0f}%" if r.ref_count else "n/a"
            miss_flag = " !!!" if r.real_missing > 0 else ""
            print(
                f"{r.name:<25} {r.status:<12} {r.new_count:>6} {r.ref_count:>6}"
                f" {r.overlap:>5} ({pct:>4}) {r.real_missing:>5}{miss_flag} {r.new_only:>5}"
            )
            if r.real_missing > 0:
                failures += 1
        elif r.status == "ERROR":
            print(f"{r.name:<25} {'ERROR':<12} {r.error}")
            failures += 1
        elif r.status == "NO REF":
            print(f"{r.name:<25} {'NO REF':<12} {r.new_count:>6}   (no reference file to compare)")
        else:
            print(f"{r.name:<25} {r.status:<12}")
            failures += 1

    total = len(results)
    ok = sum(1 for r in results if r.status in ("OK", "NO REF"))
    errored = sum(1 for r in results if r.status == "ERROR")
    no_output = sum(1 for r in results if r.status == "NO OUTPUT")

    print()
    print(f"Total: {total}  |  OK: {ok}  |  Errors: {errored}  |  No output: {no_output}")

    if failures:
        print(f"\n{failures} failure(s) detected.")
        return 1

    print("\nAll conversions successful.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch test OHRM converter against reference output.",
    )
    parser.add_argument(
        "downloads_dir",
        type=Path,
        help="Directory containing *-ro-crate.zip files and/or unzipped folders",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Keep the temporary output directory after completion",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Custom output directory (implies --keep-output)",
    )
    args = parser.parse_args()

    downloads_dir = args.downloads_dir.expanduser().resolve()
    if not downloads_dir.is_dir():
        print(f"Error: {downloads_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Set up working directories
    work_tmp = tempfile.mkdtemp(prefix="ohrm-batch-work-")
    work_dir = Path(work_tmp)

    if args.output_dir:
        output_dir = args.output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        keep_output = True
    else:
        output_tmp = tempfile.mkdtemp(prefix="ohrm-batch-output-")
        output_dir = Path(output_tmp)
        keep_output = args.keep_output

    try:
        # Step 1: Unzip
        print(f"Discovering and unzipping OHRMs from {downloads_dir}...")
        ohrms = unzip_crates(downloads_dir, work_dir)
        print(f"Found {len(ohrms)} OHRM(s).")

        if not ohrms:
            print("Nothing to convert.")
            sys.exit(0)

        # Step 2: Convert
        print(f"\nRunning ohrm-converter...")
        statuses = run_converter(work_dir, output_dir)

        # Step 3: Compare
        print("\nComparing output against reference files...")
        results: list[ComparisonResult] = []
        for ohrm_path in ohrms:
            name = ohrm_path.name
            if name in statuses and statuses[name] is not None:
                results.append(ComparisonResult(
                    name=name, status="ERROR", error=statuses[name],
                ))
            else:
                results.append(compare_output(ohrm_path, output_dir, name))

        # Step 4: Summary
        exit_code = print_summary(results)

        if keep_output:
            print(f"\nOutput preserved at: {output_dir}")

        sys.exit(exit_code)

    finally:
        # Cleanup work dir (just symlinks and unzipped copies)
        shutil.rmtree(work_dir, ignore_errors=True)
        if not keep_output:
            shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
