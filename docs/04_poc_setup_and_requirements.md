# PoC Setup And Requirements

## Σκοπός

Το παρόν κείμενο περιγράφει τι ακριβώς χρειάζεται να στηθεί για το πιλοτικό περιβάλλον του έργου.

Δεν επαναλαμβάνει την αρχιτεκτονική λογική του `PoC`, αλλά τη μεταφράζει σε πρακτικές απαιτήσεις υποδομής, εγκατάστασης και πρόσβασης.

Στόχος του είναι να απαντά με πρακτικό τρόπο:

- ποια σημεία είναι χρήσιμο να συμφωνηθούν με την Ομάδα Πληροφορικής της ΕΑΓΜΕ
- ποια υποδομή χρειάζεται
- ποια βασικά τεχνολογικά στοιχεία πρέπει να είναι διαθέσιμα
- ποια δεδομένα και ποιες προσβάσεις απαιτούνται πριν ξεκινήσει το `PoC`

Η αρχιτεκτονική του `PoC` παρουσιάζεται στο [03_poc_architecture.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/03_poc_architecture.md). Εδώ η ίδια λογική μετατρέπεται σε συγκεκριμένες οδηγίες υποδομής, deployment και readiness checks.

Στην παρούσα φάση, η Ομάδα Πληροφορικής της ΕΑΓΜΕ έχει τον βασικό ρόλο στο στήσιμο και την υλοποίηση του πιλοτικού περιβάλλοντος, με δική μας υποστήριξη και τεχνική καθοδήγηση όπου χρειάζεται.

Άρα το παρόν κείμενο λειτουργεί ως συγκεκριμένη λίστα οδηγιών και ενεργειών για το στήσιμο του περιβάλλοντος.

## Τι πρέπει να μπορεί να αποδείξει το πιλοτικό περιβάλλον

Το πιλοτικό περιβάλλον πρέπει να επιτρέπει την εκτέλεση της βασικής ροής του έργου:

```text
KOHA export + pilot PDFs
  ↓
ingestion
  ↓
text extraction / OCR fallback
  ↓
quality gating
  ↓
chunking + embeddings
  ↓
search query
  ↓
retrieval
  ↓
τεκμηριωμένο αποτέλεσμα
```

Με απλά λόγια, το περιβάλλον πρέπει να μας επιτρέπει να κάνουμε μία αναζήτηση και να λαμβάνουμε ένα χρήσιμο αποτέλεσμα με σαφή αναφορά σε πηγή.

## Τι προτείνεται να στηθεί από την Ομάδα Πληροφορικής της ΕΑΓΜΕ

Προτείνεται η Ομάδα Πληροφορικής της ΕΑΓΜΕ να διαμορφώσει ένα pilot environment στο οποίο να μπορεί να εκτελεστεί η πλήρης βασική ροή του `PoC`.

Συγκεκριμένα, προτείνεται να έχουν ολοκληρωθεί τα εξής:

- provision ενός pilot server ή `VM`
- εγκατάσταση και έλεγχος `Docker` και `Docker Compose`
- εγκατάσταση `PostgreSQL` με ενεργό `pgvector`
- εγκατάσταση και λειτουργία `Ollama` ως local service
- προετοιμασία storage paths για αρχεία, metadata exports και reports
- τοποθέτηση του πιλοτικού dataset στο προβλεπόμενο storage
- εξασφάλιση export metadata από το `KOHA`
- παροχή πρόσβασης της ομάδας εργασίας στο περιβάλλον
- βασική λειτουργική υποστήριξη του pilot

Το ζητούμενο δεν είναι υποδομή παραγωγικής λειτουργίας, αλλά λειτουργικό και επαναλήψιμο περιβάλλον δοκιμών.

## Συγκεκριμένα βήματα στησίματος

Η προτεινόμενη ακολουθία εργασιών είναι η εξής:

1. Provision server ή `VM`.
2. Εγκατάσταση λειτουργικού περιβάλλοντος για containers.
3. Εγκατάσταση `PostgreSQL` και ενεργοποίηση `pgvector`.
4. Εγκατάσταση `Ollama`.
5. Δημιουργία storage paths και έλεγχος δικαιωμάτων πρόσβασης.
6. Τοποθέτηση των πιλοτικών `PDF` και του `KOHA` export στις σωστές τοποθεσίες.
7. Επιβεβαίωση ότι το περιβάλλον είναι προσβάσιμο από την ομάδα εργασίας.
8. Επιβεβαίωση ότι μπορούν να εκτελεστούν οι βασικές batch και search ροές.

Σε πρακτικό επίπεδο, μετά από κάθε βήμα είναι χρήσιμο να υπάρχει και ένας σύντομος έλεγχος επιβεβαίωσης, ώστε να μην μείνει το validation όλο για το τέλος.

## Υποδομή

Για το `PoC`, η προτεινόμενη βάση υποδομής είναι:

- `Ubuntu Linux VM`
- `12 vCPU`
- `64 GB RAM`
- `1 TB SSD`
- χωρίς `GPU` στην πρώτη φάση

Ελάχιστη αποδεκτή βάση για περιορισμένο pilot:

- `8 vCPU`
- `32 GB RAM`
- `500 GB SSD`

Η παραπάνω διάσταση θεωρείται επαρκής για:

- φόρτωση και διαχείριση του πιλοτικού συνόλου
- extraction workflow
- `OCR` όπου χρειάζεται
- τοπικά embeddings
- `pgvector`
- περιορισμένες δοκιμές answer generation

Για να υπάρχει κοινή εικόνα για το περιβάλλον, είναι χρήσιμο να δηλωθούν ρητά:

- ποιο μηχάνημα ή `VM` διατέθηκε
- ποιο λειτουργικό χρησιμοποιείται
- ποια είναι η διαθέσιμη μνήμη, οι `CPU` και ο διαθέσιμος δίσκος
- πού θα φιλοξενηθούν τα αρχεία του pilot

## Βασικά τεχνολογικά στοιχεία

Στο pilot περιβάλλον πρέπει να είναι διαθέσιμα:

- `Docker`
- `Docker Compose`
- `PostgreSQL`
- `pgvector`
- `Ollama`
- `curl` και βασικά shell εργαλεία

Προαιρετικά:

- `Redis`, αν επιλεγεί worker queue

Σε επίπεδο εφαρμογής, η βασική λογική του `PoC` υποθέτει:

- backend σε `Python / Django`
- δυνατότητα execution batch εργασιών
- storage για metadata exports, `PDF`, reports και, αν χρειαστεί, προσωρινά page images

Σε αυτό το βήμα είναι χρήσιμο να επιβεβαιωθεί ότι:

- το `Docker` τρέχει κανονικά
- το `PostgreSQL` είναι προσβάσιμο
- το `pgvector` είναι ενεργό
- το `Ollama` απαντά σε τοπικά requests

Ενδεικτικοί έλεγχοι από terminal:

```bash
docker --version
docker compose version
psql --version
ollama --version
curl http://localhost:11434/api/tags
```

Ειδικά για τη βάση, πρέπει να μπορεί να επιβεβαιωθεί και η ενεργοποίηση του `pgvector`:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

και στη συνέχεια:

```sql
\dx
```

ώστε να εμφανίζεται η επέκταση `vector`.

## Προτεινόμενο deployment pattern για το PoC

Για το `PoC`, η πιο πρακτική και επαρκής επιλογή είναι όλες οι βασικές υπηρεσίες να φιλοξενηθούν στον ίδιο server, με εσωτερική διάκριση σε services, ports και application routes.

Η λογική αυτή μειώνει την πολυπλοκότητα της πρώτης εγκατάστασης και είναι συμβατή με το μέγεθος του πιλοτικού συνόλου.

Στην προτεινόμενη πρώτη διάταξη:

- ένας `Ubuntu VM` φιλοξενεί όλο το `PoC`
- το `Django` backend και το frontend ανήκουν στην ίδια εφαρμογή
- η βάση `PostgreSQL` παραμένει εσωτερική υπηρεσία
- το `Ollama` παραμένει εσωτερική υπηρεσία
- ο χρήστης βλέπει ένα μόνο βασικό entry point

