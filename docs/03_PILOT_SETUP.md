# Στήσιμο Πιλοτικού Περιβάλλοντος

## 1. Repository structure

Η πιλοτική υλοποίηση ακολουθεί την παρακάτω δομή:

```text
eagme-ai-assistant/
├── backend/
│   ├── manage.py
│   ├── config/
│   ├── documents/
│   ├── search/
│   └── assistant/
├── frontend/
│   ├── package.json
│   └── src/
├── data/
│   ├── koha_exports/
│   ├── pdfs/
│   ├── page_images/
│   └── extraction_reports/
├── scripts/
│   ├── ingest_documents.py
│   ├── extract_pdf_text.py
│   ├── build_embeddings.py
│   └── evaluate_search.py
├── docker-compose.yml
├── .env.example
└── README.md
```

## 2. Services

Το πιλοτικό περιβάλλον αποτελείται από τα παρακάτω services:

| Service | Ρόλος |
|---|---|
| `postgres` | PostgreSQL με pgvector extension. |
| `backend` | Django API και management commands. |
| `worker` | Background worker για ingestion, OCR, embeddings και batch jobs. |
| `frontend` | React interface για αναζήτηση, απαντήσεις και feedback. |
| `redis` | Queue/cache για background jobs. |

## 3. `.env.example`

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=eagme_ai
POSTGRES_USER=eagme
POSTGRES_PASSWORD=eagme
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/0

OPENAI_API_KEY=
EMBEDDING_MODEL=to-be-selected
LLM_MODEL=to-be-selected

PDF_STORAGE_PATH=/app/data/pdfs
KOHA_EXPORT_PATH=/app/data/koha_exports
PAGE_IMAGE_STORAGE_PATH=/app/data/page_images
EXTRACTION_REPORT_PATH=/app/data/extraction_reports
```

Τα `EMBEDDING_MODEL` και `LLM_MODEL` είναι αποφάσεις setup. Επιλέγονται με βάση κόστος, ποιότητα, όρια χρήσης και απαιτήσεις φιλοξενίας.

## 4. `docker-compose.yml`

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./backend:/app
    command: python manage.py runserver 0.0.0.0:8000

  worker:
    build:
      context: ./backend
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
      - ./backend:/app
    command: celery -A config worker -l info

  frontend:
    build:
      context: ./frontend
    depends_on:
      - backend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
```

Απόφαση πιλοτικού setup: χρησιμοποιείται Celery για background jobs. Αν η ομάδα επιλέξει RQ ή Django management command runner, αλλάζει μόνο το `worker.command`.

## 5. Προαπαιτούμενα

Στο μηχάνημα ανάπτυξης ή στο datacenter πρέπει να υπάρχουν:

- Docker,
- Docker Compose,
- πρόσβαση στα πιλοτικά PDFs,
- KOHA export ή πρόσβαση στα αντίστοιχα metadata,
- API key για LLM/embedding provider, αν χρησιμοποιηθεί paid model,
- επαρκής χώρος αποθήκευσης για PDFs, page images και extraction reports.

## 6. Προετοιμασία φακέλων

```bash
mkdir -p data/pdfs
mkdir -p data/koha_exports
mkdir -p data/page_images
mkdir -p data/extraction_reports
```

Τοποθέτηση αρχείων:

```text
data/pdfs/               πιλοτικά PDFs
data/koha_exports/       metadata exports από KOHA
data/page_images/        rendered page images για OCR
data/extraction_reports/ reports ποιότητας extraction
```

## 7. Εκκίνηση services

```bash
cp .env.example .env
docker compose up -d --build
```

## 8. Database setup

```bash
docker compose exec postgres psql -U eagme -d eagme_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec backend python manage.py migrate
```

Αν το pgvector extension δημιουργείται από Django migration, το `psql` command αφαιρείται.

## 9. Σύμβαση management commands

Η πιλοτική υλοποίηση πρέπει να παρέχει τα παρακάτω Django management commands:

| Command | Σκοπός |
|---|---|
| `ingest_koha_export` | Εισαγωγή metadata από KOHA export. |
| `register_pdfs` | Σύνδεση PDFs με documents και υπολογισμός checksums. |
| `extract_documents` | Native extraction, OCR fallback, quality classification και extraction reports. |
| `build_embeddings` | Δημιουργία embeddings μόνο για `index_content`. |
| `evaluate_search` | Αξιολόγηση retrieval έναντι ιστορικών queries και baseline. |

## 10. Εισαγωγή metadata και PDFs

```bash
docker compose exec backend python manage.py ingest_koha_export /app/data/koha_exports/pilot_export.csv
docker compose exec backend python manage.py register_pdfs /app/data/pdfs
```

## 11. Extraction pipeline

```bash
docker compose exec backend python manage.py extract_documents --limit 100
```

Το extraction pipeline εκτελεί:

1. ανάγνωση PDF metadata,
2. προσπάθεια native text extraction,
3. OCR fallback όπου χρειάζεται,
4. quality classification,
5. αποθήκευση αποτελεσμάτων ανά σελίδα,
6. δημιουργία extraction report.

## 12. Quality gates

Κάθε σελίδα ή chunk παίρνει ένα από τα παρακάτω statuses:

```text
index_content
metadata_only
skip
manual_review
```

Μόνο records με status `index_content` χρησιμοποιούνται για embeddings.

## 13. Δημιουργία embeddings

```bash
docker compose exec backend python manage.py build_embeddings --status index_content
```

Το command αποθηκεύει:

- embedding vector,
- embedding model,
- embedding version,
- ημερομηνία δημιουργίας,
- source chunk ID.

## 14. Search evaluation

```bash
docker compose exec backend python manage.py evaluate_search /app/data/koha_exports/historical_queries.csv
```

Η αξιολόγηση συγκρίνει:

- υπάρχον baseline αναζήτησης,
- keyword/metadata retrieval,
- vector retrieval,
- hybrid retrieval.

## 15. Frontend

```bash
docker compose up -d frontend
```

Το frontend παρέχει:

- search page,
- answer page με πηγές,
- document/page citations,
- user feedback,
- admin/review page για `manual_review` και failed extractions.

