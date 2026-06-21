# Django Models Outline

Το παρόν κείμενο προτείνει ένα πρακτικό outline για τα βασικά `Django models` του `PoC`.

Δεν είναι πλήρες `models.py`, αλλά είναι αρκετά συγκεκριμένο ώστε η ομάδα να μπορεί να το μετατρέψει άμεσα σε υλοποίηση.

## 1. Βασικές αρχές

Για το `PoC`, το μοντέλο δεδομένων πρέπει να υποστηρίζει:

- καταχώριση τεκμηρίων και σύνδεση με `KOHA`
- επεξεργασία ανά σελίδα
- πολλαπλούς extraction candidates ανά σελίδα
- τελική απόφαση ποιότητας ανά σελίδα
- χειροκίνητο review όπου χρειάζεται
- chunking και embeddings μόνο για σελίδες που εγκρίνονται

Η σωστή λογική σχέσεων είναι:

```text
Document
  -> DocumentPage
    -> ExtractionCandidate
    -> ReviewTask
    -> DocumentChunk
      -> EmbeddingVector
```

## 2. App `documents`

### `KohaRecord`

Ρόλος:

- αποθήκευση του metadata record που έρχεται από `KOHA`

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `koha_biblio_id = models.CharField(max_length=128, unique=True, db_index=True)`
- `title = models.TextField(blank=True)`
- `author = models.TextField(blank=True)`
- `publication_year = models.CharField(max_length=32, blank=True)`
- `language = models.CharField(max_length=32, blank=True)`
- `keywords_json = models.JSONField(default=list, blank=True)`
- `raw_metadata_json = models.JSONField(default=dict, blank=True)`
- `source_file = models.CharField(max_length=512, blank=True)`
- `created_at = models.DateTimeField(auto_now_add=True)`
- `updated_at = models.DateTimeField(auto_now=True)`

Χρήσιμα indexes:

- `koha_biblio_id`

### `Document`

Ρόλος:

- κύρια εγγραφή για κάθε PDF / τεκμήριο που επεξεργάζεται το `PoC`

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `document_id = models.CharField(max_length=64, unique=True, db_index=True)`
- `koha_record = models.ForeignKey("documents.KohaRecord", null=True, blank=True, on_delete=models.SET_NULL, related_name="documents")`
- `title = models.TextField(blank=True)`
- `filename = models.CharField(max_length=255)`
- `source_path = models.CharField(max_length=1024)`
- `checksum = models.CharField(max_length=128, db_index=True)`
- `mime_type = models.CharField(max_length=128, default="application/pdf")`
- `file_size_bytes = models.BigIntegerField(null=True, blank=True)`
- `page_count = models.IntegerField(null=True, blank=True)`
- `language = models.CharField(max_length=32, blank=True)`
- `ingest_status = models.CharField(max_length=32, db_index=True)`
- `processing_status = models.CharField(max_length=32, db_index=True, default="registered")`
- `storage_root = models.CharField(max_length=1024, blank=True)`
- `created_at = models.DateTimeField(auto_now_add=True)`
- `updated_at = models.DateTimeField(auto_now=True)`

Προτεινόμενες τιμές `ingest_status`:

- `registered`
- `metadata_linked`
- `ready_for_extraction`
- `extracted`
- `review_pending`
- `indexed`
- `failed`

Χρήσιμα constraints:

- `UniqueConstraint(fields=["checksum"], name="uq_document_checksum")`

Χρήσιμα indexes:

- `document_id`
- `checksum`
- `ingest_status`
- `processing_status`

## 3. App `extraction`

### `ExtractionRun`

Ρόλος:

- καταγραφή μιας εκτέλεσης pipeline για ένα document ή για ένα batch

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `run_id = models.CharField(max_length=64, unique=True, db_index=True)`
- `document = models.ForeignKey("documents.Document", on_delete=models.CASCADE, related_name="extraction_runs")`
- `triggered_by = models.CharField(max_length=128, blank=True)`
- `run_type = models.CharField(max_length=32, default="manual")`
- `status = models.CharField(max_length=32, db_index=True, default="started")`
- `pipeline_version = models.CharField(max_length=64, blank=True)`
- `config_json = models.JSONField(default=dict, blank=True)`
- `summary_json = models.JSONField(default=dict, blank=True)`
- `started_at = models.DateTimeField(auto_now_add=True)`
- `finished_at = models.DateTimeField(null=True, blank=True)`