Πρακτικά, αυτό σημαίνει ότι δεν χρειάζονται ξεχωριστά public domains για κάθε component του `PoC`.

## Public και internal services

Στην πρώτη φάση είναι προτιμότερο να ξεχωρίζουν καθαρά:

- ό,τι είναι public ή user-facing
- ό,τι είναι internal και χρησιμοποιείται μόνο από το backend ή από διαχειριστές

Η προτεινόμενη λογική είναι η εξής:

### Public entry point

- ένα βασικό web entry point για τη διεπαφή αναζήτησης
- προαιρετικά στο ίδιο entry point εκτίθενται και τα `API` routes του backend

Ενδεικτικά:

- `/`
- `/search`
- `/api/search`
- `/api/assistant`
- `/admin`

### Internal services

Οι παρακάτω υπηρεσίες καλό είναι να μην εκτίθενται δημόσια στο internet:

- `PostgreSQL`
- `Ollama`
- batch / worker processes
- εσωτερικά storage mounts

Η πρόσβαση σε αυτά πρέπει να γίνεται:

- είτε μόνο από `localhost`
- είτε μόνο από το εσωτερικό δίκτυο του server ή του container network

## Ενδεικτική διάταξη υπηρεσιών και ports

Η παρακάτω διάταξη είναι ενδεικτική και επαρκής για το `PoC`:

- `Nginx` ή αντίστοιχος reverse proxy στη `80/443`
- `Django` application server στη `8000`
- `Ollama` στη `11434`
- `PostgreSQL` στη `5432`

Αν χρησιμοποιηθεί `Redis` αργότερα για queues:

- `Redis` στη `6379`

Η βασική σύσταση είναι:

- μόνο ο reverse proxy να είναι public
- οι υπόλοιπες υπηρεσίες να είναι internal-only

## Ενδεικτική χαρτογράφηση ρόλων

Μια πρακτική χαρτογράφηση για το `PoC` είναι η εξής:

- `https://poc-host/` -> διεπαφή αναζήτησης χρήστη
- `https://poc-host/api/search` -> retrieval endpoint
- `https://poc-host/api/assistant` -> assistant endpoint
- `https://poc-host/admin` -> διαχειριστική πρόσβαση
- `http://127.0.0.1:11434` -> `Ollama`
- `127.0.0.1:5432` -> `PostgreSQL`

Αν δεν χρησιμοποιηθεί public DNS name στο πρώτο στάδιο, η ίδια λογική μπορεί να ισχύσει και με:

- `http://<server-ip>/`
- `http://<server-ip>/api/search`
- `http://<server-ip>/api/assistant`

## Τι σημαίνει αυτό για τα domain names

Για το `PoC`, δεν είναι απαραίτητο να οριστούν πολλά ξεχωριστά domains ή subdomains.

Η πιο απλή και καθαρή προσέγγιση είναι:

- ένα hostname ή ένα IP-based entry point για τους χρήστες
- paths για τα επιμέρους web endpoints
- internal ports για τις μη public υπηρεσίες

Άρα, για την πιλοτική φάση, ο διαχωρισμός προτείνεται να γίνει κυρίως:

- με `routes` για το web επίπεδο
- με `ports` για τις εσωτερικές υπηρεσίες

και όχι με πολλαπλά εξωτερικά domain names.

## Σχέση με το υφιστάμενο `library.eagme.gr`

Στην πιλοτική φάση, το νέο περιβάλλον δεν χρειάζεται να αντικαταστήσει ή να μεταβάλει το υφιστάμενο `library.eagme.gr`.

Η προτεινόμενη λογική είναι:

- το `library.eagme.gr` να παραμείνει το υφιστάμενο περιβάλλον `KOHA / OPAC`
- το `PoC` να λειτουργήσει ως ξεχωριστό pilot endpoint
- το `PoC` να αξιοποιεί export από το `KOHA`, χωρίς άμεση παρέμβαση στο production URL

