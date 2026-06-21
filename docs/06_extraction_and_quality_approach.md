# Extraction And Quality Approach

## Σκοπός

Το παρόν κείμενο περιγράφει τη λογική με την οποία το `PoC` θα:

- εξάγει κείμενο από τα `PDF`
- αποφασίζει πότε αρκεί το native text layer και πότε χρειάζεται `OCR`
- αξιολογεί την ποιότητα του αποτελέσματος
- αποφασίζει τι μπορεί να περάσει σε embeddings και τι όχι

Ο στόχος δεν είναι να οριστεί από την αρχή ο τέλειος μηχανισμός για κάθε κατηγορία τεκμηρίων. Ο στόχος είναι να οριστεί μια σταθερή και ελέγξιμη πρώτη προσέγγιση για το pilot.

Η αρχιτεκτονική θέση αυτού του pipeline μέσα στο `PoC` παρουσιάζεται στο [03_poc_architecture.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/03_poc_architecture.md), ενώ οι απαιτήσεις υποδομής και περιβάλλοντος στο [04_poc_setup_and_requirements.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/04_poc_setup_and_requirements.md).

## Βασική αρχή

Η βασική αρχή του `PoC` είναι η εξής:

```text
Δεν οδηγούμε σε embeddings οποιοδήποτε extracted text.
```

Πριν από τη σημασιολογική ευρετηρίαση, το περιεχόμενο πρέπει να έχει περάσει έναν ελάχιστο έλεγχο ποιότητας. Με αυτόν τον τρόπο αποφεύγεται να χτιστεί η αναζήτηση πάνω σε ασταθές ή θορυβώδες κείμενο.

## Συνολική ροή

Η προτεινόμενη ροή του pilot είναι η παρακάτω:

```text
PDF intake και document registration
  ↓
Native text extraction ανά σελίδα
  ↓
Page-level quality checks στο native αποτέλεσμα
  ↓
OCR fallback όπου χρειάζεται
  ↓
Normalization και νέα αξιολόγηση ποιότητας
  ↓
Page classification ανά status
  ↓
Chunking μόνο για indexable περιεχόμενο
  ↓
Selection για embeddings
```

Η λογική αυτή επιτρέπει να δουλεύουμε σε επίπεδο σελίδας και όχι μόνο σε επίπεδο εγγράφου. Αυτό είναι σημαντικό, γιατί σε πολλά τεκμήρια συνυπάρχουν καθαρές και προβληματικές σελίδες.

Με άλλα λόγια, το `PoC` είναι εξ ορισμού page-centric. Δεν θεωρούμε ότι ένα `PDF` είναι συνολικά καλό ή συνολικά κακό. Το ίδιο τεκμήριο μπορεί να περιλαμβάνει σελίδες που πρέπει να περάσουν σε `index_content`, σελίδες που είναι μόνο `metadata_only` και σελίδες που χρειάζονται `manual_review` ή `skip`. Για αυτό και η αποθήκευση, η αξιολόγηση και η τελική απόφαση πρέπει να γίνονται ανά σελίδα.

## 1. Native text extraction ως πρώτη διαδρομή

Η πρώτη προσπάθεια extraction γίνεται από το υπάρχον text layer του `PDF`.

Η λογική αυτή επιλέγεται γιατί:

- είναι ταχύτερη
- διατηρεί συχνά καλύτερα τη δομή του κειμένου
- αποφεύγει περιττό `OCR` όταν το κείμενο είναι ήδη αξιοποιήσιμο

Για το pilot, η native extraction είναι η προεπιλογή και το `OCR` λειτουργεί ως fallback, όχι ως καθολική πρώτη λύση.

Εργαλεία που προτείνεται να χρησιμοποιηθούν σε αυτή τη φάση:

- `PyMuPDF` (`fitz`) ως βασικό εργαλείο native extraction
- προαιρετικά `pymupdf4llm` για comparison σε επιλεγμένα δείγματα

Πιο συγκεκριμένα, η προτεινόμενη default επιλογή για το `PoC` είναι:

