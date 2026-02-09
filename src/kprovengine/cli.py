from __future__ import annotations

from pathlib import Path

import click

from .pipeline import run_pipeline
from .types import RunInputs


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(prog_name="kprovengine")
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--out",
    "out_dir",
    type=click.Path(path_type=Path),
    default=Path("runs"),
    show_default=True,
    help="Base output directory (a per-run subdir will be created).",
)
@click.option(
    "--evidence/--no-evidence",
    default=True,
    show_default=True,
    help="Record evidence mode in outputs (bundle generation is incremental in V1).",
)
def main(source: Path, out_dir: Path, evidence: bool) -> int:
    """
    KProvEngine CLI (V1 scaffold).

    V1 notes:
      - Local-first execution only.
      - OCR/LLM adapters are optional and not implied by this command.
      - Evidence here records intent/state; bundle contents remain a V1 incremental surface.
    """
    res = run_pipeline(
        RunInputs(
            sources=[source],
            output_dir=out_dir,
            evidence="ENABLED" if evidence else "DISABLED",
        )
    )

    click.echo(f"run_id={res.run_id}")
    click.echo(f"run_dir={res.run_dir}")
    click.echo("outputs:")
    for p in res.outputs:
        click.echo(f"  - {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())