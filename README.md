# Υψηλού Επιπέδου Αρχιτεκτονική Συστήματος AI Αναζήτησης για τη Βιβλιοθήκη ΕΑΓΜΕ

## 1. Στόχος του συστήματος

Στόχος του συστήματος είναι η βελτίωση της αναζήτησης στην online βιβλιοθήκη της ΕΑΓΜΕ, όχι η αντικατάσταση του υφιστάμενου καταλόγου.

Το υπάρχον σύστημα αναζήτησης βασίζεται κυρίως σε μεταδεδομένα, όπως τίτλος, συγγραφέας και keywords. Το νέο σύστημα θα λειτουργεί συμπληρωματικά, αξιοποιώντας όπου είναι εφικτό και το πλήρες περιεχόμενο των τεχνικών εκθέσεων PDF.

Η βασική ιδέα είναι:

```text
KOHA / υφιστάμενος κατάλογος
        +
Full-text extraction από PDFs
        +
Vector search / semantic search
        +
AI assistant με τεκμηριωμένες απαντήσεις
```

Ο χρήστης δεν θα παίρνει απλώς λίστα εγγράφων, αλλά απάντηση βασισμένη σε σχετικά αποσπάσματα, με αναφορά στο έγγραφο και στη σελίδα από όπου προκύπτει η πληροφορία.

---

## 2. Κρίσιμο εύρημα από την αρχική τεχνική διερεύνηση

Η βασική τεχνική δυσκολία δεν είναι η δημιουργία embeddings ή η χρήση LLM.

Η βασική δυσκολία είναι η αξιόπιστη εξαγωγή περιεχομένου από ετερογενή PDFs.

Στο δείγμα εγγράφων διαπιστώθηκαν διαφορετικές κατηγορίες αρχείων:

1. Νεότερα ή σχετικά καθαρά PDFs, όπου το υπάρχον text layer είναι αρκετά χρήσιμο.
2. Σκαναρισμένα έγγραφα με μέτρια ποιότητα OCR.
3. Παλαιά δακτυλογραφημένα ελληνικά έγγραφα, συχνά σε καθαρεύουσα.
4. Σελίδες με πολύ κακή σάρωση, θόρυβο, χαμηλή αντίθεση ή σχεδόν μη ανακτήσιμο κείμενο.
5. Σελίδες εξωφύλλων, περιεχομένων, πινάκων, χαρτών, σκαριφημάτων και εικόνων.

Επομένως, δεν είναι ασφαλές να εφαρμοστεί ένα ενιαίο pipeline του τύπου:

```text
PDF → OCR → vectors
```

Αυτό θα οδηγούσε σε indexing θορυβώδους ή λανθασμένου κειμένου, άρα και σε μη αξιόπιστες απαντήσεις από το AI assistant.

---

## 3. Προτεινόμενη βασική αρχιτεκτονική

Η προτεινόμενη αρχιτεκτονική είναι quality-aware και date-aware.

```text
PDF / KOHA record
        ↓
Ανάγνωση μεταδεδομένων
        ↓
Ταξινόμηση εγγράφου βάσει χρονολογίας και κατάστασης
        ↓
Επιλογή κατάλληλου extraction pipeline
        ↓
Έλεγχος ποιότητας εξαγόμενου κειμένου
        ↓
Chunking μόνο σε αξιόπιστο περιεχόμενο
        ↓
Embeddings / vectors
        ↓
Αποθήκευση σε PostgreSQL + pgvector
        ↓
Hybrid search: KOHA/Elasticsearch + vector search
        ↓
AI assistant με τεκμηριωμένη απάντηση και πηγές
```

Το σύστημα δεν θα θεωρεί όλα τα PDFs ισότιμα. Κάθε έγγραφο και, όπου χρειάζεται, κάθε σελίδα, θα περνά από έλεγχο καταλληλότητας πριν χρησιμοποιηθεί για semantic search.

---

## 4. Date-aware στρατηγική επεξεργασίας

Προτείνεται αρχικός διαχωρισμός των εγγράφων με βάση τη χρονολογία τους, επειδή η χρονολογία φαίνεται να αποτελεί ισχυρή ένδειξη για την ποιότητα του αρχείου.

### Α. Έγγραφα πριν το 1990

Τα έγγραφα πριν το 1990 θεωρούνται υψηλού ρίσκου για αυτόματη εξαγωγή.

Συχνά περιλαμβάνουν:

