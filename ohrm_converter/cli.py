"""CLI entry point for ohrm-converter."""
from __future__ import annotations
from pathlib import Path
import typer
from ohrm_converter.crate import build_crate
from ohrm_converter.loader import load_ohrm

app = typer.Typer(
    name="ohrm-converter",
    help="Convert OHRM database dumps to RO-Crate JSON-LD.",
)


def _discover_ohrms(directory: Path) -> list[Path]:
    """Find OHRM folders in a directory (contain an 'ohrm' subdirectory)."""
    ohrms = []
    for entry in sorted(directory.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith(".") or entry.name.startswith("$"):
            continue
        if entry.name.endswith(".zip"):
            continue
        for child in entry.iterdir():
            if child.is_dir() and child.name.lower() == "ohrm":
                ohrms.append(entry)
                break
    return ohrms


@app.command()
def main(
    input_dir: Path = typer.Argument(
        ...,
        help="Directory containing OHRM folders to convert.",
        exists=True,
        file_okay=False,
    ),
    output: Path = typer.Option(
        ...,
        "-o", "--output",
        help="Output directory for RO-Crate metadata files.",
    ),
) -> None:
    """Convert OHRM database dumps to RO-Crate JSON-LD."""
    ohrms = _discover_ohrms(input_dir)

    if not ohrms:
        typer.echo(f"No OHRM folders found in {input_dir}")
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(ohrms)} OHRM(s) to convert.")

    for ohrm_path in ohrms:
        ohrm_name = ohrm_path.name
        typer.echo(f"Converting {ohrm_name}...")
        output_dir = output / ohrm_name

        try:
            with load_ohrm(ohrm_path) as conn:
                build_crate(conn, output_dir)
            typer.echo(f"  -> {output_dir / 'ro-crate-metadata.json'}")
        except Exception as e:
            typer.echo(f"  ERROR: {e}", err=True)

    typer.echo("Done.")
