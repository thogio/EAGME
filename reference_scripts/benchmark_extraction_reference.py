from __future__ import annotations

import argparse
from pathlib import Path

from extraction_reference_lib import (
    ensure_dependencies,
    extract_page_candidates,
    parse_int_csv,
    score_page_bundle,
    safe_write_json,
    write_markdown_report,
    write_summary_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full reference extraction benchmark end-to-end."
    )
    parser.add_argument("--pdf", required=True, help="Path to input PDF.")
    parser.add_argument("--pages", required=True, help="Comma-separated human page numbers.")
    parser.add_argument(
        "--lang",
        default="ell+eng",
        help="Tesseract language string. Default: ell+eng",
    )
    parser.add_argument(
        "--expected-language",
        choices=["ell", "eng"],
        default="ell",
        help="Expected page language for readability scoring.",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=3,
        help="Render scale for page images. Default: 3",
    )
    parser.add_argument(
        "--psm-modes",
        default="3,4,6",
        help="Comma-separated Tesseract PSM modes. Default: 3,4,6",
    )
    parser.add_argument(
        "--output-dir",
        default="reference_benchmark_outputs",
        help="Output directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dependencies(check_ollama=True)

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    pages = parse_int_csv(args.pages, "Pages")
    psm_modes = parse_int_csv(args.psm_modes, "PSM modes")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for page_number in pages:
        page_bundle = extract_page_candidates(
            pdf_path=pdf_path,
            page_number=page_number,
            expected_language=args.expected_language,
            output_dir=output_dir,
            lang=args.lang,
            scale=args.scale,
            psm_modes=psm_modes,
        )
        results.append(score_page_bundle(page_bundle, output_dir))

    safe_write_json(output_dir / f"{pdf_path.stem}_scored_pages.json", results)
    write_summary_outputs(results, pdf_path, output_dir)
    write_markdown_report(results, output_dir)

    print(f"Wrote outputs under: {output_dir / pdf_path.stem}")
    print(f"Wrote summary: {output_dir / f'{pdf_path.stem}_summary.json'}")
    print(f"Wrote decisions: {output_dir / 'page_decisions.csv'}")
    print(f"Wrote report: {output_dir / 'comparison_report.md'}")


if __name__ == "__main__":
    main()