- δακτυλογραφημένο κείμενο,
- καθαρεύουσα,
- πολυτονικά ή ασυνήθιστα σημεία,
- φθαρμένες σαρώσεις,
- χειρόγραφες σημειώσεις,
- χαμηλή ποιότητα OCR.

Προτεινόμενη αντιμετώπιση:

```text
Pre-1990 documents
        ↓
Δεν γίνεται αυτόματο bulk vectorization
        ↓
Δοκιμή με ειδικό historical OCR pipeline
        ↓
Αν η ποιότητα είναι επαρκής → indexing
        ↓
Αν όχι → metadata-only / manual review / ειδικό fallback
```

Τα έγγραφα αυτά δεν αγνοούνται. Παραμένουν διαθέσιμα μέσω KOHA metadata και μπορούν να μπουν σε ουρά για ειδική επεξεργασία.

### Β. Έγγραφα 1990–2010

Τα έγγραφα αυτής της περιόδου αντιμετωπίζονται ως μεικτής ποιότητας.

Προτεινόμενη αντιμετώπιση:

```text
1990–2010 documents
        ↓
Έλεγχος text layer με PyMuPDF / pymupdf4llm
        ↓
Αν το κείμενο είναι επαρκές → extraction + indexing
        ↓
Αν όχι → OCR fallback
        ↓
Αν και το OCR αποτύχει → manual review ή metadata-only
```

### Γ. Έγγραφα μετά το 2010

Τα νεότερα έγγραφα θεωρούνται πιο κατάλληλα για πλήρη αυτόματη επεξεργασία.

Προτεινόμενη αντιμετώπιση:

```text
Post-2010 documents
        ↓
pymupdf4llm / PyMuPDF extraction
        ↓
Chunking
        ↓
Embeddings
        ↓
Vector indexing
```

Σε αυτή την κατηγορία μπορούμε να κινηθούμε πιο επιθετικά, με OCR fallback μόνο όπου το text layer δεν επαρκεί.

---

## 5. Extraction subsystem

Το extraction subsystem θα έχει πολλαπλά επίπεδα.

### 5.1 Native PDF extraction

Για καθαρά ή νεότερα PDFs:

- PyMuPDF
- pymupdf4llm

Χρήση:

```text
PDF με καλό text layer
        ↓
Εξαγωγή κειμένου / δομής
        ↓
Καθαρισμός
        ↓
Chunking
```

Αυτό είναι το προτιμώμενο path όταν το PDF έχει αξιόπιστο text layer, επειδή αποφεύγει το θόρυβο που εισάγει το OCR από σφραγίδες, περιθώρια, χειρόγραφες σημειώσεις ή σκιές.

### 5.2 OCR fallback

Για σκαναρισμένα ή προβληματικά PDFs:

- Surya OCR ως βασικός υποψήφιος OCR μηχανισμός για δοκιμή.
- EasyOCR ως εναλλακτικό benchmark.
- docTR ως επιπλέον εναλλακτική.
- Tesseract μόνο ως baseline, όχι ως τελική λύση για ιστορικά ελληνικά κείμενα.

Το OCR pipeline θα πρέπει να υποστηρίζει:

```text
render page image
        ↓
crop / cleanup / contrast enhancement
        ↓
OCR
        ↓
quality check
        ↓
accept / reject / manual review
```

### 5.3 Vision LLM fallback

Για έγγραφα όπου αποτυγχάνει το OCR, μπορεί να εξεταστεί χρήση τοπικού vision-language model μέσω Ollama ή άλλης υποδομής.

Όμως αυτό δεν πρέπει να θεωρηθεί authoritative OCR.

Ο ρόλος του vision LLM πρέπει να είναι:

- βοηθητικός,
- fallback για manual review,
- περιγραφή εικόνων/χαρτών/σκαριφημάτων,
- όχι ανεξέλεγκτη παραγωγή κειμένου για scientific indexing.

Ο λόγος είναι ότι τα vision LLMs μπορούν να παράγουν πειστικό αλλά λανθασμένο κείμενο. Για επιστημονική βιβλιοθήκη, αυτό είναι σημαντικός κίνδυνος.

---

## 6. Quality gates πριν το vectorization

Το σύστημα δεν πρέπει να δημιουργεί embeddings από οποιοδήποτε εξαγόμενο κείμενο.

Κάθε σελίδα ή chunk πρέπει να χαρακτηρίζεται ως:

```text
index_content
metadata_only
skip
manual_review
```

### index_content

Χρήση όταν το κείμενο είναι αρκετά αξιόπιστο ώστε να μπει σε full-text/vector search.

### metadata_only

