from __future__ import annotations

import json
import re
import shutil
import statistics
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path

import cv2
import fitz
import pandas as pd
import pytesseract
from PIL import Image

try:
    import numpy as np
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "numpy is required for the reference extraction scripts. "
        "Install it with: python3 -m pip install numpy"
    ) from exc


GREEK_CHARS_RE = re.compile(r"[Α-Ωα-ωΆΈΉΊΌΎΏάέήίόύώϊΐϋΰΪΫἀ-῾]")
LATIN_CHARS_RE = re.compile(r"[A-Za-z]")

GREEK_SIGNAL_WORDS = {
    "και",
    "καί",
    "της",
    "τής",
    "των",
    "τών",
    "του",
    "τού",
    "τον",
    "τόν",
    "την",
    "τήν",
    "εις",
    "είς",
    "επι",
    "επί",
    "απο",
    "από",
    "δια",
    "διά",
    "με",
    "μετά",
    "κατα",
    "κατά",
    "προς",
    "πρός",
    "ως",
    "ώς",
    "υδατος",
    "ύδατος",
    "νερου",
    "νερού",
    "πηγων",
    "πηγών",
    "σηραγγος",
    "σήραγγος",
    "γεωλογιας",
    "γεωλογίας",
    "υπεδαφους",
    "υπεδάφους",
    "σχιστολιθοι",
    "σχιστόλιθοι",
    "υδροχημικη",
    "υδροχημικής",
    "αναλυσεις",
    "αναλύσεις",
    "υδροληψιας",
    "υδροληψίας",
}

ENGLISH_SIGNAL_WORDS = {
    "the",
    "and",
    "of",
    "in",
    "to",
    "for",
    "with",
    "were",
    "was",
    "data",
    "survey",
    "surveys",
    "geological",
    "geophysical",
    "equipment",
    "fieldwork",
    "crete",
    "santorini",
    "thera",
    "report",
    "page",
}

NOISE_TOKENS = [
    "#####",
    "####",
    "^",
    "|",
    "￾",
    "�",
    "□",
    "■",
    "●",
    "♦",
    "▯",
    "sso^",
    "l-t/γ",
    "σοο",
    "aeknawkdggxagxiis",
]

MIN_CONTENT_WORDS = 90
MIN_CONTENT_CHARS = 600


def safe_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def safe_write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def preview_text(text: str, max_chars: int = 700) -> str:
    if not text:
        return "[EMPTY]"
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars] + "..."


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def strip_accents(text: str) -> str:
    text = normalize_unicode(text)
    decomposed = unicodedata.normalize("NFD", text)
    no_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", no_marks)


def normalize_for_search(text: str) -> str:
    text = normalize_unicode(text)
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip().lower()


def words(text: str) -> list[str]:
    return re.findall(r"[\wΆΈΉΊΌΎΏάέήίόύώϊΐϋΰΪΫἀ-῾]+", text or "", flags=re.UNICODE)


def count_chars(regex: re.Pattern[str], text: str) -> int:
    return len(regex.findall(text or ""))


def has_digit_inside_word(token: str) -> bool:
    return bool(re.search(r"[A-Za-zΑ-Ωα-ω][0-9]|[0-9][A-Za-zΑ-Ωα-ω]", token))


def parse_int_csv(raw: str, label: str) -> list[int]:
    try:
        values = [int(value.strip()) for value in raw.split(",") if value.strip()]
    except ValueError as exc:
        raise SystemExit(f"{label} must be a comma-separated list of integers.") from exc
    if not values:
        raise SystemExit(f"At least one {label.lower()} value is required.")
    return values


def ensure_dependencies(check_ollama: bool = False) -> None:
    if shutil.which("tesseract") is None:
        raise SystemExit("tesseract not found in PATH")

    if check_ollama and shutil.which("ollama") is not None:
        subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)


def extract_with_pymupdf(page: fitz.Page) -> str:
    return page.get_text("text") or ""


def extract_with_pymupdf4llm(pdf_path: Path, page_number_human: int) -> str:
    try:
        import pymupdf4llm
    except Exception:
        return ""

    try:
        return pymupdf4llm.to_markdown(str(pdf_path), pages=[page_number_human - 1]) or ""
    except Exception:
        return ""


