# Scripts Αναφοράς

Ο φάκελος αυτός περιέχει καθαρισμένα scripts αναφοράς για το `PoC`.

Σκοπός τους δεν είναι να αποτελέσουν αυτούσιο κώδικα παραγωγικής χρήσης, αλλά να προσφέρουν στην Ομάδα Πληροφορικής της ΕΑΓΜΕ:

- συγκεκριμένη βάση για το extraction benchmark
- συγκεκριμένα terminal βήματα ελέγχου του `OCR` stack
- επαναλήψιμα scripts που μπορούν να μεταφερθούν αργότερα σε `Django` commands

## Περιεχόμενα

- `check_ocr_stack.sh`
  - έλεγχος ότι υπάρχουν `tesseract`, ελληνικό language pack και `ollama`
- `extraction_reference_lib.py`
  - κοινή βιβλιοθήκη με OCR helpers, scoring, page-role logic και report helpers
- `extract_candidates_reference.py`
  - βήμα 1: εξαγωγή όλων των candidates και αποθήκευση των ενδιάμεσων artifacts
- `score_extraction_reference.py`
  - βήμα 2: επιλογή καλύτερου candidate και απόφαση `index_content` / `metadata_only` / `manual_review` / `skip`
- `report_extraction_reference.py`
  - βήμα 3: παραγωγή των συγκεντρωτικών αρχείων `csv` και του `comparison_report.md`
- `benchmark_extraction_reference.py`
  - ενιαίο wrapper που εκτελεί και τα τρία βήματα με μία εντολή

## Ελάχιστη εγκατάσταση

Σε `Ubuntu / Debian`:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-ell
python3 -m pip install pymupdf pytesseract pillow opencv-python pandas numpy
```

Προαιρετικά:

```bash
python3 -m pip install pymupdf4llm pandas
```

## Βασικοί έλεγχοι

```bash
bash reference_scripts/check_ocr_stack.sh
```

## Ενδεικτικό benchmark

```bash
python3 reference_scripts/benchmark_extraction_reference.py \
  --pdf "/path/to/document.pdf" \
  --pages 1,2,3 \
  --lang ell+eng \
  --expected-language ell
```

## Βήμα-βήμα εκτέλεση

```bash
python3 reference_scripts/extract_candidates_reference.py \
  --pdf "/path/to/document.pdf" \
  --pages 1,2,3 \
  --lang ell+eng \
  --expected-language ell
```

```bash
python3 reference_scripts/score_extraction_reference.py \
  --pdf "/path/to/document.pdf"
```

```bash
python3 reference_scripts/report_extraction_reference.py \
  --pdf "/path/to/document.pdf"
```

Το benchmark παράγει:

- native extraction outputs
- OCR outputs για κάθε `PSM`
- normalized selected text
- `10_candidates.json` ανά σελίδα
- `11_page_decision.json` ανά σελίδα
- `<pdf>_scored_pages.json`
- `page_decisions.csv`
- `candidate_comparison.csv`
- `comparison_report.md`

## Πώς συνδέεται με Django

Η λογική που δείχνουν τα scripts μπορεί να μεταφερθεί σε `Django management commands` όπως:

```bash
python manage.py ingest_koha_export /app/data/koha_exports/pilot_export.csv
python manage.py register_pdfs /app/data/pdfs
python manage.py extract_documents --limit 100
python manage.py build_embeddings --status index_content
python manage.py evaluate_search /app/data/koha_exports/historical_queries.csv
```

Πιο συγκεκριμένη αντιστοίχιση υπάρχει στο:

- `poc_implementation_notes/django_commands_mapping.md`
- `poc_implementation_notes/django_project_structure.md`
- `poc_implementation_notes/django_models_outline.md`

Η βασική ιδέα είναι:

- τα scripts εδώ χρησιμοποιούνται ως σημείο αναφοράς
- η τελική επιχειρησιακή ροή υλοποιείται μέσα στο `Django` backend