Προτεινόμενες τιμές `status`:

- `started`
- `completed`
- `failed`

### `DocumentPage`

Ρόλος:

- κύρια εγγραφή ανά σελίδα PDF

Γιατί χρειάζεται:

- στο συγκεκριμένο έργο η απόφαση ποιότητας δεν λαμβάνεται μόνο σε επίπεδο τεκμηρίου αλλά σε επίπεδο σελίδας
- το ίδιο `PDF` μπορεί να περιέχει εξώφυλλο, πίνακα περιεχομένων, καθαρό επιστημονικό κείμενο και προβληματικές σαρώσεις
- οι `ExtractionCandidate` αφορούν εναλλακτικά αποτελέσματα για μία συγκεκριμένη σελίδα
- η απόφαση `index_content`, `metadata_only`, `manual_review` ή `skip` πρέπει να αποθηκεύεται ανά σελίδα
- τα chunks και τα embeddings πρέπει να διατηρούν αναφορά στην ακριβή σελίδα προέλευσης

Χωρίς το `DocumentPage`, το σύστημα θα έπρεπε να αντιμετωπίζει όλο το τεκμήριο ως ομοιογενές, κάτι που δεν ισχύει στα περισσότερα πιλοτικά αρχεία.

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `document = models.ForeignKey("documents.Document", on_delete=models.CASCADE, related_name="pages")`
- `page_number = models.IntegerField()`
- `extraction_run = models.ForeignKey("extraction.ExtractionRun", null=True, blank=True, on_delete=models.SET_NULL, related_name="pages")`
- `selected_method = models.CharField(max_length=128, blank=True)`
- `selected_quality = models.CharField(max_length=32, blank=True, db_index=True)`
- `page_role = models.CharField(max_length=64, blank=True, db_index=True)`
- `action = models.CharField(max_length=32, blank=True, db_index=True)`
- `selected_text_path = models.CharField(max_length=1024, blank=True)`
- `normalized_text_path = models.CharField(max_length=1024, blank=True)`
- `selected_metrics_json = models.JSONField(default=dict, blank=True)`
- `review_status = models.CharField(max_length=32, default="not_required", db_index=True)`
- `review_notes = models.TextField(blank=True)`
- `created_at = models.DateTimeField(auto_now_add=True)`
- `updated_at = models.DateTimeField(auto_now=True)`

Προτεινόμενες τιμές `selected_quality`:

- `good`
- `usable`
- `weak`
- `bad`
- `empty`

Προτεινόμενες τιμές `page_role`:

- `content`
- `cover_or_metadata`
- `table_of_contents`
- `low_confidence`
- `blank_or_noise`

Προτεινόμενες τιμές `action`:

- `index_content`
- `metadata_only`
- `manual_review`
- `skip`

Προτεινόμενες τιμές `review_status`:

- `not_required`
- `pending`
- `approved`
- `rejected`

Χρήσιμα constraints:

- `UniqueConstraint(fields=["document", "page_number"], name="uq_document_page")`

Χρήσιμα indexes:

- `document, page_number`
- `action`
- `page_role`
- `review_status`

Ενδεικτικό παράδειγμα model:

```python
from django.db import models


class DocumentPage(models.Model):
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="pages",
    )
    page_number = models.IntegerField()
    selected_method = models.CharField(max_length=128, blank=True)
    selected_quality = models.CharField(max_length=32, blank=True, db_index=True)
    page_role = models.CharField(max_length=64, blank=True, db_index=True)
    action = models.CharField(max_length=32, blank=True, db_index=True)
    selected_text_path = models.CharField(max_length=1024, blank=True)
    normalized_text_path = models.CharField(max_length=1024, blank=True)
    selected_metrics_json = models.JSONField(default=dict, blank=True)
    review_status = models.CharField(max_length=32, default="not_required", db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "page_number"],
                name="uq_document_page",
            )
        ]
```