def get_tesseract_confidence(image_path: Path, lang: str, psm: int) -> float | None:
    try:
        data = pytesseract.image_to_data(
            Image.open(image_path),
            lang=lang,
            config=f"--oem 1 --psm {psm}",
            output_type=pytesseract.Output.DICT,
        )
    except Exception:
        return None

    confs = []
    for value in data.get("conf", []):
        try:
            conf = float(value)
        except Exception:
            continue
        if conf >= 0:
            confs.append(conf)

    if not confs:
        return None
    return round(statistics.mean(confs), 2)


def estimate_metrics(
    text: str,
    expected_language: str,
    ocr_confidence: float | None = None,
) -> dict:
    text = normalize_unicode(text)
    token_list = words(text)
    token_count = len(token_list)
    char_count = len(text)

    greek_chars = count_chars(GREEK_CHARS_RE, text)
    latin_chars = count_chars(LATIN_CHARS_RE, text)

    stripped = strip_accents(text).lower()
    stripped_tokens = [strip_accents(token).lower() for token in token_list]

    noise_token_count = sum(stripped.count(token.lower()) for token in NOISE_TOKENS)
    digit_inside_word_count = sum(1 for token in token_list if has_digit_inside_word(token))
    very_short_word_ratio = (
        sum(1 for token in token_list if len(token) <= 1) / token_count
        if token_count
        else 1.0
    )

    if expected_language == "ell":
        signal_words = GREEK_SIGNAL_WORDS
        expected_chars = greek_chars
        unexpected_chars = latin_chars
    else:
        signal_words = ENGLISH_SIGNAL_WORDS
        expected_chars = latin_chars
        unexpected_chars = greek_chars

    normalized_signal_words = {strip_accents(word).lower() for word in signal_words}
    signal_count = sum(1 for token in stripped_tokens if token in normalized_signal_words)
    expected_char_ratio = expected_chars / char_count if char_count else 0
    unexpected_char_ratio = unexpected_chars / char_count if char_count else 0

    readability_index = 0.0
    readability_index += min(char_count / 1800, 1.0) * 20
    readability_index += min(token_count / 280, 1.0) * 25
    readability_index += min(signal_count / 25, 1.0) * 25
    readability_index += min(expected_char_ratio / 0.55, 1.0) * 20

    if ocr_confidence is not None:
        readability_index += min(max(ocr_confidence, 0) / 100, 1.0) * 10

    readability_index -= min(unexpected_char_ratio / 0.20, 1.0) * 12
    readability_index -= min(noise_token_count / 5, 1.0) * 15
    readability_index -= min(digit_inside_word_count / 5, 1.0) * 10
    readability_index -= min(very_short_word_ratio / 0.30, 1.0) * 8
    readability_index = max(0, round(readability_index, 2))

    return {
        "chars": char_count,
        "words": token_count,
        "greek_chars": greek_chars,
        "latin_chars": latin_chars,
        "expected_char_ratio": round(expected_char_ratio, 4),
        "unexpected_char_ratio": round(unexpected_char_ratio, 4),
        "signal_words": signal_count,
        "noise_tokens": noise_token_count,
        "digit_inside_words": digit_inside_word_count,
        "very_short_word_ratio": round(very_short_word_ratio, 4),
        "ocr_confidence": ocr_confidence,
        "readability_index": readability_index,
    }


def classify_candidate(metrics: dict) -> str:
    if metrics["chars"] < 80 or metrics["words"] < 15:
        return "empty"
    if metrics["readability_index"] >= 70:
        return "good"
    if metrics["readability_index"] >= 50:
        return "usable"
    if metrics["readability_index"] >= 35:
        return "weak"
    return "bad"


def detect_page_role(text: str, metrics: dict) -> str:
    norm = strip_accents(normalize_for_search(text))

    if metrics["chars"] < 80 or metrics["words"] < 15:
        return "blank_or_noise"

    if any(term in norm for term in ["περιεχομενα", "contents"]):
        return "table_of_contents"

    cover_terms = ["μελετη", "εκθεσις", "εκθεσης", "ινστιτουτο", "γεωλογικων", "report on"]
    if metrics["words"] < 80 and any(term in norm for term in cover_terms):
        return "cover_or_metadata"

    if metrics["readability_index"] < 35:
        return "low_confidence"

    return "content"