Χρήση για:

- εξώφυλλα,
- πίνακες περιεχομένων,
- σελίδες με λίγη αλλά χρήσιμη πληροφορία,
- σελίδες όπου το περιεχόμενο είναι χρήσιμο ως metadata αλλά όχι ως κύριο scientific text.

### skip

Χρήση όταν η σελίδα είναι άδεια, πολύ θορυβώδης ή μη ανακτήσιμη.

### manual_review

Χρήση όταν η σελίδα φαίνεται σημαντική αλλά η ποιότητα εξαγωγής δεν είναι αρκετά αξιόπιστη.

---

## 7. Αποθήκευση δεδομένων

Προτείνεται PostgreSQL ως βασική βάση δεδομένων και pgvector για vector search.

Ενδεικτικά βασικά entities:

```text
documents
document_pages
document_chunks
document_embeddings
extraction_runs
search_logs
answer_logs
```

### documents

Περιέχει:

- ID εγγράφου,
- KOHA record ID,
- τίτλο,
- συγγραφέα,
- χρονολογία,
- keywords,
- αρχείο PDF,
- checksum,
- κατάσταση επεξεργασίας.

### document_pages

Περιέχει:

- αριθμό σελίδας,
- επιλεγμένο κείμενο,
- normalized κείμενο,
- extraction method,
- quality status,
- page action: index_content / metadata_only / skip / manual_review.

### document_chunks

Περιέχει τα τελικά αποσπάσματα που θα χρησιμοποιηθούν για αναζήτηση και απαντήσεις.

Κάθε chunk πρέπει να κρατά:

- document ID,
- page start,
- page end,
- section title αν υπάρχει,
- original text,
- normalized text,
- quality metadata.

### document_embeddings

Περιέχει:

- chunk ID,
- vector,
- embedding model,
- embedding version,
- ημερομηνία δημιουργίας.

---

## 8. Chunking και κανονικοποίηση ελληνικών

Η κανονικοποίηση πρέπει να γίνεται προσεκτικά.

Δεν πρέπει να αντικαθιστούμε το πρωτότυπο κείμενο. Πρέπει να κρατάμε δύο μορφές:

```text
original_text
normalized_text
```

Το `original_text` είναι η πηγή αλήθειας.

Το `normalized_text` χρησιμοποιείται για καλύτερη αναζήτηση και matching.

Ενδεικτική ελαφριά κανονικοποίηση:

- καθαρισμός whitespace,
- διόρθωση hyphenation σε αλλαγές γραμμής,
- Unicode normalization,
- lowercase search copy,
- πιθανή αφαίρεση τόνων για matching,
- mapping παλαιών/νέων όρων όπου υπάρχει συμφωνημένο λεξιλόγιο.

Δεν προτείνεται αρχικά πλήρης “μετάφραση” καθαρεύουσας σε νέα ελληνικά, γιατί υπάρχει κίνδυνος αλλοίωσης επιστημονικού νοήματος.

---

## 9. Keywords και controlled vocabulary

Ο υπάρχων κατάλογος keywords της βιβλιοθήκης πρέπει να χρησιμοποιηθεί ως controlled vocabulary layer.

Για κάθε document/page/chunk μπορεί να γίνεται enrichment με σχετικά keywords.

Παράδειγμα:

```text
“θερμομεταλλικαί πηγαί”
“θερμομεταλλικών πηγών”
“ιαματικά ύδατα”
```

μπορούν να συνδέονται με ένα κοινό keyword/concept.

Αυτό βοηθά ειδικά σε παλιά ελληνικά κείμενα, όπου ο χρήστης μπορεί να ψάχνει με σύγχρονους όρους αλλά το έγγραφο να περιέχει καθαρεύουσα ή παλαιότερη ορολογία.

---

## 10. Search architecture

Η αναζήτηση δεν πρέπει να βασιστεί μόνο στα vectors.

Προτείνεται hybrid search:

```text
User query
        ↓
Query analysis
        ↓
Παράλληλη αναζήτηση:
    1. KOHA / Elasticsearch metadata search
    2. Exact keyword search
    3. Vector semantic search
    4. Controlled vocabulary expansion
        ↓
Merge / rerank αποτελεσμάτων
        ↓
LLM answer generation
        ↓
Απάντηση με πηγές και σελίδες
```

Η τελική απάντηση πρέπει να περιλαμβάνει:

- σύντομη απάντηση,
- σχετικά έγγραφα,
- σελίδες,
- αποσπάσματα ή τεκμηρίωση,
- ένδειξη αβεβαιότητας όπου το OCR είναι χαμηλής ποιότητας.

