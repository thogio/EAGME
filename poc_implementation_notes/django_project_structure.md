# Django Project Structure

Το παρόν κείμενο προτείνει συγκεκριμένη δομή για την υλοποίηση του `PoC` σε `Django`.

Στόχος είναι να υπάρχει μια πιο συγκεκριμένη αφετηρία για την Ομάδα Πληροφορικής της ΕΑΓΜΕ, ώστε να μην χρειαστεί να ξεκινήσει από λευκή σελίδα, αλλά να έχει:

- συγκεκριμένα ονόματα `apps`
- συγκεκριμένα σημεία για `services`
- συγκεκριμένα paths για `management commands`
- καθαρό διαχωρισμό ανάμεσα σε documents, extraction, review και search

## 1. Προτεινόμενη δομή έργου

```text
eagme_poc/
  manage.py
  config/
    __init__.py
    settings.py
    urls.py
    asgi.py
    wsgi.py
  apps/
    common/
    documents/
    extraction/
    review/
    search/
    ai_runtime/
  storage/
    pdfs/
    koha_exports/
    extraction_reports/
    page_images/
  requirements/
    base.txt
    dev.txt
```

Η παραπάνω δομή αρκεί για το `PoC` και αφήνει καθαρό δρόμο για επέκταση μετά το πιλοτικό.

## 2. Προτεινόμενα Django apps

### `apps.common`

Ρόλος:

- κοινά helpers
- base models
- constants
- filesystem utilities
- κοινές enums για statuses

Προτεινόμενα αρχεία:

```text
apps/common/
  __init__.py
  apps.py
  constants.py
  choices.py
  file_utils.py
  model_utils.py
```

### `apps.documents`

Ρόλος:

- καταχώριση και διαχείριση τεκμηρίων
- σύνδεση PDF με metadata από `KOHA`
- βασική κατάσταση ingestion

Προτεινόμενα αρχεία:

```text
apps/documents/
  __init__.py
  apps.py
  models.py
  admin.py
  services/
    __init__.py
    registry.py
    koha_import.py
    checksum.py
  management/
    commands/
      register_pdfs.py
      ingest_koha_export.py
```

Προτεινόμενα μοντέλα:

- `Document`
- `DocumentSource`
- `KohaRecord`

Ελάχιστα πεδία `Document`:

- `document_id`
- `title`
- `filename`
- `source_path`
- `checksum`
- `mime_type`
- `language`
- `ingest_status`
- `koha_record_id`
- `created_at`
- `updated_at`

### `apps.extraction`

Ρόλος:

- extraction pipeline
- `OCR`
- candidate generation
- quality scoring
- επιλογή τελικού κειμένου ανά σελίδα

Προτεινόμενα αρχεία:

```text
apps/extraction/
  __init__.py
  apps.py
  models.py
  admin.py
  services/
    __init__.py
    extraction_pipeline.py
    native_extractors.py
    ocr_extractors.py
    image_processing.py
    scoring.py
    page_decisions.py
    report_builder.py
  management/
    commands/
      check_ocr_stack.py
      extract_candidates.py
      score_extractions.py
      generate_extraction_report.py
```

Προτεινόμενα μοντέλα:

- `DocumentPage`
- `ExtractionCandidate`
- `ExtractionArtifact`
- `ExtractionRun`

Ελάχιστα πεδία `DocumentPage`:

- `document`
- `page_number`
- `selected_method`
- `selected_quality`
- `page_role`
- `action`
- `selected_text_path`
- `normalized_text_path`
- `selected_metrics_json`
- `review_status`

Ελάχιστα πεδία `ExtractionCandidate`:

- `document`
- `page_number`
- `method_name`
- `method_type`
- `ocr_psm`
- `artifact_path`
- `preview_text`
- `metrics_json`
- `is_selected`
- `created_at`

### `apps.review`

Ρόλος:

- χειροκίνητος έλεγχος σελίδων που μπαίνουν σε `manual_review`
- τελική επικύρωση πριν το indexing

Προτεινόμενα αρχεία:

```text
apps/review/
  __init__.py
  apps.py
  models.py
  admin.py
  services/
    __init__.py
    review_queue.py
    review_actions.py
```

Προτεινόμενα μοντέλα:

- `ReviewTask`
- `ReviewDecision`

Ελάχιστα πεδία `ReviewTask`:

- `document`
- `page_number`
- `reason`
- `status`
- `assigned_to`
- `created_at`
- `completed_at`

### `apps.search`

Ρόλος:

- chunking
- embeddings
- `pgvector`
- retrieval
- search API / search services

Προτεινόμενα αρχεία:

```text
apps/search/
  __init__.py
  apps.py
  models.py
  admin.py
  services/
    __init__.py
    chunking.py
    embeddings.py
    vector_index.py
    retrieval.py
    hybrid_search.py
  management/
    commands/
      build_embeddings.py
      rebuild_vector_index.py
      evaluate_search.py
```

