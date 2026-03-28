"""CLI entry point for ohrm-converter."""
from __future__ import annotations
from pathlib import Path
import shutil
import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from ohrm_converter.crate import build_crate
from ohrm_converter.loader import load_ohrm

app = typer.Typer(
    name="ohrm-converter",
    help="Convert OHRM database dumps to RO-Crate JSON-LD.",
)

console = Console()


def _progress_label(idx: int, total: int, ohrm_name: str) -> Text:
    """Build a width-stable progress label for live and final output."""
    counter_width = len(str(total))
    return Text.assemble(
        (f"[{idx:>{counter_width}}/{total}]", "dim"),
        " ",
        ohrm_name,
    )


def _status_line(
    symbol: str,
    symbol_style: str,
    idx: int,
    total: int,
    ohrm_name: str,
    detail: str | None = None,
) -> Text:
    """Build a completed/error line with the same alignment as the spinner."""
    line = Text.assemble((symbol, symbol_style), " ", _progress_label(idx, total, ohrm_name))
    if detail:
        line.append(" ")
        line.append(detail, style="dim")
    return line


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
    full_crate: bool = typer.Option(
        False,
        "--full-crate",
        help="Copy source files into the output, producing a complete RO-Crate.",
    ),
) -> None:
    """Convert OHRM database dumps to RO-Crate JSON-LD."""
    ohrms = _discover_ohrms(input_dir)

    if not ohrms:
        console.print(f"[red]No OHRM folders found in {input_dir}[/red]")
        raise typer.Exit(code=1)

    total = len(ohrms)
    console.print(f"Found [bold]{total}[/bold] OHRM(s) to convert.\n")

    results: list[tuple[str, str, str]] = []

    with Live(console=console, refresh_per_second=10) as live:
        for idx, ohrm_path in enumerate(ohrms, 1):
            ohrm_name = ohrm_path.name
            output_dir = output / ohrm_name

            label = _progress_label(idx, total, ohrm_name)
            label.append("\n\n")
            live.update(Spinner("dots", text=label))

            try:
                if full_crate:
                    shutil.copytree(ohrm_path, output_dir, dirs_exist_ok=True)
                with load_ohrm(ohrm_path) as conn:
                    build_crate(conn, output_dir)
                live.update(Text(""))
                console.print(_status_line("\u2713", "green", idx, total, ohrm_name))
                output_detail = str(output_dir) if full_crate else str(output_dir / "ro-crate-metadata.json")
                results.append((ohrm_name, "ok", output_detail))
            except Exception as e:
                live.update(Text(""))
                console.print(_status_line("\u2717", "red", idx, total, ohrm_name, f"\u2014 {e}"))
                results.append((ohrm_name, "error", str(e)))

    # Summary table
    console.print()
    table = Table(title="Conversion Summary")
    table.add_column("OHRM", style="bold")
    table.add_column("Status")
    table.add_column("Output")

    ok_count = 0
    for name, status, detail in results:
        if status == "ok":
            ok_count += 1
            table.add_row(name, "[green]ok[/green]", detail)
        else:
            table.add_row(name, "[red]error[/red]", f"[dim]{detail}[/dim]")

    console.print(table)

    fail_count = len(results) - ok_count
    if fail_count:
        console.print(f"\n[green]{ok_count} succeeded[/green], [red]{fail_count} failed[/red]")
    else:
        console.print(f"\n[green]All {ok_count} converted successfully.[/green]")