---

## 11. AI assistant

Ο AI assistant δεν πρέπει να λειτουργεί ως ελεύθερο chatbot.

Πρέπει να λειτουργεί ως scientific retrieval assistant.

Βασικοί κανόνες:

```text
- Απαντά μόνο με βάση ανακτημένες πηγές.
- Δεν εφευρίσκει πληροφορίες.
- Αναφέρει έγγραφο και σελίδα.
- Όταν η ποιότητα OCR είναι χαμηλή, το δηλώνει.
- Διαχωρίζει τεκμηριωμένα ευρήματα από ερμηνεία.
- Αν δεν υπάρχουν επαρκή στοιχεία, το λέει καθαρά.
```

Η ακρίβεια και η ιχνηλασιμότητα είναι σημαντικότερες από μια “ωραία” απάντηση.

---

## 12. Προτεινόμενα στάδια υλοποίησης

### Φάση 1 — Ανάλυση αποθέματος και κατηγοριοποίηση

Στόχος:

- συλλογή metadata από KOHA,
- κατανομή εγγράφων ανά χρονολογία,
- εντοπισμός τύπων PDF,
- επιλογή αντιπροσωπευτικού δείγματος.

Παραδοτέο:

```text
Document inventory report
Date buckets
Quality buckets
Processing strategy ανά κατηγορία
```

### Φάση 2 — OCR / extraction benchmark

Στόχος:

- δοκιμή PyMuPDF / pymupdf4llm,
- δοκιμή Surya OCR,
- δοκιμή EasyOCR / docTR ως benchmark,
- αξιολόγηση σε πραγματικά έγγραφα ΕΑΓΜΕ.

Παραδοτέο:

```text
Extraction benchmark report
Προτεινόμενο extraction pipeline ανά κατηγορία εγγράφου
```

### Φάση 3 — Prototype ingestion pipeline

Στόχος:

- ingest περιορισμένου αριθμού εγγράφων,
- extraction,
- quality gates,
- chunking,
- αποθήκευση σε PostgreSQL.

Παραδοτέο:

```text
documents
pages
chunks
quality metadata
```

### Φάση 4 — Vector search prototype

Στόχος:

- δημιουργία embeddings,
- αποθήκευση σε pgvector,
- πρώτη semantic search δοκιμή,
- σύγκριση με KOHA/keyword search.

Παραδοτέο:

```text
Hybrid retrieval prototype
Search evaluation report
```

### Φάση 5 — AI assistant prototype

Στόχος:

- ερώτηση χρήστη,
- hybrid retrieval,
- παραγωγή απάντησης,
- citations,
- audit logging.

Παραδοτέο:

```text
AI assistant demo
Source-grounded answers
Query/answer logs
```

---

## 13. Τελική αρχιτεκτονική σε μία εικόνα

```text
KOHA Metadata / PDF Repository
        ↓
Document Intake
        ↓
Date-aware Classification
        ↓
Quality-aware Extraction Router
        ├── Post-2010: PyMuPDF / pymupdf4llm
        ├── 1990–2010: Native extraction + OCR fallback
        └── Pre-1990: Historical OCR / manual review / fallback
        ↓
Quality Gates
        ├── index_content
        ├── metadata_only
        ├── skip
        └── manual_review
        ↓
Text Normalization + Keyword Enrichment
        ↓
Chunking
        ↓
Embeddings
        ↓
PostgreSQL + pgvector
        ↓
Hybrid Retrieval
        ├── KOHA / Elasticsearch
        ├── Keyword Search
        ├── Vector Search
        └── Controlled Vocabulary
        ↓
LLM Answer Generator
        ↓
Τεκμηριωμένη απάντηση με πηγές, σελίδες και audit log
```

---

## 14. Κεντρική τεχνική θέση

Το έργο δεν πρέπει να παρουσιαστεί ως απλό “chatbot πάνω σε PDFs”.

Η σωστή τεχνική περιγραφή είναι:

```text
Σύστημα τεκμηριωμένης σημασιολογικής αναζήτησης
με quality-aware document extraction,
hybrid retrieval και AI assistant με πηγές.
```

Το LLM είναι το τελικό interface.

Η πραγματική αξία και δυσκολία βρίσκεται πριν από αυτό:

```text
να εξάγουμε αξιόπιστο περιεχόμενο
από ανομοιογενή, παλαιά και συχνά προβληματικά επιστημονικά PDFs.
```