Επεξήγηση:

- κάθε εγγραφή αντιστοιχεί σε μία συγκεκριμένη σελίδα ενός συγκεκριμένου τεκμηρίου
- το `selected_method` δείχνει ποια μέθοδος κέρδισε τελικά, π.χ. `pymupdf_native` ή `tesseract_processed_psm_6`
- το `selected_quality` κρατά τη συνοπτική αποτίμηση του καλύτερου candidate
- το `page_role` βοηθά να ξεχωρίζουμε content, cover, table of contents ή low-confidence page
- το `action` είναι η τελική επιχειρησιακή απόφαση, δηλαδή αν η σελίδα θα περάσει σε indexing, review ή skip
- τα `selected_text_path` και `normalized_text_path` δείχνουν στα τελικά artifacts στο filesystem
- το `selected_metrics_json` κρατά traceability χωρίς να απαιτείται ξεχωριστό πεδίο για κάθε metric από την πρώτη φάση

Πρακτικά, το `DocumentPage` είναι το σημείο όπου συμπυκνώνεται η page-level απόφαση του pipeline.

### `ExtractionCandidate`

Ρόλος:

- αποθήκευση όλων των εναλλακτικών extraction outputs για μία σελίδα

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `page = models.ForeignKey("extraction.DocumentPage", on_delete=models.CASCADE, related_name="candidates")`
- `method_name = models.CharField(max_length=128, db_index=True)`
- `method_type = models.CharField(max_length=32, db_index=True)`
- `ocr_psm = models.IntegerField(null=True, blank=True)`
- `artifact_path = models.CharField(max_length=1024, blank=True)`
- `preview_text = models.TextField(blank=True)`
- `metrics_json = models.JSONField(default=dict, blank=True)`
- `quality = models.CharField(max_length=32, blank=True, db_index=True)`
- `page_role = models.CharField(max_length=64, blank=True, db_index=True)`
- `is_selected = models.BooleanField(default=False, db_index=True)`
- `extra_json = models.JSONField(default=dict, blank=True)`
- `created_at = models.DateTimeField(auto_now_add=True)`

Προτεινόμενες τιμές `method_type`:

- `native`
- `ocr`

Χρήσιμα constraints:

- `UniqueConstraint(fields=["page", "method_name"], name="uq_page_method_name")`

Χρήσιμα indexes:

- `page, method_name`
- `quality`
- `is_selected`

Ενδεικτικό παράδειγμα model:

```python
from django.db import models


class ExtractionCandidate(models.Model):
    page = models.ForeignKey(
        "extraction.DocumentPage",
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    method_name = models.CharField(max_length=128, db_index=True)
    method_type = models.CharField(max_length=32, db_index=True)
    ocr_psm = models.IntegerField(null=True, blank=True)
    artifact_path = models.CharField(max_length=1024, blank=True)
    preview_text = models.TextField(blank=True)
    metrics_json = models.JSONField(default=dict, blank=True)
    quality = models.CharField(max_length=32, blank=True, db_index=True)
    page_role = models.CharField(max_length=64, blank=True, db_index=True)
    is_selected = models.BooleanField(default=False, db_index=True)
    extra_json = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["page", "method_name"],
                name="uq_page_method_name",
            )
        ]
```

Επεξήγηση:

- κάθε `ExtractionCandidate` είναι μία εναλλακτική απόπειρα εξαγωγής για την ίδια σελίδα
- το `method_name` κρατά την πλήρη ταυτότητα της μεθόδου, π.χ. `tesseract_raw_psm_3`
- το `method_type` κρατά τον γενικό τύπο, π.χ. `native` ή `ocr`
- το `ocr_psm` χρειάζεται μόνο στις OCR περιπτώσεις, για να ξέρουμε ποια ρύθμιση χρησιμοποιήθηκε
- το `artifact_path` δείχνει στο text artifact που παρήχθη από αυτή τη μέθοδο
- το `metrics_json` κρατά τα μετρήσιμα signals, όπως `chars`, `words`, `ocr_confidence`, `readability_index`
- το `is_selected` δείχνει αν ο candidate ήταν ο τελικός νικητής για τη συγκεκριμένη σελίδα
- το `extra_json` επιτρέπει να κρατηθούν βοηθητικά στοιχεία χωρίς να βαραίνει νωρίς το schema

