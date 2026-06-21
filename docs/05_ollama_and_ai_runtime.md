# Ollama And AI Runtime

## Σκοπός

Το παρόν κείμενο εξηγεί τι είναι το `Ollama`, γιατί προτείνεται για το `PoC`, πώς εντάσσεται στη βασική ροή του συστήματος και ποια τοπικά models είναι λογικό να χρησιμοποιηθούν στην πρώτη φάση.

Στόχος δεν είναι να παρουσιαστεί το `Ollama` ως γενική πλατφόρμα τεχνητής νοημοσύνης, αλλά να αποσαφηνιστεί ο πολύ συγκεκριμένος ρόλος του μέσα στο πιλοτικό περιβάλλον.

Η αρχιτεκτονική θέση του `Ollama` μέσα στο `PoC` παρουσιάζεται συνοπτικά στο [03_poc_architecture.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/03_poc_architecture.md), ενώ εδώ αναλύεται η λειτουργική του χρήση ως local runtime.

## Τι είναι το Ollama

Το `Ollama` είναι local runtime για γλωσσικά μοντέλα και embedding models.

Με απλά λόγια:

- εγκαθίσταται σε server ή `VM`
- κατεβάζει τα επιλεγμένα models τοπικά
- εκθέτει ένα τοπικό API
- επιτρέπει στο backend του `PoC` να καλεί models χωρίς να στέλνει δεδομένα σε εξωτερικό cloud

Άρα, αντί να γίνεται κλήση σε εξωτερικό provider για κάθε embedding ή answer request, η εφαρμογή επικοινωνεί με το τοπικό `Ollama` service.

Χρήσιμες επίσημες πηγές:

- Linux install: [https://ollama.com/download/linux](https://ollama.com/download/linux)
- Model library: [https://ollama.com/library](https://ollama.com/library)
- Embedding models: [https://ollama.com/blog/embedding-models](https://ollama.com/blog/embedding-models)
- API docs: [https://github.com/ollama/ollama/blob/main/docs/api.md](https://github.com/ollama/ollama/blob/main/docs/api.md)

## Γιατί προτείνεται στο PoC

Για την πιλοτική φάση, το `Ollama` είναι πρακτική πρώτη επιλογή γιατί:

- δεν απαιτεί cloud API χρέωση ανά request
- μπορεί να τρέξει μέσα στην υποδομή της ΕΑΓΜΕ
- επιτρέπει local-only δοκιμή της βασικής ροής
- είναι αρκετό για να αξιολογηθεί αν η συνολική λογική του pipeline λειτουργεί

Χρειάζεται όμως μία σαφής διευκρίνιση:

το `Ollama` δεν είναι "χωρίς κόστος" συνολικά. Απλώς μεταφέρει το κόστος από τα εξωτερικά API calls σε:

- υπολογιστικούς πόρους του pilot server
- χρόνο επεξεργασίας
- λειτουργική συντήρηση του τοπικού runtime

Για το `PoC`, αυτή η ανταλλαγή είναι αποδεκτή, επειδή ο βασικός στόχος είναι να δοκιμαστεί η λύση τοπικά και ελεγχόμενα.

## Πού χρησιμοποιείται στο PoC

Στο `PoC`, το `Ollama` προτείνεται να χρησιμοποιηθεί σε δύο πολύ συγκεκριμένα σημεία:

1. για παραγωγή embeddings
2. για answer generation πάνω σε ήδη ανακτημένο context

Δεν χρησιμοποιείται για extraction, OCR ή retrieval από μόνο του.

## Χρήση για embeddings

Αφού ολοκληρωθούν:

- η εξαγωγή κειμένου
- ο ποιοτικός έλεγχος
- η επιλογή των σελίδων που είναι κατάλληλες για indexing
- το chunking

το backend στέλνει κάθε αποδεκτό chunk στο embedding endpoint του `Ollama`.

Το `Ollama` επιστρέφει έναν embedding vector, ο οποίος αποθηκεύεται στη `PostgreSQL` με `pgvector`.

Η πρακτική ροή είναι η εξής:

```text
selected page text
  ↓
chunk creation
  ↓
embedding request προς Ollama
  ↓
vector response
  ↓
storage στη PostgreSQL / pgvector
```

Αργότερα, όταν ο χρήστης γράψει query:

- το query γίνεται embedding με το ίδιο embedding model
- γίνεται vector similarity search
- βρίσκονται τα πιο σχετικά chunks

Αυτό σημαίνει ότι το `Ollama` συμμετέχει και στη live αναζήτηση, αλλά μόνο στο βήμα της μετατροπής του query σε vector. Η επιλογή των αποτελεσμάτων, η ταξινόμηση και η επιστροφή τους προς τον χρήστη παραμένουν ευθύνη του backend και της βάσης.

Ενδεικτικό embedding request:

```bash
curl http://localhost:11434/api/embed -d '{
  "model": "nomic-embed-text",
  "input": "Υδρογεωλογική μελέτη της περιοχής..."
}'
```

## Χρήση για answer generation

Το answer model δεν ψάχνει μόνο του στη βάση.

Πρώτα το σύστημα:

- βρίσκει σχετικά chunks
- επιλέγει το κατάλληλο context
- κρατά τις πηγές που θα συνοδεύσουν την απάντηση

και μόνο μετά στέλνει στο `Ollama`:

- το user query
- τα σχετικά αποσπάσματα
- τις αναφορές σε έγγραφο και σελίδα

Η πρακτική ροή είναι:

```text
user query
  ↓
retrieval
  ↓
selected chunks + source references
  ↓
request προς Ollama answer model
  ↓
τεκμηριωμένη απάντηση
```

Είναι σημαντικό να ξεχωρίζει ότι υπάρχουν δύο διαφορετικά τελικά modes:

- `search mode`
  - επιστρέφονται σχετικά τεκμήρια ή αποσπάσματα χωρίς σύνθεση απάντησης
- `assistant mode`
  - τα ήδη ανακτημένα αποσπάσματα στέλνονται στο answer model για σύντομη τεκμηριωμένη απάντηση

Άρα το answer model δεν αποτελεί εναλλακτική του retrieval. Αποτελεί δεύτερο στρώμα πάνω από αυτό.

Ενδεικτικό generation request:

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:8b",
  "messages": [
    {
      "role": "user",
      "content": "Με βάση τα παρακάτω αποσπάσματα, απάντησε και ανέφερε την πηγή."
    }
  ],
  "stream": false
}'
```

## Τι δεν κάνει το Ollama στο PoC

Το `Ollama` δεν αναλαμβάνει:

- PDF extraction
- OCR
- quality scoring
- chunking
- vector storage
- retrieval orchestration

Αυτά υλοποιούνται από τα υπόλοιπα components του `PoC`, κυρίως από το backend, τα processing services και τη βάση.

Άρα ο σωστός τρόπος να το σκεφτόμαστε είναι:

- το `Ollama` είναι local AI runtime
- δεν είναι ολόκληρο το σύστημα αναζήτησης

## Προτεινόμενα αρχικά models

Για το `PoC`, προτείνεται να υπάρχει ένας καθαρός αρχικός συνδυασμός:

### Για embeddings

Αρχική επιλογή:

- `nomic-embed-text`

Προαιρετική εναλλακτική για comparison:

- `mxbai-embed-large`

### Για answer generation

Αρχική επιλογή:

- `qwen3:8b`

Εναλλακτικό model για comparison:

- `llama3.1:8b`

Η λογική εδώ είναι συντηρητική:

- μία βασική embedding επιλογή
- ένα βασικό answer model
- μία εναλλακτική για συγκριτική δοκιμή, όχι πλήθος models από την αρχή

## Τι προτείνεται να μην κλειδώσει από τώρα

Στην πρώτη φάση δεν χρειάζεται να κλειδώσουν οριστικά:

- το τελικό answer model
- η τελική στρατηγική fallback
- το αν το answer generation θα μείνει πάντα local
- το αν αργότερα θα χρειαστεί hybrid επιλογή

Αυτό που χρειάζεται να αποδειχθεί πρώτα είναι ότι:

- το local embedding flow δουλεύει σταθερά
- το vector retrieval επιστρέφει χρήσιμο context
- το local answer generation είναι αρκετό για πιλοτική αξιολόγηση

## Τι είναι χρήσιμο να ληφθεί υπόψη από την Ομάδα Πληροφορικής

Στην πράξη, είναι χρήσιμο να ληφθεί υπόψη ότι το `Ollama` στο `PoC` θα χρησιμοποιηθεί κυρίως για:

- embedding batch jobs
- query embeddings
- περιορισμένες δοκιμές answer generation

Δεν μιλάμε σε αυτή τη φάση για βαριά παραγωγική χρήση με μεγάλους ταυτόχρονους φόρτους.

Αυτό σημαίνει ότι η υποδομή είναι σκόπιμο να εξασφαλίζει:

- σταθερό local service
- επαρκή `RAM`
- επαρκή αποθηκευτικό χώρο για models
- σωστή εσωτερική συνδεσιμότητα ανάμεσα στο backend και το `Ollama`

## Αν η ποιότητα των local answers δεν είναι αρκετή

Αν διαπιστωθεί ότι η ποιότητα του local answer model δεν είναι επαρκής, δεν χρειάζεται να αλλάξει όλο το σύστημα.

Η ασφαλής fallback πορεία είναι:

- να παραμείνουν local το extraction pipeline
- να παραμείνουν local τα embeddings
- να παραμείνει local το `pgvector`
- και να αλλάξει μόνο το answer generation layer

Αυτό επιτρέπει να προστατευθεί η βασική αρχιτεκτονική του `PoC`, χωρίς να εξαρτάται η όλη λύση από μία μόνο επιλογή answer model.

## Συμπέρασμα

Για το `PoC`, το `Ollama` είναι η προτεινόμενη local AI runtime επιλογή γιατί επιτρέπει:

- τοπική παραγωγή embeddings
- τοπική answer generation
- έλεγχο της βασικής ροής χωρίς εξωτερική API εξάρτηση
- πειραματισμό με μικρό αριθμό μοντέλων σε ελεγχόμενο περιβάλλον

Η βασική προτεινόμενη αρχική κατεύθυνση είναι:

- `nomic-embed-text` για embeddings
- `qwen3:8b` για answer generation

Αυτό αρκεί για να δοκιμαστεί η ουσία του `PoC`, χωρίς να προστεθεί άσκοπη πολυπλοκότητα από το πρώτο βήμα.
