# API Response Contract

## Σκοπός

Το παρόν σημείωμα ορίζει την ελάχιστη λογική του response contract ανάμεσα στο backend του `PoC` και στη διεπαφή χρήστη.

Δεν αποτελεί πλήρες `OpenAPI` specification ούτε τελικό serializer design. Στόχος του είναι να αποσαφηνίσει:

- ποια βασικά response modes πρέπει να υποστηρίζονται
- ποια πεδία πρέπει να επιστρέφονται με σταθερό τρόπο
- πώς ξεχωρίζουν τα search results από την τεκμηριωμένη answer response
- ποιο είναι το ελάχιστο explanatory context που πρέπει να φτάνει στη διεπαφή

## Βασική αρχή

Το `PoC` δεν πρέπει να επιστρέφει μόνο:

- έναν τίτλο τεκμηρίου
- ή μία απάντηση χωρίς συμφραζόμενα

Πρέπει να επιστρέφει αποτέλεσμα που να επιτρέπει στον χρήστη να καταλάβει:

- τι βρέθηκε
- γιατί θεωρήθηκε σχετικό
- από ποια πηγή προέρχεται
- και, όπου υπάρχει απάντηση, πάνω σε ποια αποσπάσματα στηρίζεται

## Response modes

Για την πρώτη φάση, αρκεί να θεωρήσουμε δύο βασικά response modes:

### 1. `search`

Το σύστημα επιστρέφει κυρίως:

- σχετικά τεκμήρια
- αποσπάσματα ή chunks
- references σε έγγραφο και σελίδα

Δεν απαιτείται σε αυτό το mode να υπάρχει συνθετική answer summary.

### 2. `assistant`

Το σύστημα επιστρέφει:

- σύντομη τεκμηριωμένη answer summary
- supporting snippets
- references σε έγγραφο και σελίδα

Η answer summary πρέπει να βασίζεται μόνο σε ήδη ανακτημένο context.

## Κοινά πεδία

Ανεξάρτητα από το mode, το response πρέπει να μπορεί να μεταφέρει τουλάχιστον τα εξής:

- `mode`
- `query_text`
- `results_count`
- `response_time_ms`, όπου είναι διαθέσιμο
- `results` ή `supporting_chunks`
- references σε `document_id` και `page`

Αν το backend δεν μπορεί να επιστρέψει τουλάχιστον αυτά με σταθερό τρόπο, η διεπαφή θα δυσκολευτεί να παρουσιάσει ελέγξιμο και συνεπές αποτέλεσμα.

## Προτεινόμενο ελάχιστο search response

Το `search response` καλό είναι να περιλαμβάνει:

- ordered results
- βασικά metadata για κάθε αποτέλεσμα
- snippet ή chunk text
- score ή rank indicator
- source type, όπου αυτό είναι χρήσιμο

Ενδεικτική μορφή:

```json
{
  "mode": "search",
  "query_text": "υδρογεωλογική μελέτη λαυρίου",
  "results_count": 2,
  "results": [
    {
      "document_id": "DOC001",
      "title": "Υδρογεωλογική μελέτη περιοχής Λαυρίου",
      "page": 12,
      "snippet": "Η μελέτη αναφέρει ότι...",
      "score": 0.84,
      "source_type": "semantic"
    },
    {
      "document_id": "DOC014",
      "title": "Γεωλογικά δεδομένα Αττικής",
      "page": 3,
      "snippet": "Στην περιοχή Λαυρίου...",
      "score": 0.67,
      "source_type": "metadata"
    }
  ]
}
```

## Προτεινόμενο ελάχιστο assistant response

Το `assistant response` καλό είναι να περιλαμβάνει:

- answer summary
- supporting chunks
- τις ίδιες βασικές αναφορές πηγής που θα χρειαζόταν και το search mode

Ενδεικτική μορφή:

```json
{
  "mode": "assistant",
  "query_text": "τι αναφέρεται για την υδρογεωλογία του Λαυρίου;",
  "answer_summary": "Οι σχετικές μελέτες αναφέρουν ότι...",
  "supporting_chunks": [
    {
      "document_id": "DOC001",
      "title": "Υδρογεωλογική μελέτη περιοχής Λαυρίου",
      "page": 12,
      "snippet": "Η μελέτη αναφέρει ότι...",
      "score": 0.84
    },
    {
      "document_id": "DOC014",
      "title": "Γεωλογικά δεδομένα Αττικής",
      "page": 3,
      "snippet": "Στην περιοχή Λαυρίου...",
      "score": 0.67
    }
  ]
}
```

## Τι πρέπει να παραμένει σταθερό

Για να υπάρχει καθαρός συντονισμός ανάμεσα σε backend και UI, είναι χρήσιμο να μείνουν σταθερά τουλάχιστον τα εξής:

- το `mode`
- το `document_id`
- το `title`
- το `page`
- το `snippet`
- ένα βασικό `score` ή rank indicator

Ακόμη και αν αργότερα αλλάξουν τα endpoints ή οι serializers, αυτά τα πεδία είναι καλό να θεωρούνται ο ελάχιστος σταθερός πυρήνας του contract.

## Σχέση με το hybrid retrieval

Στην πρώτη φάση δεν χρειάζεται το response να εξηγεί όλη την εσωτερική λογική ranking. Είναι όμως χρήσιμο να μπορεί, όπου χρειάζεται, να δείχνει αν ένα αποτέλεσμα προήλθε κυρίως από:

- `metadata`
- `semantic`
- ή μεταγενέστερα από `hybrid`

Αυτό βοηθά:

- στο debugging
- στην αξιολόγηση
- και στη μελλοντική βελτίωση της πολιτικής συγχώνευσης αποτελεσμάτων

## Τι δεν χρειάζεται να κλειδώσει από τώρα

Στην πρώτη φάση δεν χρειάζεται να κλειδώσουν οριστικά:

- τα τελικά endpoint URLs
- η ακριβής ονομασία όλων των πεδίων
- η πλήρης δομή ενός μελλοντικού public API
- advanced pagination ή faceting

Αυτό που χρειάζεται να κλειδώσει είναι το ελάχιστο νόημα του response και η σαφής διάκριση ανάμεσα σε:

- `search results`
- `assistant answer`
- `supporting evidence`

## Σχέση με τα υπόλοιπα implementation notes

Το παρόν αρχείο απαντά κυρίως στο ερώτημα:

- `τι shape πρέπει να έχει το αποτέλεσμα προς τη διεπαφή`

Συμπληρώνει τα εξής:

- `django_project_structure.md`
  - πού ανήκουν τα `search` και `ai_runtime` services
- `django_models_outline.md`
  - ποια μοντέλα κρατούν chunks, embeddings και query logs
- `django_commands_mapping.md`
  - ποια commands σχετίζονται με evaluation και αναζήτηση

## Current recommendation

Για το `PoC`, η πιο σωστή πρακτική είναι:

- ένα απλό αλλά σταθερό `search response`
- ένα απλό αλλά τεκμηριωμένο `assistant response`
- κοινή λογική references και snippets και στα δύο

Αυτό αρκεί για να υπάρχει καθαρό handoff ανάμεσα σε backend και διεπαφή, χωρίς να προστεθεί πρόωρα περιττή πολυπλοκότητα.
