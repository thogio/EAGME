# Django Commands Mapping

Το παρόν σημείωμα δείχνει πώς τα reference scripts του `PoC` μπορούν να μεταφερθούν σε `Django management commands`, χωρίς να αλλάξει η λογική τους.

Στόχος δεν είναι να μεταφερθούν αυτούσια τα scripts, αλλά:

- να κρατηθεί η ίδια ακολουθία βημάτων
- να κρατηθούν τα ίδια ενδιάμεσα artifacts όπου χρειάζεται
- να μπορεί η ομάδα να τρέχει κάθε στάδιο και από terminal και από `Django`

## Προτεινόμενη σειρά commands

```bash
python manage.py check_ocr_stack
python manage.py register_pdfs /app/data/pdfs
python manage.py extract_candidates --document-id DOC001 --pages 1,2,3
python manage.py score_extractions --document-id DOC001
python manage.py generate_extraction_report --document-id DOC001
python manage.py build_embeddings --document-id DOC001 --status index_content
```

## 1. Έλεγχος περιβάλλοντος

Reference script:

- `check_ocr_stack.sh`

Προτεινόμενο command:

```bash
python manage.py check_ocr_stack
```

Τι ελέγχει:

- αν υπάρχει `tesseract`
- αν υπάρχει το ελληνικό language pack `ell`
- αν υπάρχει `ollama`
- προαιρετικά αν υπάρχουν τα βασικά Python packages

Προτεινόμενο output:

- terminal report με `OK / MISSING`
- προαιρετική εγγραφή σε πίνακα `system_checks`

## 2. Καταχώριση PDF προς επεξεργασία

Reference logic:

- δεν υπάρχει ξεχωριστό script σήμερα, αλλά είναι προαπαιτούμενο βήμα πριν από το benchmark

Προτεινόμενο command:

```bash
python manage.py register_pdfs /app/data/pdfs
```

Είσοδος:

- φάκελος με PDF αρχεία

Τι κάνει:

- εντοπίζει τα PDF
- δημιουργεί εγγραφές `Document`
- αποθηκεύει βασικά στοιχεία όπως filename, path, checksum, status

Προτεινόμενα πεδία μοντέλου:

- `document_id`
- `source_path`
- `filename`
- `checksum`
- `mime_type`
- `ingest_status`
- `created_at`

## 3. Εξαγωγή candidates ανά σελίδα

Reference script:

- `extract_candidates_reference.py`

Κοινή λογική:

- `extraction_reference_lib.py`

Προτεινόμενο command:

```bash
python manage.py extract_candidates --document-id DOC001 --pages 1,2,3
```

Εναλλακτικά:

```bash
python manage.py extract_candidates --document-id DOC001 --page-range 1:20
```

Τι κάνει:

- ανοίγει το PDF
- κάνει native extraction με `PyMuPDF`
- προαιρετικά κάνει extraction με `pymupdf4llm`
- κάνει render της σελίδας σε εικόνα
- κόβει τα περιθώρια με `crop_to_content`
- τρέχει `Tesseract` σε πολλά `PSM`
- τρέχει `Tesseract` και σε preprocessed εικόνα
- αποθηκεύει όλα τα candidate texts και τα πρώτα metrics

Ενδεικτική αντιστοίχιση κώδικα:

- `extract_page_candidates(...)`
- `extract_with_pymupdf(...)`
- `extract_with_pymupdf4llm(...)`
- `render_page_to_image(...)`
- `crop_to_content(...)`
- `preprocess_for_ocr(...)`
- `run_tesseract(...)`

Artifacts που πρέπει να παραχθούν:

- raw/native text αρχεία ανά candidate
- rendered και processed images
- `10_candidates.json` ανά σελίδα

Προτεινόμενη αποθήκευση σε Django:

- filesystem για μεγάλα artifacts
- database για metadata και statuses

Προτεινόμενα μοντέλα:

- `DocumentPage`
- `ExtractionCandidate`
- `ExtractionArtifact`

Ενδεικτικά πεδία `ExtractionCandidate`:

- `document`
- `page_number`
- `method_name`
- `method_type`
- `ocr_psm`
- `artifact_path`
- `preview_text`
- `metrics_json`
- `created_at`

## 4. Αξιολόγηση candidates και απόφαση ανά σελίδα

Reference script:

- `score_extraction_reference.py`

Κοινή λογική:

- `estimate_metrics(...)`
- `classify_candidate(...)`
- `detect_page_role(...)`
- `choose_candidate(...)`
- `score_page_bundle(...)`

Προτεινόμενο command:

```bash
python manage.py score_extractions --document-id DOC001
```

Τι κάνει:

- διαβάζει τα candidates ανά σελίδα
- υπολογίζει readability και γλωσσικά metrics
- χαρακτηρίζει κάθε candidate ως `good`, `usable`, `weak`, `bad`, `empty`
- χαρακτηρίζει τον ρόλο της σελίδας ως `content`, `cover_or_metadata`, `table_of_contents`, `low_confidence`, `blank_or_noise`
- επιλέγει τον καλύτερο candidate
- αποφασίζει `index_content`, `metadata_only`, `manual_review`, `skip`

Artifacts που πρέπει να παραχθούν:

- `08_selected_text.txt`
- `09_selected_text_normalized.txt`
- `11_page_decision.json`
- `<pdf>_scored_pages.json`
- `page_decisions.csv`
- `candidate_comparison.csv`

Προτεινόμενα πεδία `DocumentPage`:

- `selected_method`
- `selected_quality`
- `page_role`
- `action`
- `selected_text_path`
- `normalized_text_path`
- `selected_metrics_json`
- `review_status`

## 5. Παραγωγή report

Reference script:

- `report_extraction_reference.py`

Κοινή λογική:

- `write_summary_outputs(...)`
- `write_markdown_report(...)`

Προτεινόμενο command:

```bash
python manage.py generate_extraction_report --document-id DOC001
```

Τι κάνει:

- συγκεντρώνει τις αποφάσεις όλων των σελίδων
- γράφει συνοπτικούς πίνακες
- γράφει αναλυτικό `comparison_report.md`

Outputs:

- `page_decisions.csv`
- `candidate_comparison.csv`
- `comparison_report.md`

Προαιρετική επέκταση:

- αποθήκευση report run σε πίνακα `ExtractionRun`
- σύνδεση report με ημερομηνία, operator και έκδοση pipeline

## 6. Δημιουργία embeddings μόνο για κατάλληλες σελίδες

Reference source:

- τα current reference scripts σταματούν πριν από το embedding stage
- η λογική όμως υπάρχει ήδη στα `action` values

Προτεινόμενο command:

```bash
python manage.py build_embeddings --document-id DOC001 --status index_content
```

Τι πρέπει να κάνει:

- διαβάζει μόνο σελίδες με `action=index_content`
- παίρνει το `09_selected_text_normalized.txt` ή το αντίστοιχο πεδίο από τη βάση
- εφαρμόζει chunking
- παράγει embeddings
- αποθηκεύει chunks και vectors

Σύνδεση με προηγούμενα βήματα:

- `metadata_only` pages δεν μπαίνουν σε semantic indexing
- `manual_review` pages περιμένουν ανθρώπινο έλεγχο
- `skip` pages εξαιρούνται

## 7. Πρακτική αντιστοίχιση script προς command

| Reference script | Django command | Ρόλος |
|---|---|---|
| `check_ocr_stack.sh` | `check_ocr_stack` | έλεγχος περιβάλλοντος |
| `extract_candidates_reference.py` | `extract_candidates` | παραγωγή extraction candidates |
| `score_extraction_reference.py` | `score_extractions` | αξιολόγηση και επιλογή candidate |
| `report_extraction_reference.py` | `generate_extraction_report` | παραγωγή συνοπτικών outputs |
| `benchmark_extraction_reference.py` | `run_extraction_benchmark` | end-to-end εκτέλεση |

## 8. Πρακτική αντιστοίχιση για το PoC

Για το `PoC`, η πιο απλή υλοποίηση είναι:

- τα μεγάλα αρχεία να μένουν στο filesystem
- τα statuses και τα metrics να μπαίνουν στη βάση
- τα `management commands` να καλούν την ίδια Python λογική που ήδη υπάρχει στο `extraction_reference_lib.py`

Αυτό σημαίνει ότι η ομάδα δεν χρειάζεται να ξαναγράψει από την αρχή το pipeline.

Χρειάζεται να κάνει:

1. μεταφορά της κοινής λογικής σε `Django app`, π.χ. `apps/extraction/services/`
2. ορισμό μοντέλων `Document`, `DocumentPage`, `ExtractionCandidate`, `ExtractionRun`
3. δημιουργία `management commands`
4. σύνδεση του `Admin` με τα page decisions και το manual review

## 9. Ελάχιστο set από commands για πρώτη υλοποίηση

Αν η ομάδα θέλει να ξεκινήσει με το απολύτως απαραίτητο, αρκούν τα εξής:

```bash
python manage.py register_pdfs /app/data/pdfs
python manage.py extract_candidates --document-id DOC001 --pages 1,2,3
python manage.py score_extractions --document-id DOC001
python manage.py generate_extraction_report --document-id DOC001
```

Αυτό αρκεί για να αποδείξει:

- ότι το extraction pipeline λειτουργεί
- ότι γίνεται επιλογή καλύτερου candidate
- ότι υπάρχει page-level quality control
- ότι μπορούμε να αποφασίσουμε ποιες σελίδες μπαίνουν για semantic indexing