- `PyMuPDF` για την πρώτη προσπάθεια extraction
- όχι `pymupdf4llm` ως βασική διαδρομή παραγωγής
- `pymupdf4llm` μόνο για comparison σε benchmark pages

Ενδεικτική εγκατάσταση:

```bash
pip install pymupdf pymupdf4llm
```

Ενδεικτική εκτέλεση:

```bash
python manage.py extract_documents --limit 100
```

Ενδεικτική λογική μέσα σε `Django` command:

```python
import fitz

doc = fitz.open(pdf_path)
page = doc[page_index]
native_text = page.get_text("text")
```

## 2. Πότε ενεργοποιείται OCR fallback

Το `OCR` ενεργοποιείται όταν υπάρχουν σαφείς ενδείξεις ότι το native extraction δεν είναι αρκετό.

Ενδεικτικές περιπτώσεις:

- η σελίδα επιστρέφει σχεδόν άδειο κείμενο
- το κείμενο έχει εξαιρετικά λίγους χαρακτήρες σε σχέση με το ορατό περιεχόμενο
- υπάρχουν πολλές ακολουθίες θορύβου ή σπασμένων tokens
- η σελίδα φαίνεται να είναι image-based scan
- το αποτέλεσμα είναι εμφανώς μη αναγνώσιμο για χρήση σε retrieval

Στο pilot, ο στόχος δεν είναι να εξαντληθούν όλοι οι δυνατοί `OCR` δρόμοι, αλλά να επιβεβαιωθεί μια αξιόπιστη βασική fallback λογική.

Εργαλεία που προτείνεται να αξιολογηθούν:

- `Tesseract OCR` ως baseline OCR επιλογή
- `Surya OCR` ως βασικός υποψήφιος για βελτιωμένο fallback
- `EasyOCR` ως εναλλακτική για comparison
- `docTR` ως εναλλακτική για comparison

Η πιο συγκεκριμένη πρώτη οδηγία είναι:

- native extraction με `PyMuPDF`
- fallback `OCR` με `Tesseract`
- προαιρετικό preprocessing εικόνας με `OpenCV`
- δεύτερη φάση comparison με `Surya OCR`, `EasyOCR` ή `docTR`

Ενδεικτική εγκατάσταση baseline OCR stack σε `Ubuntu / Debian`:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-ell
pip install pytesseract pillow opencv-python
```

Έλεγχος ότι το `Tesseract` και το ελληνικό language pack είναι διαθέσιμα:

```bash
tesseract --version
tesseract --list-langs
```

Στη λίστα γλωσσών πρέπει να εμφανίζεται το `ell`.

## 3. Τι ελέγχεται σε επίπεδο σελίδας

Η ποιότητα δεν κρίνεται γενικά και αόριστα. Για κάθε σελίδα εξετάζονται βασικά signals που δείχνουν αν το αποτέλεσμα είναι αξιοποιήσιμο.

Ενδεικτικά:

- ποσότητα κειμένου
- αναγνωσιμότητα λέξεων
- παρουσία ελληνικών χαρακτήρων όπου αυτό αναμένεται
- ποσοστό θορύβου ή άχρηστων συμβόλων
- συνοχή της διάταξης του κειμένου
- ενδείξεις ότι πρόκειται για καθαρό κείμενο, πίνακα, χάρτη ή άλλη ειδική περίπτωση

Η αξιολόγηση αυτή δεν χρειάζεται να είναι απόλυτα σύνθετη στην πρώτη φάση. Αρκεί να είναι επαναλήψιμη και να οδηγεί σε λογικές αποφάσεις.

Σε πρακτικό επίπεδο, το extraction step πρέπει να καταγράφει τουλάχιστον:

- `document_id`
- `page_number`
- `extraction_method`
- `char_count`
- `word_count`
- `quality_score`
- `quality_status`
- `needs_ocr`

Στο `PoC` είναι χρήσιμο να καταγράφονται και:

- `greek_chars`
- `latin_chars`
- `ocr_confidence`
- `noise_tokens`
- `readability_index`

Ενδεικτική λογική normalization που μπορεί να μεταφερθεί σε utility module του `Django` backend:

```python
import re
import unicodedata