Πρακτικά, το `ExtractionCandidate` επιτρέπει να μη χαθεί η πληροφορία για τις αποτυχημένες ή οριακές εναλλακτικές προσπάθειες extraction. Αυτό είναι χρήσιμο και για debugging και για μελλοντική βελτίωση του pipeline.

### `ExtractionArtifact`

Ρόλος:

- καταγραφή paths για rendered images, processed images, reports και ενδιάμεσα αρχεία

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `page = models.ForeignKey("extraction.DocumentPage", on_delete=models.CASCADE, related_name="artifacts")`
- `candidate = models.ForeignKey("extraction.ExtractionCandidate", null=True, blank=True, on_delete=models.CASCADE, related_name="artifacts")`
- `artifact_type = models.CharField(max_length=64, db_index=True)`
- `file_path = models.CharField(max_length=1024)`
- `mime_type = models.CharField(max_length=128, blank=True)`
- `size_bytes = models.BigIntegerField(null=True, blank=True)`
- `created_at = models.DateTimeField(auto_now_add=True)`

Προτεινόμενες τιμές `artifact_type`:

- `rendered_page_image`
- `cropped_page_image`
- `processed_page_image`
- `native_text`
- `ocr_text`
- `selected_text`
- `normalized_text`
- `page_decision_json`

## 4. App `review`

### `ReviewTask`

Ρόλος:

- ουρά χειροκίνητου ελέγχου για σελίδες `manual_review`

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `page = models.OneToOneField("extraction.DocumentPage", on_delete=models.CASCADE, related_name="review_task")`
- `reason = models.CharField(max_length=255, blank=True)`
- `status = models.CharField(max_length=32, db_index=True, default="pending")`
- `assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="review_tasks")`
- `priority = models.CharField(max_length=16, default="normal", db_index=True)`
- `created_at = models.DateTimeField(auto_now_add=True)`
- `completed_at = models.DateTimeField(null=True, blank=True)`

Προτεινόμενες τιμές `status`:

- `pending`
- `in_progress`
- `approved`
- `rejected`

### `ReviewDecision`

Ρόλος:

- ιστορικό αποφάσεων review

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `review_task = models.ForeignKey("review.ReviewTask", on_delete=models.CASCADE, related_name="decisions")`
- `decision = models.CharField(max_length=32, db_index=True)`
- `selected_candidate = models.ForeignKey("extraction.ExtractionCandidate", null=True, blank=True, on_delete=models.SET_NULL, related_name="review_decisions")`
- `notes = models.TextField(blank=True)`
- `decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="review_decisions")`
- `created_at = models.DateTimeField(auto_now_add=True)`

Προτεινόμενες τιμές `decision`:

- `approve_selected`
- `select_other_candidate`
- `mark_metadata_only`
- `mark_skip`

## 5. App `search`

### `DocumentChunk`

Ρόλος:

- chunks που παράγονται μόνο από σελίδες κατάλληλες για indexing

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `document = models.ForeignKey("documents.Document", on_delete=models.CASCADE, related_name="chunks")`
- `page = models.ForeignKey("extraction.DocumentPage", on_delete=models.CASCADE, related_name="chunks")`
- `chunk_index = models.IntegerField()`
- `text = models.TextField()`
- `normalized_text = models.TextField(blank=True)`
- `token_count_estimate = models.IntegerField(null=True, blank=True)`
- `chunk_status = models.CharField(max_length=32, default="ready", db_index=True)`
- `created_at = models.DateTimeField(auto_now_add=True)`

Προτεινόμενες τιμές `chunk_status`:

- `ready`
- `embedded`
- `failed`