def decide_action(page_role: str, candidate_quality: str, metrics: dict) -> str:
    if page_role in {"cover_or_metadata", "table_of_contents"}:
        return "metadata_only"
    if page_role == "blank_or_noise":
        return "skip"
    if (
        candidate_quality in {"good", "usable"}
        and metrics["words"] >= MIN_CONTENT_WORDS
        and metrics["chars"] >= MIN_CONTENT_CHARS
    ):
        return "index_content"
    if candidate_quality == "weak":
        return "manual_review"
    return "skip"


def render_page_to_image(page: fitz.Page, output_path: Path, scale: int = 3) -> Path:
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    pix.save(output_path)
    return output_path


def crop_to_content(input_image_path: Path, output_image_path: Path, padding: int = 30) -> Path:
    img = cv2.imread(str(input_image_path))
    if img is None:
        raise RuntimeError(f"Could not read image: {input_image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = gray < 245
    coords = np.argwhere(mask)

    if coords.size == 0:
        shutil.copyfile(input_image_path, output_image_path)
        return output_image_path

    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0)

    h, w = gray.shape
    x0 = max(int(x0) - padding, 0)
    y0 = max(int(y0) - padding, 0)
    x1 = min(int(x1) + padding, w - 1)
    y1 = min(int(y1) + padding, h - 1)

    cropped = img[y0 : y1 + 1, x0 : x1 + 1]
    cv2.imwrite(str(output_image_path), cropped)
    return output_image_path