Ως βασική πρόταση hostname για το πιλοτικό περιβάλλον προτείνεται:

- `ai.library.eagme.gr`

Το όνομα αυτό έχει το πλεονέκτημα ότι:

- συνδέεται καθαρά με τη βιβλιοθήκη
- αποτυπώνει ότι πρόκειται για το AI layer
- μπορεί να παραμείνει χρήσιμο και μετά το `PoC`, αν η λύση ωριμάσει

Σε περίπτωση που η ΕΑΓΜΕ θελήσει πιο σαφή διάκριση πιλοτικού χαρακτήρα, μπορεί εναλλακτικά να χρησιμοποιηθεί πιο προσωρινό hostname, όπως:

- `ai-poc.library.eagme.gr`

Για την παρούσα φάση, όμως, η βασική πρόταση είναι το:

- `ai.library.eagme.gr`

ώστε:

- το υφιστάμενο `library.eagme.gr` να παραμείνει σταθερό
- το `PoC` να είναι εύκολα αναγνωρίσιμο
- να υπάρχει καθαρός διαχωρισμός ανάμεσα στο production catalog και στο pilot AI environment

## Storage και πρόσβαση

Πρέπει να προβλεφθούν φάκελοι ή mounts για:

- `pdfs`
- `koha_exports`
- `extraction_reports`
- `page_images`, εφόσον χρησιμοποιηθούν προσωρινά για `OCR`, debugging ή review

Η λογική είναι να υπάρχουν διακριτές τοποθεσίες για:

- τα πρωτογενή αρχεία
- τα metadata
- τα ενδιάμεσα artifacts επεξεργασίας
- τα reports που θα χρειαστούν για έλεγχο και αξιολόγηση

Η ελάχιστη αναμενόμενη δομή είναι η εξής:

```text
/pilot-data/pdfs
/pilot-data/koha_exports
/pilot-data/extraction_reports
/pilot-data/page_images
```

Αν χρησιμοποιηθούν διαφορετικά paths, αυτά πρέπει να καταγραφούν ρητά.

Για να αποφευχθούν προβλήματα δικαιωμάτων, είναι χρήσιμο τα paths αυτά να είναι από την αρχή γνωστά και σταθερά τόσο για την εφαρμογή όσο και για τις batch εργασίες.

## Δεδομένα και προσβάσεις

Πριν ξεκινήσει το `PoC`, πρέπει να είναι διαθέσιμα:

- το πιλοτικό σύνολο περίπου `100` τεκμηρίων
- export metadata από το `KOHA`
- όπου είναι εφικτό, baseline στοιχεία ή ιστορικά queries
- όπου είναι διαθέσιμα, η υφιστάμενη λίστα keywords ή άλλο βασικό βιβλιοθηκονομικό βοηθητικό υλικό

Η ελάχιστη απαίτηση δεδομένων είναι να μπορούμε να συνδέσουμε:

- metadata
- αρχεία `PDF`
- βασική αναζήτηση πάνω στο επεξεργασμένο περιεχόμενο

Χωρίς αυτά, δεν μπορεί να κλείσει η βασική λειτουργική αλυσίδα του pilot.

Πιο συγκεκριμένα, η προετοιμασία δεδομένων του `PoC` χρειάζεται να καλύπτει τουλάχιστον τα εξής:

- παραλαβή του pilot συνόλου `PDF`
- παραλαβή του αντίστοιχου export μεταδεδομένων από το `KOHA`
- ύπαρξη σταθερού αναγνωριστικού που να επιτρέπει σύνδεση ανάμεσα σε bibliographic record και αρχείο
- βασικό πίνακα αντιστοίχισης `PDF -> metadata`, αν αυτό δεν προκύπτει άμεσα από το naming
- αρχικό έλεγχο πληρότητας, ώστε να φανεί ποια αρχεία έχουν κανονικό match και ποια παραμένουν unmatched

Σε πρακτικό επίπεδο, πριν περάσουμε στο ingestion, είναι χρήσιμο να μπορεί να απαντηθεί με σαφήνεια:

- πόσα `PDF` παραλήφθηκαν συνολικά
- πόσα ανοίγουν κανονικά
- πόσα έχουν έγκυρη αντιστοίχιση με metadata
- πόσα χρειάζονται χειροκίνητη διόρθωση σε ονομασία, mapping ή bibliographic link

Είναι χρήσιμο να αποτυπωθεί:

- πού βρίσκονται τα `PDF`
- πού βρίσκεται το `KOHA` export
- πού βρίσκεται τυχόν mapping file ή βοηθητικό inventory του pilot
- ποιος έχει πρόσβαση στο pilot environment
- αν υπάρχουν baseline στοιχεία ή αν αυτό θα ακολουθήσει σε επόμενο βήμα

Η βασική λογική είναι ότι το `PoC` δεν ξεκινά απλώς από ένα folder με αρχεία, αλλά από ένα ελάχιστα ελεγμένο και τεκμηριωμένο dataset εισόδου.

## Τι πρέπει να εγκατασταθεί στο pilot server

Το πιλοτικό περιβάλλον πρέπει να περιλαμβάνει τουλάχιστον:

- `Docker`
- `Docker Compose`
- `PostgreSQL` με `pgvector`
- `Ollama` ως local service

Για το `Ollama`, στην πρώτη φάση προτείνεται να υπάρχουν διαθέσιμα:

- ένα embedding model
- ένα answer model

Ενδεικτικά:

- `nomic-embed-text`
- `qwen3:8b`

Αυτό αρκεί για να λειτουργήσει η βασική τοπική ροή embeddings και answer generation χωρίς εξάρτηση από εξωτερικό `API`.

Η αναλυτική εξήγηση του ρόλου του `Ollama`, των model categories και των ενδεικτικών API κλήσεων δίνεται στο [05_ollama_and_ai_runtime.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/05_ollama_and_ai_runtime.md).

Μετά την εγκατάσταση, είναι χρήσιμο να επιβεβαιωθεί ότι:

- το `Ollama` service τρέχει
- τα models έχουν κατέβει επιτυχώς
- μπορεί να γίνει τουλάχιστον ένα embedding test
- μπορεί να γίνει τουλάχιστον ένα answer generation test

Ενδεικτικές εντολές:

```bash
ollama pull nomic-embed-text
ollama pull qwen3:8b
ollama list
curl http://localhost:11434/api/embed -d '{
  "model": "nomic-embed-text",
  "input": "δοκιμαστικό κείμενο"
}'
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:8b",
  "messages": [{"role": "user", "content": "Απάντησε με μία λέξη: λειτουργεί;"}],
  "stream": false
}'
```

## Τι πρέπει να μπορεί να κάνει το περιβάλλον μετά το setup

Σε λειτουργικό επίπεδο, το pilot περιβάλλον πρέπει να υποστηρίζει:

- εισαγωγή metadata από `KOHA` export
- σύνδεση metadata με τα πιλοτικά `PDF`
- καταχώριση document registry με σταθερά ids και βασικά file properties
- εκτέλεση text extraction
- `OCR` fallback όπου απαιτείται
- βασική ταξινόμηση ποιότητας
- δημιουργία chunks
- δημιουργία embeddings
- αποθήκευση vectors
- βασική αναζήτηση
- επιστροφή αποτελέσματος με αναφορά σε έγγραφο και σελίδα

Για να είναι αυτό απολύτως σαφές: στο `PoC` τα vector embeddings δεν προβλέπεται να αποθηκευτούν σε ξεχωριστό vector database. Η αποθήκευση θα γίνεται στην ίδια βάση `PostgreSQL`, με ενεργή την επέκταση `pgvector`. Δηλαδή κάθε chunk που εγκρίνεται για indexing θα αποκτά το embedding του μέσα σε πίνακα της ίδιας βάσης, ώστε η retrieval λογική να εκτελεί vector similarity search απευθείας εκεί.

Δεν είναι αναγκαίο σε αυτή τη φάση να υπάρχει πλήρες production interface. Αρκεί ένα απλό interface ή test endpoint που να επιτρέπει δοκιμές της πλήρους ροής.

