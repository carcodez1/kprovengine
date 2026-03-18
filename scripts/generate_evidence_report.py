#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from kprovengine.reporting import write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate an interactive HTML evidence report from a JSON manifest."
    )
    parser.add_argument("manifest", help="Path to the evidence manifest JSON file.")
    parser.add_argument("--html-out", required=True, help="Output path for the generated HTML report.")
    parser.add_argument(
        "--archive-out",
        help="Optional output path for the enriched JSON archive used by the report.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    write_report(
        manifest_path=Path(args.manifest),
        html_output=Path(args.html_out),
        archive_output=Path(args.archive_out) if args.archive_out else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