def preprocess_for_ocr(input_image_path: Path, output_image_path: Path) -> Path:
    img = cv2.imread(str(input_image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Could not read image: {input_image_path}")

    denoised = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)
    cv2.imwrite(str(output_image_path), contrast)
    return output_image_path


def run_tesseract(image_path: Path, lang: str, psm: int) -> tuple[str, float | None]:
    try:
        text = pytesseract.image_to_string(
            Image.open(image_path),
            lang=lang,
            config=f"--oem 1 --psm {psm}",
        )
    except Exception:
        return "", None

    return text, get_tesseract_confidence(image_path, lang, psm)


def build_candidate_record(
    name: str,
    method_type: str,
    text: str,
    expected_language: str,
    text_path: Path,
    ocr_confidence: float | None = None,
    extra: dict | None = None,
) -> dict:
    metrics = estimate_metrics(text, expected_language, ocr_confidence)
    quality = classify_candidate(metrics)
    role = detect_page_role(text, metrics)

    safe_write_text(text_path, text)

    return {
        "method_type": method_type,
        "text_path": str(text_path),
        "metrics": metrics,
        "quality": quality,
        "page_role": role,
        "preview": preview_text(text, 400),
        "extra": extra or {},
    }


def choose_candidate(candidates: dict) -> dict:
    role_rank = {
        "content": 4,
        "table_of_contents": 3,
        "cover_or_metadata": 3,
        "low_confidence": 1,
        "blank_or_noise": 0,
    }
    quality_rank = {
        "good": 4,
        "usable": 3,
        "weak": 2,
        "bad": 1,
        "empty": 0,
    }

    selected_name, selected_data = max(
        candidates.items(),
        key=lambda item: (
            role_rank.get(item[1]["page_role"], 0),
            quality_rank.get(item[1]["quality"], 0),
            item[1]["metrics"]["readability_index"],
            item[1]["metrics"]["words"],
        ),
    )

    action = decide_action(
        selected_data["page_role"],
        selected_data["quality"],
        selected_data["metrics"],
    )

    return {
        "selected_method": selected_name,
        "selected_quality": selected_data["quality"],
        "page_role": selected_data["page_role"],
        "action": action,
        "reason": (
            f"Selected {selected_name}: role={selected_data['page_role']}, "
            f"quality={selected_data['quality']}, "
            f"readability={selected_data['metrics']['readability_index']}. "
            f"Action={action}."
        ),
    }


def extract_page_candidates(
    pdf_path: Path,
    page_number: int,
    expected_language: str,
    output_dir: Path,
    lang: str,
    scale: int,
    psm_modes: list[int],
) -> dict:
    page_dir = output_dir / pdf_path.stem / f"page_{page_number:03d}"
    page_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    page_index = page_number - 1
    if page_index < 0 or page_index >= len(doc):
        raise ValueError(f"Page {page_number} out of range. PDF has {len(doc)} pages.")

    page = doc[page_index]
    candidates: dict[str, dict] = {}

    native_text = extract_with_pymupdf(page)
    candidates["pymupdf_native"] = build_candidate_record(
        "pymupdf_native",
        "native",
        native_text,
        expected_language,
        page_dir / "01_pymupdf_native.txt",
    )

    llm_text = extract_with_pymupdf4llm(pdf_path, page_number)
    if llm_text:
        candidates["pymupdf4llm"] = build_candidate_record(
            "pymupdf4llm",
            "native",
            llm_text,
            expected_language,
            page_dir / "02_pymupdf4llm.md",
        )

    rendered_path = render_page_to_image(page, page_dir / "03_rendered_page.png", scale)
    cropped_path = crop_to_content(rendered_path, page_dir / "04_cropped_page.png")

    for psm in psm_modes:
        text, conf = run_tesseract(cropped_path, lang, psm)
        candidates[f"tesseract_raw_psm_{psm}"] = build_candidate_record(
            f"tesseract_raw_psm_{psm}",
            "ocr",
            text,
            expected_language,
            page_dir / f"05_tesseract_raw_psm_{psm}.txt",
            ocr_confidence=conf,
            extra={"psm": psm, "image_path": str(cropped_path)},
        )

    processed_path = preprocess_for_ocr(cropped_path, page_dir / "06_processed_page.png")
    for psm in psm_modes:
        text, conf = run_tesseract(processed_path, lang, psm)
        candidates[f"tesseract_processed_psm_{psm}"] = build_candidate_record(
            f"tesseract_processed_psm_{psm}",
            "ocr",
            text,
            expected_language,
            page_dir / f"07_tesseract_processed_psm_{psm}.txt",
            ocr_confidence=conf,
            extra={"psm": psm, "image_path": str(processed_path)},
        )

    page_bundle = {
        "pdf": pdf_path.stem,
        "pdf_path": str(pdf_path),
        "page": page_number,
        "expected_language": expected_language,
        "render_scale": scale,
        "ocr_lang": lang,
        "psm_modes": psm_modes,
        "candidates": candidates,
    }

    safe_write_json(page_dir / "10_candidates.json", page_bundle)
    doc.close()
    return page_bundle


def score_page_bundle(page_bundle: dict, output_dir: Path) -> dict:
    page_dir = output_dir / page_bundle["pdf"] / f"page_{page_bundle['page']:03d}"
    candidates = page_bundle["candidates"]

    decision = choose_candidate(candidates)
    selected = candidates[decision["selected_method"]]
    selected_text = Path(selected["text_path"]).read_text(encoding="utf-8")
    normalized_text = normalize_for_search(selected_text)

    safe_write_text(page_dir / "08_selected_text.txt", selected_text)
    safe_write_text(page_dir / "09_selected_text_normalized.txt", normalized_text)

    result = {
        "pdf": page_bundle["pdf"],
        "pdf_path": page_bundle["pdf_path"],
        "page": page_bundle["page"],
        "expected_language": page_bundle["expected_language"],
        **decision,
        "selected_metrics": selected["metrics"],
        "selected_text_path": str(page_dir / "08_selected_text.txt"),
        "selected_normalized_text_path": str(page_dir / "09_selected_text_normalized.txt"),
        "candidates": candidates,
    }

    safe_write_json(page_dir / "11_page_decision.json", result)
    return result


def find_candidate_bundles(output_dir: Path, pdf_stem: str) -> list[Path]:
    return sorted((output_dir / pdf_stem).glob("page_*/10_candidates.json"))


def find_decision_files(output_dir: Path, pdf_stem: str) -> list[Path]:
    return sorted((output_dir / pdf_stem).glob("page_*/11_page_decision.json"))


def write_summary_outputs(results: list[dict], pdf_path: Path, output_dir: Path) -> None:
    decision_rows = []
    candidate_rows = []

    for result in results:
        selected_metrics = result["selected_metrics"]
        decision_rows.append(
            {
                "pdf": result["pdf"],
                "page": result["page"],
                "selected_method": result["selected_method"],
                "quality": result["selected_quality"],
                "page_role": result["page_role"],
                "action": result["action"],
                "readability": selected_metrics["readability_index"],
                "chars": selected_metrics["chars"],
                "words": selected_metrics["words"],
                "ocr_confidence": selected_metrics["ocr_confidence"],
                "reason": result["reason"],
            }
        )

        for name, candidate in result["candidates"].items():
            metrics = candidate["metrics"]
            candidate_rows.append(
                {
                    "pdf": result["pdf"],
                    "page": result["page"],
                    "method": name,
                    "type": candidate["method_type"],
                    "quality": candidate["quality"],
                    "page_role": candidate["page_role"],
                    "readability": metrics["readability_index"],
                    "chars": metrics["chars"],
                    "words": metrics["words"],
                    "expected_char_ratio": metrics["expected_char_ratio"],
                    "signal_words": metrics["signal_words"],
                    "noise_tokens": metrics["noise_tokens"],
                    "digit_inside_words": metrics["digit_inside_words"],
                    "ocr_confidence": metrics["ocr_confidence"],
                    "selected": name == result["selected_method"],
                    "preview": candidate["preview"],
                }
            )

    safe_write_json(output_dir / f"{pdf_path.stem}_summary.json", results)
    pd.DataFrame(decision_rows).to_csv(
        output_dir / "page_decisions.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(candidate_rows).to_csv(
        output_dir / "candidate_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )


def write_markdown_report(results: list[dict], output_dir: Path) -> None:
    report_path = output_dir / "comparison_report.md"
    lines = [
        "# PDF Extraction Benchmark Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Final Page Decisions",
        "",
        "| PDF | Page | Method | Quality | Role | Action | Readability | Words | Chars | OCR conf | Reason |",
        "|---|---:|---|---|---|---|---:|---:|---:|---:|---|",
    ]

    for result in results:
        metrics = result["selected_metrics"]
        conf = "" if metrics["ocr_confidence"] is None else metrics["ocr_confidence"]
        reason = result["reason"].replace("|", "\\|")
        lines.append(
            f"| {result['pdf']} | {result['page']} | {result['selected_method']} "
            f"| {result['selected_quality']} | {result['page_role']} | {result['action']} "
            f"| {metrics['readability_index']} | {metrics['words']} | {metrics['chars']} "
            f"| {conf} | {reason} |"
        )

    lines.extend(["", "## Detailed Pages", ""])

    for result in results:
        lines.append(f"### {result['pdf']} - page {result['page']}")
        lines.append("")
        lines.append(f"- Selected method: **{result['selected_method']}**")
        lines.append(f"- Quality: **{result['selected_quality']}**")
        lines.append(f"- Page role: **{result['page_role']}**")
        lines.append(f"- Action: **{result['action']}**")
        lines.append(f"- Reason: {result['reason']}")
        lines.append("")
        lines.append("| Method | Type | Quality | Role | Readability | Words | Chars | Signal words | Noise | OCR conf |")
        lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|")

        for name, candidate in sorted(
            result["candidates"].items(),
            key=lambda item: (
                item[0] != result["selected_method"],
                -item[1]["metrics"]["readability_index"],
            ),
        ):
            metrics = candidate["metrics"]
            conf = "" if metrics["ocr_confidence"] is None else metrics["ocr_confidence"]
            mark = " yes" if name == result["selected_method"] else ""
            lines.append(
                f"| {name}{mark} | {candidate['method_type']} | {candidate['quality']} "
                f"| {candidate['page_role']} | {metrics['readability_index']} "
                f"| {metrics['words']} | {metrics['chars']} | {metrics['signal_words']} "
                f"| {metrics['noise_tokens']} | {conf} |"
            )

        lines.extend(
            [
                "",
                "Selected preview:",
                "",
                "```text",
                preview_text(
                    Path(result["selected_text_path"]).read_text(encoding="utf-8"),
                    1200,
                ),
                "```",
                "",
            ]
        )

    safe_write_text(report_path, "\n".join(lines))