Χρήσιμα constraints:

- `UniqueConstraint(fields=["page", "chunk_index"], name="uq_page_chunk_index")`

### `EmbeddingVector`

Ρόλος:

- αποθήκευση embedding για κάθε chunk μέσα στη `PostgreSQL` με χρήση `pgvector`

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `chunk = models.OneToOneField("search.DocumentChunk", on_delete=models.CASCADE, related_name="embedding")`
- `embedding = VectorField(dimensions=768)` ή άλλο dimension ανάλογα με το embedding model
- `model_name = models.CharField(max_length=128, db_index=True)`
- `vector_status = models.CharField(max_length=32, default="created", db_index=True)`
- `dimension = models.IntegerField()`
- `embedding_version = models.CharField(max_length=64, blank=True)`
- `metadata_json = models.JSONField(default=dict, blank=True)`
- `created_at = models.DateTimeField(auto_now_add=True)`
- `updated_at = models.DateTimeField(auto_now=True)`

Προτεινόμενες τιμές `vector_status`:

- `created`
- `stored`
- `failed`

Για το `PoC`, η πρόθεση είναι σαφής:

- το πραγματικό embedding vector αποθηκεύεται τελικά μέσα στην ίδια βάση `PostgreSQL`
- η επέκταση που χρησιμοποιείται είναι η `pgvector`
- κάθε `DocumentChunk` αντιστοιχεί σε μία εγγραφή `EmbeddingVector`
- δεν προβλέπεται ξεχωριστό vector database στην πιλοτική φάση

Η πρακτική υλοποίηση είναι η εξής:

1. δημιουργείται το chunk στο `DocumentChunk`
2. καλείται το embedding model μέσω `Ollama`
3. επιστρέφεται λίστα αριθμών `float`
4. η λίστα αποθηκεύεται στο πεδίο `embedding`
5. το `vector_status` αλλάζει σε `stored`

Σε επίπεδο `Django`, αυτό σημαίνει ότι το `search` app πρέπει να χρησιμοποιεί `pgvector`-compatible field, ώστε το vector να γράφεται στον πίνακα της `PostgreSQL` και να μπορεί μετά να χρησιμοποιηθεί σε vector similarity queries.

Ενδεικτικό παράδειγμα model:

```python
from django.db import models
from pgvector.django import VectorField


class DocumentChunk(models.Model):
    document = models.ForeignKey("documents.Document", on_delete=models.CASCADE)
    page = models.ForeignKey("extraction.DocumentPage", on_delete=models.CASCADE)
    chunk_index = models.IntegerField()
    text = models.TextField()
    normalized_text = models.TextField(blank=True)


class EmbeddingVector(models.Model):
    chunk = models.OneToOneField(
        DocumentChunk,
        on_delete=models.CASCADE,
        related_name="embedding",
    )
    embedding = VectorField(dimensions=768)
    model_name = models.CharField(max_length=128)
    vector_status = models.CharField(max_length=32, default="created")
    created_at = models.DateTimeField(auto_now_add=True)
```

Επεξήγηση:

- το `VectorField` είναι το πεδίο που αποθηκεύει τον embedding vector μέσα στη `PostgreSQL`
- το `dimensions=768` είναι παράδειγμα και πρέπει να ταιριάζει με το embedding model που θα χρησιμοποιηθεί
- το `OneToOneField` σημαίνει ότι στο `PoC` κάθε chunk αντιστοιχίζεται σε ένα embedding record
- το `normalized_text` είναι το κείμενο που συνήθως στέλνεται στο embedding model, όχι απαραίτητα το ακατέργαστο text

Ενδεικτικό παράδειγμα αποθήκευσης:

```python
import ollama


response = ollama.embed(
    model="nomic-embed-text",
    input=chunk.normalized_text,
)

vector = response["embeddings"][0]

EmbeddingVector.objects.create(
    chunk=chunk,
    embedding=vector,
    model_name="nomic-embed-text",
    vector_status="stored",
)
```

Επεξήγηση:

- καλείται το local embedding model μέσω `Ollama`
- επιστρέφεται ένας πίνακας από `float`
- ο πίνακας γράφεται απευθείας στο πεδίο `embedding`
- το `vector_status` δείχνει ότι το chunk έχει πλέον αποθηκευμένο vector

Ενδεικτικό παράδειγμα retrieval:

```python
from pgvector.django import CosineDistance

query_vector = ollama.embed(
    model="nomic-embed-text",
    input=query_text,
)["embeddings"][0]

results = EmbeddingVector.objects.order_by(
    CosineDistance("embedding", query_vector)
)[:5]
```

Επεξήγηση:

- το query μετατρέπεται πρώτα και αυτό σε embedding vector
- η `PostgreSQL` συγκρίνει το query vector με τα αποθηκευμένα vectors
- η ταξινόμηση γίνεται με similarity metric, εδώ ενδεικτικά με `CosineDistance`
- το αποτέλεσμα που επιστρέφεται είναι τα πιο σχετικά chunks, όχι απευθείας ολόκληρα documents

### `SearchQueryLog`

Ρόλος:

- καταγραφή αναζητήσεων για baseline και αξιολόγηση

Προτεινόμενα πεδία:

- `id = models.BigAutoField(primary_key=True)`
- `query_text = models.TextField()`
- `query_type = models.CharField(max_length=32, default="semantic", db_index=True)`
- `top_k = models.IntegerField(default=5)`
- `results_count = models.IntegerField(default=0)`
- `response_time_ms = models.IntegerField(null=True, blank=True)`
- `user_identifier = models.CharField(max_length=128, blank=True, db_index=True)`
- `session_identifier = models.CharField(max_length=128, blank=True, db_index=True)`
- `created_at = models.DateTimeField(auto_now_add=True, db_index=True)`

## 6. Σχέσεις που πρέπει να μείνουν σταθερές

Οι πιο σημαντικές σχέσεις είναι:

- ένα `Document` έχει πολλές `DocumentPage`
- κάθε `DocumentPage` έχει πολλούς `ExtractionCandidate`
- κάθε `DocumentPage` έχει το πολύ ένα ενεργό `ReviewTask`
- κάθε `DocumentPage` μπορεί να δώσει πολλά `DocumentChunk`
- κάθε `DocumentChunk` έχει ένα `EmbeddingVector`

Αυτό επιτρέπει:

- page-level extraction
- page-level review
- page-level traceability
- chunk-level semantic search

## 7. Ελάχιστο σύνολο μοντέλων πρώτης φάσης

Αν η ομάδα θέλει να ξεκινήσει με το απολύτως απαραίτητο, αρκούν:

- `KohaRecord`
- `Document`
- `DocumentPage`
- `ExtractionCandidate`
- `DocumentChunk`
- `EmbeddingVector`

Το `ReviewTask`, `ReviewDecision`, `ExtractionRun` και `ExtractionArtifact` μπορούν να μπουν αμέσως μετά, χωρίς να αλλάξει ο βασικός κορμός.

## 8. Ελάχιστα χρήσιμα admin views

Για το `PoC`, αξίζει να υπάρχουν τουλάχιστον τα εξής στο `Django Admin`:

- λίστα `Document` με φίλτρα `ingest_status`, `processing_status`
- λίστα `DocumentPage` με φίλτρα `action`, `page_role`, `review_status`
- λίστα `ExtractionCandidate` με φίλτρο `is_selected`
- λίστα `ReviewTask` με φίλτρο `status`
- λίστα `DocumentChunk` με φίλτρο `chunk_status`

## 9. Τι να αποφευχθεί στην πρώτη υλοποίηση

Στην πρώτη υλοποίηση καλό είναι να αποφευχθούν:

- υπερβολικά generic models
- polymorphic structures χωρίς λόγο
- πολύπλοκες inheritance αλυσίδες
- αποθήκευση όλων των artifacts μόνο μέσα στη βάση

Για το `PoC`, η απλή και ασφαλής πρακτική είναι:

- μεγάλα αρχεία στο filesystem
- metadata, statuses και σχέσεις στη βάση