def normalize_for_search(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip().lower()
```

## 4. Λειτουργική απόφαση ανά σελίδα

Για να είναι η ροή επαναλήψιμη, η απόφαση δεν πρέπει να μένει σε γενικές εκτιμήσεις. Σε κάθε σελίδα το σύστημα πρέπει να ακολουθεί την ίδια βασική λογική:

```text
1. Extract native text
2. Measure page-level signals
3. Αν το native result είναι ανεπαρκές, τρέχει OCR fallback
4. Συγκρίνει native και OCR αποτέλεσμα
5. Επιλέγει το καλύτερο διαθέσιμο κείμενο
6. Αποδίδει quality_status
7. Μόνο αν το status είναι index_content συνεχίζει σε chunking και embeddings
```

Σε πρακτικό επίπεδο, η λογική μπορεί να αποτυπωθεί ως εξής:

```python
native_text = extract_native_text(page)
native_metrics = measure_quality(native_text)

if should_run_ocr(native_metrics):
    ocr_text = run_ocr(page_image)
    ocr_metrics = measure_quality(ocr_text)
    final_text, final_metrics, extraction_method = select_best_result(
        native_text,
        native_metrics,
        ocr_text,
        ocr_metrics,
    )
else:
    final_text = native_text
    final_metrics = native_metrics
    extraction_method = "native"

quality_status = assign_quality_status(final_metrics)
```

Το σημαντικό εδώ είναι ότι:

- το `OCR` δεν τρέχει υποχρεωτικά σε κάθε σελίδα
- το τελικό κείμενο της σελίδας δεν είναι πάντα το native result
- η απόφαση για indexing λαμβάνεται μετά την τελική επιλογή κειμένου και όχι νωρίτερα

## 5. Quality score και quality status

Για το pilot είναι χρήσιμο να υπάρχει ένας απλός μηχανισμός quality scoring που να οδηγεί σε σαφές quality status.

Η ακριβής μαθηματική διατύπωση μπορεί να προσαρμοστεί στην πορεία, αλλά το σύστημα πρέπει να μπορεί να καταλήγει τουλάχιστον στις παρακάτω καταστάσεις:

- `index_content`
- `metadata_only`
- `manual_review`
- `skip`

Η λογική τους είναι η εξής:

### `index_content`

Η σελίδα ή το chunk έχει αρκετά καθαρό και αναγνώσιμο κείμενο ώστε να χρησιμοποιηθεί για embeddings και σημασιολογική αναζήτηση.

### `metadata_only`

Υπάρχει πληροφορία που αξίζει να κρατηθεί στο επίπεδο metadata ή βασικής περιγραφής, αλλά όχι κείμενο αρκετά αξιόπιστο για semantic indexing.

### `manual_review`

Η σελίδα φαίνεται σημαντική, αλλά το αποτέλεσμα είναι οριακό ή αμφίβολο. Σε αυτή την περίπτωση δεν απορρίπτεται αυτόματα, αλλά οδηγείται σε ελεγχόμενο review.

### `skip`

Το αποτέλεσμα είναι υπερβολικά φτωχό, θορυβώδες ή άσχετο για retrieval, οπότε δεν προχωρά στο επόμενο στάδιο.

Σε λειτουργικό επίπεδο, η λογική είναι:

```text
page text -> quality signals -> quality score -> quality status
```

Στην αρχική αξιολόγηση και στο πρώτο benchmark είναι χρήσιμο να χρησιμοποιούνται rule-based metrics όπως:

- `char_count`
- `word_count`
- `greek_chars`
- `latin_chars`
- `weird_chars` ή `noise_tokens`
- `ocr_confidence`
- `readability_index`

Άρα η πιο πρακτική οδηγία για το `PoC` είναι:

- να ξεκινήσει με `rule-based scoring`
- να μη στηθεί από την αρχή πιο σύνθετο `ML` quality model
- να ρυθμιστούν τα thresholds αφού τρέξει το πρώτο benchmark

## 6. Ειδικές περιπτώσεις

Δεν αναμένονται όλες οι σελίδες να συμπεριφέρονται ως συνεχές επιστημονικό κείμενο.

Στο pilot πρέπει να λαμβάνονται υπόψη και ειδικές κατηγορίες όπως:

- εξώφυλλα
- πίνακες περιεχομένων
- βιβλιογραφίες
- χάρτες και γεωλογικές τομές
- σελίδες με κυρίως πίνακες
- σελίδες με περιορισμένο ή μηδενικό συνεκτικό κείμενο

Σε αρκετές από αυτές τις περιπτώσεις, η σωστή απόφαση δεν είναι απαραίτητα το `index_content`, αλλά το `metadata_only` ή το `manual_review`.

## 7. Από τη σελίδα στο chunk

Η απόφαση δεν σταματά στη σελίδα. Αφού ολοκληρωθεί το page-level filtering, ακολουθεί chunking.

Σε αυτό το στάδιο, ο στόχος είναι:

- να ομαδοποιηθεί μόνο το αξιόπιστο περιεχόμενο
- να μην περάσουν σε embeddings chunks που βασίζονται κυρίως σε θορυβώδες ή οριακό κείμενο

Στο pilot, το πρακτικό κριτήριο είναι απλό:

- embeddings δημιουργούνται μόνο για περιεχόμενο που έχει επαρκή ποιότητα
- περιεχόμενο με status `manual_review` ή `skip` δεν περνά αυτόματα σε vector index

### Βασική στρατηγική chunking για το PoC

Στην πρώτη φάση, το chunking δεν χρειάζεται να είναι υπερβολικά σύνθετο. Χρειάζεται όμως να είναι σταθερό, επαναλήψιμο και να προστατεύει την ιχνηλασιμότητα του περιεχομένου.

Η προτεινόμενη βασική λογική είναι η εξής:

- chunking μόνο πάνω σε `normalized_text` που έχει ήδη εγκριθεί για indexing
- διατήρηση αναφοράς σε `document`, `page` και `chunk_index`
- αποφυγή δημιουργίας chunks που ανακατεύουν αποσπάσματα από διαφορετικές σελίδες στην πρώτη φάση
- αποφυγή υπερβολικά μικρών chunks που δεν έχουν αρκετό νοηματικό περιεχόμενο
- αποφυγή υπερβολικά μεγάλων chunks που δυσκολεύουν το retrieval και θολώνουν την πηγή

Με άλλα λόγια, για το `PoC` προτιμάται συντηρητική στρατηγική chunking με έμφαση στην καθαρότητα και όχι στην επιθετική συμπίεση του περιεχομένου.

### Τι πρέπει να κρατά κάθε chunk

Για να μπορεί το retrieval και το answer layer να επιστρέφουν πραγματικά τεκμηριωμένο αποτέλεσμα, κάθε chunk πρέπει να διατηρεί τουλάχιστον:

- αναφορά στο τεκμήριο προέλευσης
- αναφορά στη σελίδα προέλευσης
- αύξοντα αριθμό `chunk_index`
- το αρχικό ή επιλεγμένο κείμενο του chunk
- το `normalized_text` που χρησιμοποιείται για embedding

Αυτό είναι κρίσιμο γιατί το retrieval δεν πρέπει να επιστρέφει απλώς "σχετικό κείμενο". Πρέπει να επιστρέφει σχετικό κείμενο που μπορεί να συνδεθεί ξανά με τη σωστή πηγή.

### Πρακτική πολιτική boundaries

Στο `PoC`, η πιο ασφαλής αρχική επιλογή είναι:

- chunking ανά σελίδα
- όχι ενοποίηση περιεχομένου από πολλές σελίδες στο ίδιο chunk
- προαιρετικό μικρό overlap μόνο αν φανεί ότι κόβονται συστηματικά ενιαίες παράγραφοι ή ενότητες

Η λογική αυτής της επιλογής είναι ότι:

- απλοποιεί τον έλεγχο της πηγής
- μειώνει τον κίνδυνο να χαθεί η σωστή σελιδοαναφορά
- διευκολύνει το manual review όπου χρειάζεται
- ταιριάζει καλύτερα στη σημερινή ωριμότητα του `PoC`

Αν αργότερα το pilot δείξει ότι η page-level προσέγγιση είναι υπερβολικά αυστηρή, μπορεί να εξεταστεί πιο ώριμη πολιτική chunk overlap ή section-based chunking.

### Τι πρέπει να αποφεύγεται

Στο πρώτο `PoC` είναι προτιμότερο να αποφεύγονται:

- chunks που περιέχουν κυρίως τίτλους χωρίς σώμα κειμένου
- chunks που ενώνονται μηχανικά από οριακές σελίδες
- chunks που αναμειγνύουν καθαρό κείμενο με θορυβώδη ή αμφίβολα αποσπάσματα
- chunks χωρίς σαφή provenance σε τεκμήριο και σελίδα

Η βασική αρχή παραμένει:

```text
καλύτερα λιγότερα αλλά καθαρά και ιχνηλάσιμα chunks
παρά περισσότερα αλλά αμφίβολα embeddings
```

Ενδεικτική εκτέλεση:

```bash
python manage.py build_embeddings --status index_content
```

Ενδεικτική προετοιμασία embedding service:

```bash
ollama pull nomic-embed-text
```

Η πιο συγκεκριμένη υλοποίηση των πεδίων `DocumentChunk` και της σχέσης τους με τα embeddings αποτυπώνεται στα εσωτερικά technical notes, κυρίως στο [poc_implementation_notes/django_models_outline.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/poc_implementation_notes/django_models_outline.md).

## 8. Πού παραμένει ο ανθρώπινος έλεγχος

Η ανθρώπινη παρέμβαση δεν είναι ο κύριος τρόπος λειτουργίας του pipeline. Παραμένει μόνο εκεί όπου η αυτόματη απόφαση δεν είναι αρκετά ασφαλής.

Ενδεικτικά:

- σε σελίδες με οριακή ποιότητα
- σε σημαντικά τεκμήρια με αμφίβολο extraction
- σε περιπτώσεις όπου το native extraction και το `OCR` δίνουν πολύ διαφορετικά αποτελέσματα
- σε ειδικές κατηγορίες σελίδων που δεν είναι εύκολο να ταξινομηθούν σωστά αυτόματα

Στόχος είναι το pilot να βρει τη σωστή ισορροπία:

- όσο το δυνατόν περισσότερος αυτοματισμός
- όσο το δυνατόν λιγότερο review
- χωρίς να θυσιάζεται η ποιότητα του retrieval

## 9. Τι θα μετρηθεί στο pilot

Για να αξιολογηθεί αν η προσέγγιση λειτουργεί, το pilot πρέπει να απαντήσει πρακτικά στα εξής:

- ποια extraction μέθοδος λειτουργεί καλύτερα ανά τύπο `PDF`
- πότε αρκεί το native text layer
- πότε χρειάζεται `OCR`
- ποιο ποσοστό των σελίδων οδηγείται σε `index_content`
- ποιο ποσοστό οδηγείται σε `manual_review`
- αν τα chunks που τελικά μπαίνουν σε embeddings είναι πράγματι αναγνώσιμα και χρήσιμα

Η αξιολόγηση αυτή δεν γίνεται θεωρητικά. Βασίζεται σε αντιπροσωπευτικό δείγμα εγγράφων και σελίδων από το pilot dataset.

Στο benchmark είναι χρήσιμο να καταγράφονται τουλάχιστον:

- method
- page type
- readability
- fidelity
- retrieval usefulness
- proposed status

Για το αρχικό benchmark, οι συγκεκριμένες μέθοδοι είναι:

1. `PyMuPDF` native extraction
2. `pymupdf4llm`
3. `Tesseract OCR` πάνω σε raw rendered page
4. `OpenCV preprocessing -> Tesseract OCR`

Και προαιρετικά:

5. `Surya OCR`
6. `EasyOCR`
7. `docTR`

## 10. Ρόλος του benchmark και του sample review

Για την πρώτη ρύθμιση του pipeline, είναι χρήσιμο να προηγηθεί μικρό benchmark σε περιορισμένο αριθμό σελίδων και εγγράφων.

Αυτό βοηθά να επιβεβαιωθούν:

- η default extraction μέθοδος
- η default `OCR` fallback μέθοδος
- η πρώτη λογική quality thresholds
- οι περιπτώσεις που πρέπει να οδηγούνται σε review

Αντίστοιχα, ο χειροκίνητος έλεγχος σε αντιπροσωπευτικές σελίδες δεν έχει στόχο να αντικαταστήσει τον αυτοματισμό. Έχει στόχο να βαθμονομήσει σωστά την αρχική λογική του συστήματος.

Μια συγκεκριμένη πρακτική οδηγία για την Ομάδα Πληροφορικής είναι η εξής:

- να κρατηθούν 3 έως 5 benchmark αρχεία
- να εξεταστούν 20 έως 30 σελίδες συνολικά
- να υπάρχουν και εύκολα και δύσκολα παραδείγματα
- να περιλαμβάνονται σελίδες με καθαρό native text
- να περιλαμβάνονται σελίδες που απαιτούν `OCR`
- να περιλαμβάνονται οριακές ή χαμηλής ποιότητας περιπτώσεις
- να περιλαμβάνονται και ειδικές σελίδες, όπως εξώφυλλα ή πίνακες περιεχομένων

## 11. Τι δεν χρειάζεται να κλειδώσει από τώρα

Στην πρώτη φάση δεν χρειάζεται να κλειδώσουν οριστικά:

- ο τέλειος `OCR` engine
- η τελική φόρμουλα του score
- όλα τα thresholds
- κάθε ειδική περίπτωση δύσκολου περιεχομένου

Αρκεί να υπάρχει:

- καθαρή βασική ροή
- σταθερή λογική fallback
- σαφής διάκριση ανάμεσα σε indexable και μη indexable content
- ελεγχόμενος ανθρώπινος έλεγχος όπου πραγματικά χρειάζεται

## Συγκεκριμένα εργαλεία και εντολές

Για την πρώτη υλοποίηση του pilot προτείνεται η εξής βάση:

- native extraction με `PyMuPDF`
- `OCR` fallback με `Tesseract`
- προαιρετικό preprocessing με `OpenCV`
- comparison με `Surya OCR`, `EasyOCR` ή `docTR`
- embeddings μέσω `Ollama`
- vector storage σε `PostgreSQL / pgvector`

Οι βασικές λειτουργικές εντολές που πρέπει να υπάρχουν είναι οι εξής:

```bash
python manage.py ingest_koha_export /app/data/koha_exports/pilot_export.csv
python manage.py register_pdfs /app/data/pdfs
python manage.py extract_documents --limit 100
python manage.py score_extraction_quality --limit 100
python manage.py build_embeddings --status index_content
```

Τα ακριβή command names μπορεί να αλλάξουν στην τελική υλοποίηση, αλλά οι παραπάνω λειτουργίες πρέπει να καλύπτονται με σαφή και επαναλήψιμο τρόπο.

Αν η πρώτη φάση τρέξει πιο πρακτικά από terminal και όχι μόνο μέσω `Django`, η ελάχιστη ακολουθία είναι:

```bash
tesseract --version
tesseract --list-langs
ollama list
python benchmark_extraction_reference.py --input-dir /app/data/pdfs --output-dir /app/data/extraction_reports
python extract_candidates_reference.py --input-dir /app/data/pdfs --output-json /app/data/extraction_reports/candidates.json
python score_extraction_reference.py --input-json /app/data/extraction_reports/candidates.json --output-json /app/data/extraction_reports/scored.json
python report_extraction_reference.py --input-json /app/data/extraction_reports/scored.json --output-dir /app/data/extraction_reports/final
```

Η παρούσα ενότητα εστιάζει στη λειτουργική λογική του pipeline. Για το πού και με ποιες υπηρεσίες θα τρέξουν αυτά στο πιλοτικό περιβάλλον, βλ. [04_poc_setup_and_requirements.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/04_poc_setup_and_requirements.md).