Η αναλυτική περιγραφή του extraction pipeline, των quality gates, της λογικής σελίδας προς chunk και των quality statuses περιγράφεται ξεχωριστά στο [06_extraction_and_quality_approach.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/06_extraction_and_quality_approach.md).

## Βασικές λειτουργικές ικανότητες του PoC

Για να είναι το pilot χρήσιμο, πρέπει να υπάρχουν τουλάχιστον οι εξής λογικές δυνατότητες:

- ingestion metadata
- document registration
- extraction pipeline
- quality gating
- embeddings generation
- search / retrieval
- review flow για τις οριακές περιπτώσεις

Ειδικά για τη φάση `document registration`, το περιβάλλον πρέπει να μπορεί τουλάχιστον να:

- διαβάζει το `KOHA` export
- διαβάζει τον φάκελο των `PDF`
- δημιουργεί μοναδική εγγραφή `Document` για κάθε αρχείο
- αποθηκεύει `document_id`, filename, path, checksum, mime type και, όπου είναι διαθέσιμο, page count
- συνδέει το `Document` με το σωστό metadata record ή να το επισημαίνει ως unmatched
- ξεχωρίζει τεκμήρια `ready_for_extraction` από τεκμήρια που χρειάζονται πρώτα διόρθωση στο mapping

Με άλλα λόγια, το ingestion δεν είναι απλή αντιγραφή αρχείων στο storage. Είναι η φάση στην οποία το pilot αποκτά την πρώτη εσωτερική registry των τεκμηρίων του.

Σε επίπεδο λειτουργικού αποτελέσματος, το σύστημα πρέπει να μπορεί να ξεχωρίζει τουλάχιστον:

- `index_content`
- `metadata_only`
- `manual_review`
- `skip`

Μόνο το περιεχόμενο που περνά ως κατάλληλο για indexing πρέπει να οδηγείται σε embeddings. Η ακριβής λογική με την οποία αποδίδονται τα παραπάνω statuses δεν ορίζεται εδώ, αλλά στο [06_extraction_and_quality_approach.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/06_extraction_and_quality_approach.md).

Η πρακτική ακολουθία είναι:

```text
selected page text
  ↓
chunk creation
  ↓
embedding generation μέσω Ollama
  ↓
αποθήκευση vector στη PostgreSQL / pgvector
  ↓
vector similarity retrieval
```

Η παραπάνω ακολουθία περιγράφει τι πρέπει να μπορεί να υποστηρίξει το περιβάλλον. Η αρχιτεκτονική της ροής δίνεται στο [03_poc_architecture.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/03_poc_architecture.md), ενώ οι λεπτομέρειες για το embedding runtime στο [05_ollama_and_ai_runtime.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/05_ollama_and_ai_runtime.md).

Για την υλοποίηση της registration λογικής σε `Django`, τα πιο σχετικά εσωτερικά σημειώματα είναι:

- [poc_implementation_notes/django_commands_mapping.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/poc_implementation_notes/django_commands_mapping.md)
- [poc_implementation_notes/django_models_outline.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/poc_implementation_notes/django_models_outline.md)

## Ενδεικτική πρώτη δοκιμή end-to-end

Αφού ολοκληρωθεί το βασικό setup, είναι χρήσιμο να μπορεί να εκτελεστεί μια πρώτη δοκιμή με σαφή σειρά ενεργειών:

```bash
python manage.py ingest_koha_export /app/data/koha_exports/pilot_export.csv
python manage.py register_pdfs /app/data/pdfs
python manage.py extract_documents --limit 100
python manage.py score_extraction_quality --limit 100
python manage.py build_embeddings --status index_content
```

Αν η πρώτη υλοποίηση γίνει πιο πρακτικά από terminal scripts, μπορεί να χρησιμοποιηθεί και η αντίστοιχη reference ροή:

