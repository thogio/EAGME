from __future__ import annotations

import argparse
from pathlib import Path

from extraction_reference_lib import read_json, write_markdown_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the shareable markdown report from scored page decisions."
    )
    parser.add_argument("--pdf", required=True, help="Path to input PDF.")
    parser.add_argument(
        "--output-dir",
        default="reference_benchmark_outputs",
        help="Output directory that already contains scored page decisions.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf)
    output_dir = Path(args.output_dir)
    scored_path = output_dir / f"{pdf_path.stem}_scored_pages.json"

    if not scored_path.exists():
        raise SystemExit(
            f"Missing scored page file: {scored_path}. "
            "Run score_extraction_reference.py first."
        )

    results = read_json(scored_path)
    write_markdown_report(results, output_dir)
    print(f"Wrote report: {output_dir / 'comparison_report.md'}")


if __name__ == "__main__":
    main()
