from __future__ import annotations

import argparse
from pathlib import Path

from extraction_reference_lib import (
    find_candidate_bundles,
    read_json,
    score_page_bundle,
    safe_write_json,
    write_summary_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score extracted candidates and produce page-level decisions."
    )
    parser.add_argument("--pdf", required=True, help="Path to input PDF.")
    parser.add_argument(
        "--output-dir",
        default="reference_benchmark_outputs",
        help="Output directory that already contains candidate artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf)
    output_dir = Path(args.output_dir)
    bundle_paths = find_candidate_bundles(output_dir, pdf_path.stem)

    if not bundle_paths:
        raise SystemExit(
            f"No candidate bundles found for {pdf_path.stem} under {output_dir}. "
            "Run extract_candidates_reference.py first."
        )

    results = []
    for bundle_path in bundle_paths:
        page_bundle = read_json(bundle_path)
        results.append(score_page_bundle(page_bundle, output_dir))

    safe_write_json(output_dir / f"{pdf_path.stem}_scored_pages.json", results)
    write_summary_outputs(results, pdf_path, output_dir)
    print(f"Wrote page decisions under: {output_dir / pdf_path.stem}")
    print(f"Wrote summary: {output_dir / f'{pdf_path.stem}_summary.json'}")
    print(f"Wrote decisions: {output_dir / 'page_decisions.csv'}")


if __name__ == "__main__":
    main()