```bash
python extract_candidates_reference.py --input-dir /app/data/pdfs --output-json /app/data/extraction_reports/candidates.json
python score_extraction_reference.py --input-json /app/data/extraction_reports/candidates.json --output-json /app/data/extraction_reports/scored.json
python report_extraction_reference.py --input-json /app/data/extraction_reports/scored.json --output-dir /app/data/extraction_reports/final
```

Η παραπάνω δοκιμή δείχνει την ελάχιστη λειτουργική σειρά ενεργειών του περιβάλλοντος. Η ανάλυση των επιμέρους βημάτων extraction και scoring βρίσκεται στο [06_extraction_and_quality_approach.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/docs/06_extraction_and_quality_approach.md), ενώ τα σχετικά scripts αναφοράς βρίσκονται στον φάκελο [reference_scripts/README.md](/Users/stelios/Documents/Hartis/ΕΑΓΜΕ/eagme-ai-assistant/reference_scripts/README.md).

Στο τέλος της δοκιμής, πρέπει να είναι εφικτό να γίνει τουλάχιστον ένα query και να επιστραφεί αποτέλεσμα με αναφορά σε τεκμήριο και σελίδα.

## Τι δεν είναι απαραίτητο στο πρώτο PoC

Στο πρώτο στάδιο δεν είναι απαραίτητα:

- πλήρες production `UI`
- πλήρης αυτοματοποίηση για όλο το corpus
- τέλεια επεξεργασία όλων των παλαιών ή προβληματικών εγγράφων
- πλήρης υποστήριξη χαρτών και σύνθετου οπτικού υλικού
- τέλειο `OCR` για όλο το ιστορικό αρχείο

Ο στόχος του `PoC` είναι να αποδείξει ότι η βασική λειτουργική αλυσίδα στέκεται σε πραγματικά δεδομένα, όχι να εξαντλήσει από την πρώτη φάση όλες τις δύσκολες περιπτώσεις.

## Ελάχιστο λειτουργικό αποτέλεσμα

Το `PoC` θεωρείται λειτουργικά επαρκές όταν:

- έχουν τοποθετηθεί στο περιβάλλον περίπου `100` τεκμήρια
- έχουν φορτωθεί τα βασικά metadata
- έχει εκτελεστεί extraction pipeline
- έχει παραχθεί αξιοποιήσιμο κείμενο για ουσιαστικό μέρος του δείγματος
- έχουν δημιουργηθεί embeddings για το κατάλληλο περιεχόμενο
- μπορεί να εκτελεστεί αναζήτηση
- το αποτέλεσμα επιστρέφεται με σαφή τεκμηρίωση

Αυτό είναι το ελάχιστο σημείο στο οποίο το pilot παύει να είναι απλό τεχνικό setup και γίνεται πραγματικό εργαλείο αξιολόγησης του έργου.

## Checklist επιβεβαίωσης

Πριν ξεκινήσει η πρώτη πλήρης δοκιμή, είναι χρήσιμο να έχει επιβεβαιωθεί ότι ισχύουν τα παρακάτω:

- υπάρχει διαθέσιμος server ή `VM`
- έχουν εγκατασταθεί `Docker` και `Docker Compose`
- λειτουργεί `PostgreSQL` με `pgvector`
- λειτουργεί `Ollama`
- υπάρχουν διαθέσιμα τα απαιτούμενα local models
- έχουν δημιουργηθεί τα storage paths
- έχουν τοποθετηθεί το `KOHA` export και τα πιλοτικά `PDF`
- υπάρχει πρόσβαση της ομάδας εργασίας στο περιβάλλον
- μπορεί να εκτελεστεί η πρώτη πλήρης δοκιμαστική ροή

Από πλευράς ΕΑΓΜΕ, το βασικό ζητούμενο είναι:

- υποδομή
- πρόσβαση στα δεδομένα
- βασικές τεχνολογικές εγκαταστάσεις
- στοιχειώδης λειτουργική υποστήριξη

Αν αυτά εξασφαλιστούν, τότε το πιλοτικό μπορεί να αποδείξει στην πράξη αν η προτεινόμενη αρχιτεκτονική και η λογική επεξεργασίας μπορούν να στηρίξουν την επόμενη φάση του έργου.
