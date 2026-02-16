from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from .pipeline import run_pipeline
from .types import RunInputs

# ----- Deterministic exit codes (POSIX-ish) -----
EX_OK = 0
EX_USAGE = 64        # command line usage error
EX_DATAERR = 65      # input data incorrect / missing input
EX_SOFTWARE = 70     # internal software error
EX_IOERR = 74        # I/O error


@dataclass(frozen=True)
class CliResult:
    run_id: str
    run_dir: str
    outputs: list[str]
    evidence: bool


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _canon_existing_file(p: Path) -> Path:
    cp = p.expanduser().resolve(strict=True)
    if not cp.is_file():
        raise ValueError(f"source must be a file: {cp}")
    return cp


def _canon_out_dir(p: Path) -> Path:
    pp = p.expanduser()
    if not pp.is_absolute():
        pp = Path.cwd() / pp
    parent = pp.parent.resolve(strict=True)
    return parent / pp.name


def _sorted_str_paths(paths: Iterable[object]) -> list[str]:
    out: list[str] = []
    for x in paths:
        try:
            out.append(str(Path(x)))  # type: ignore[arg-type]
        except Exception:
            out.append(str(x))
    return sorted(out)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kprovengine",
        description="kprovengine CLI (V1).",
        add_help=True,
    )

    parser.add_argument(
        "source",
        help="Input source file path.",
    )
    parser.add_argument(
        "--out",
        default="runs",
        help="Base output directory (a per-run subdir will be created). Default: runs",
    )
    parser.add_argument(
        "--evidence",
        dest="evidence",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Record evidence mode in outputs (bundle generation remains incremental in V1).",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=("json", "text"),
        default="json",
        help="Output format. json is stable for automation. Default: json",
    )
    # Keep version simple and stdlib-only. If you want real package version,
    # read from importlib.metadata in py>=3.8 (still stdlib), but keep it stable.
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Contract:
      - Deterministic exit codes.
      - Stable JSON schema when --format=json.
      - Errors are prefixed with 'error:' and written to stderr.
      - All exceptions are handled at the CLI boundary.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()

    try:
        ns = parser.parse_args(argv)

        if ns.version:
            # V1: conservative fixed string. If you want dynamic:
            # from importlib.metadata import version; print(version("kprovengine"))
            print("kprovengine (V1)")
            return EX_OK

        src = _canon_existing_file(Path(ns.source))
        out_base = _canon_out_dir(Path(ns.out))
        evidence = bool(ns.evidence)
        fmt = str(ns.fmt).lower()

        # Preserve existing V1 pipeline contract: evidence as marker string.
        res = run_pipeline(
            RunInputs(
                sources=[src],
                output_dir=out_base,
                evidence="ENABLED" if evidence else "DISABLED",
            )
        )

        outputs = _sorted_str_paths(getattr(res, "outputs", []))
        run_dir = str(Path(getattr(res, "run_dir", "")).expanduser().resolve(strict=False))
        run_id = str(getattr(res, "run_id", ""))

        cli_res = CliResult(
            run_id=run_id,
            run_dir=run_dir,
            outputs=outputs,
            evidence=evidence,
        )

        if fmt == "json":
            print(json.dumps(asdict(cli_res), indent=2, sort_keys=True))
        else:
            print(f"run_id={cli_res.run_id}")
            print(f"run_dir={cli_res.run_dir}")
            print(f"evidence={'ENABLED' if cli_res.evidence else 'DISABLED'}")
            print("outputs:")
            for p in cli_res.outputs:
                print(f"  - {p}")

        return EX_OK

    except SystemExit as e:
        # argparse uses SystemExit for -h and parsing errors.
        code = int(getattr(e, "code", 0) or 0)
        if code == 0:
            return EX_OK
        return EX_USAGE

    except ValueError as e:
        _eprint(f"error: {e}")
        return EX_USAGE

    except FileNotFoundError as e:
        _eprint(f"error: {e}")
        return EX_DATAERR

    except OSError as e:
        _eprint(f"error: {e}")
        return EX_IOERR

    except Exception as e:
        _eprint(f"error: {type(e).__name__}: {e}")
        return EX_SOFTWARE


if __name__ == "__main__":
    sys.exit(main())
