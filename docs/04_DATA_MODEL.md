# Data Model Πιλοτικής Υλοποίησης

## 1. Βασικά tables

Η πιλοτική υλοποίηση χρησιμοποιεί τα παρακάτω βασικά tables:

```text
documents
document_pages
document_chunks
document_embeddings
extraction_runs
queries
query_results
answers
user_feedback
```

## 2. `documents`

Αντιπροσωπεύει μία τεχνική έκθεση.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `koha_record_id` | ID εγγραφής από KOHA. |
| `title` | Τίτλος έκθεσης. |
| `author` | Συγγραφέας ή φορέας. |
| `year` | Χρονολογία, όπου είναι διαθέσιμη. |
| `keywords` | Keywords από KOHA ή controlled vocabulary. |
| `pdf_path` | Path του PDF στο storage. |
| `checksum` | Checksum για ανίχνευση αλλαγών. |
| `processing_status` | Κατάσταση επεξεργασίας. |
| `created_at` | Ημερομηνία εισαγωγής. |
| `updated_at` | Ημερομηνία τελευταίας αλλαγής. |

## 3. `document_pages`

Αντιπροσωπεύει μία σελίδα PDF.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `document_id` | Σύνδεση με `documents`. |
| `page_number` | Αριθμός σελίδας. |
| `extracted_text` | Κείμενο όπως εξήχθη. |
| `normalized_text` | Καθαρισμένο/search-friendly κείμενο. |
| `extraction_method` | `native`, `ocr`, `manual`, `mixed`. |
| `quality_status` | `index_content`, `metadata_only`, `skip`, `manual_review`. |
| `quality_score` | Αριθμητική ένδειξη ποιότητας, αν χρησιμοποιηθεί. |
| `page_image_path` | Path rendered image για OCR/manual review. |
| `created_at` | Ημερομηνία δημιουργίας. |

## 4. `document_chunks`

Αντιπροσωπεύει chunk που μπορεί να χρησιμοποιηθεί για retrieval.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `document_id` | Σύνδεση με `documents`. |
| `page_start` | Πρώτη σελίδα chunk. |
| `page_end` | Τελευταία σελίδα chunk. |
| `original_text` | Πρωτότυπο κείμενο chunk. |
| `normalized_text` | Search-friendly κείμενο chunk. |
| `quality_status` | Κληρονομείται/υπολογίζεται από τις σελίδες. |
| `metadata` | JSON metadata για section, keywords, extraction details. |
| `created_at` | Ημερομηνία δημιουργίας. |

## 5. `document_embeddings`

Αντιπροσωπεύει embedding για chunk.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `chunk_id` | Σύνδεση με `document_chunks`. |
| `embedding` | Vector μέσω pgvector. |
| `embedding_model` | Όνομα embedding model. |
| `embedding_version` | Version ή deployment identifier. |
| `created_at` | Ημερομηνία δημιουργίας. |

## 6. `extraction_runs`

Καταγράφει κάθε εκτέλεση extraction.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `started_at` | Έναρξη run. |
| `finished_at` | Λήξη run. |
| `status` | `running`, `completed`, `failed`. |
| `documents_processed` | Πλήθος επεξεργασμένων εγγράφων. |
| `pages_processed` | Πλήθος επεξεργασμένων σελίδων. |
| `errors` | JSON με σφάλματα. |
| `config` | JSON με παραμέτρους run. |

## 7. `queries`

Καταγράφει ερωτήματα χρηστών.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `query_text` | Το ερώτημα του χρήστη. |
| `user_id` | Χρήστης, αν υπάρχει authentication. |
| `created_at` | Ημερομηνία ερωτήματος. |

## 8. `query_results`

Καταγράφει retrieval αποτελέσματα.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `query_id` | Σύνδεση με `queries`. |
| `chunk_id` | Σύνδεση με `document_chunks`. |
| `retrieval_method` | `metadata`, `keyword`, `vector`, `hybrid`. |
| `score` | Retrieval score. |
| `rank` | Θέση αποτελέσματος. |

## 9. `answers`

Καταγράφει απαντήσεις του AI Assistant.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `query_id` | Σύνδεση με `queries`. |
| `answer_text` | Παραγόμενη απάντηση. |
| `llm_model` | LLM model. |
| `prompt_version` | Version prompt. |
| `sources` | JSON με document/page/chunk citations. |
| `created_at` | Ημερομηνία απάντησης. |

## 10. `user_feedback`

Καταγράφει αξιολόγηση χρήστη.

Πεδία:

| Field | Περιγραφή |
|---|---|
| `id` | Εσωτερικό ID. |
| `query_id` | Σύνδεση με `queries`. |
| `answer_id` | Σύνδεση με `answers`. |
| `rating` | Αριθμητική αξιολόγηση. |
| `comment` | Προαιρετικό σχόλιο. |
| `created_at` | Ημερομηνία feedback. |

## 11. Constraints

Η υλοποίηση πρέπει να διασφαλίζει:

- ένα `document` να μπορεί να έχει πολλές `document_pages`,
- ένα `document` να μπορεί να έχει πολλά `document_chunks`,
- embeddings να δημιουργούνται μόνο για chunks με `quality_status = index_content`,
- κάθε answer να έχει sources,
- κάθε extraction run να είναι audit-able,
- αλλαγή embedding model να μην διαγράφει παλιά embeddings χωρίς ρητή reindex διαδικασία.