Προτεινόμενα μοντέλα:

- `DocumentChunk`
- `EmbeddingVector`
- `SearchQueryLog`

Ελάχιστα πεδία `DocumentChunk`:

- `document`
- `page_number`
- `chunk_index`
- `text`
- `normalized_text`
- `embedding_status`
- `vector_id`

### `apps.ai_runtime`

Ρόλος:

- σύνδεση με `Ollama`
- embedding model calls
- answer model calls
- health checks για local AI runtime

Προτεινόμενα αρχεία:

```text
apps/ai_runtime/
  __init__.py
  apps.py
  services/
    __init__.py
    ollama_client.py
    embeddings_client.py
    llm_client.py
    health_checks.py
  management/
    commands/
      test_ollama.py
```

Σημαντική παρατήρηση:

- το `Ollama` δεν χρειάζεται να γίνει ξεχωριστό web application
- χρειάζεται να γίνει καθαρό service layer μέσα στο `Django`

## 3. Προτεινόμενα management command paths

Η πιο καθαρή μορφή είναι:

```text
apps/documents/management/commands/register_pdfs.py
apps/documents/management/commands/ingest_koha_export.py
apps/extraction/management/commands/check_ocr_stack.py
apps/extraction/management/commands/extract_candidates.py
apps/extraction/management/commands/score_extractions.py
apps/extraction/management/commands/generate_extraction_report.py
apps/search/management/commands/build_embeddings.py
apps/search/management/commands/rebuild_vector_index.py
apps/search/management/commands/evaluate_search.py
apps/ai_runtime/management/commands/test_ollama.py
```

## 4. Προτεινόμενη αντιστοίχιση reference scripts προς services

| Reference artifact | Django target |
|---|---|
| `check_ocr_stack.sh` | `apps/extraction/management/commands/check_ocr_stack.py` |
| `extract_candidates_reference.py` | `apps/extraction/services/extraction_pipeline.py` |
| `score_extraction_reference.py` | `apps/extraction/services/scoring.py` + `page_decisions.py` |
| `report_extraction_reference.py` | `apps/extraction/services/report_builder.py` |
| `extraction_reference_lib.py` | διαμοιρασμός λογικής στα `native_extractors.py`, `ocr_extractors.py`, `image_processing.py`, `scoring.py` |

## 5. Προτεινόμενη εσωτερική διάσπαση services

Αν η ομάδα θέλει να κρατήσει τη λογική καθαρή, η καλύτερη διάσπαση είναι:

- `native_extractors.py`
  - `extract_with_pymupdf(...)`
  - `extract_with_pymupdf4llm(...)`

- `image_processing.py`
  - `render_page_to_image(...)`
  - `crop_to_content(...)`
  - `preprocess_for_ocr(...)`

- `ocr_extractors.py`
  - `run_tesseract(...)`
  - `get_tesseract_confidence(...)`

- `scoring.py`
  - `estimate_metrics(...)`
  - `classify_candidate(...)`
  - `detect_page_role(...)`

- `page_decisions.py`
  - `choose_candidate(...)`
  - `decide_action(...)`
  - `score_page_bundle(...)`

- `report_builder.py`
  - `write_summary_outputs(...)`
  - `write_markdown_report(...)`

## 6. Τι δεν χρειάζεται να γίνει περίπλοκο στο PoC

Για την πρώτη υλοποίηση δεν χρειάζεται:

- `Celery`
- μικροϋπηρεσίες
- ξεχωριστό API μόνο για OCR
- ξεχωριστό API μόνο για `Ollama`
- πολύπλοκο permissions model

Για το `PoC`, αρκεί:

- ένα `Django` project
- μερικά καθαρά `apps`
- `management commands`
- storage στο filesystem
- metadata και statuses στη βάση

## 7. Ελάχιστη υλοποίηση πρώτης φάσης

Αν η ομάδα θέλει να ξεκινήσει από το απολύτως απαραίτητο, μπορεί να υλοποιήσει πρώτα μόνο:

- `apps/documents`
- `apps/extraction`
- `apps/search`
- `apps/ai_runtime`

και να αφήσει το `apps/review` για αμέσως επόμενο βήμα.

Σε αυτή την περίπτωση, το manual review μπορεί προσωρινά να γίνεται:

- από `Django Admin`
- με φίλτρο σελίδων όπου `action = manual_review`

## 8. Προτεινόμενη σειρά ανάπτυξης

Η πιο πρακτική σειρά είναι:

1. `apps/documents`
2. `apps/extraction`
3. `apps/ai_runtime`
4. `apps/search`
5. `apps/review`

Αυτό επιτρέπει στην ομάδα να αποδείξει νωρίς ότι:

- το PDF ingestion δουλεύει
- το extraction pipeline παράγει αποτελέσματα
- η ποιότητα μπορεί να αξιολογηθεί
- τα σωστά κείμενα μπορούν να περάσουν σε embeddings και search
