# Epstein Files ARD Tech Stack

<!-- 
Purpose: Technologies, setup, constraints
Audience: AI agents needing to understand technical environment
Update Frequency: When stack changes
Last Updated: 2026-02-01 (M05)
-->

## Core Technologies

### Data Processing

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Primary language for pipelines |
| pandas | Latest | Data manipulation |
| polars | Latest | Large file processing (if pandas too slow) |
| pyarrow | Latest | Parquet read/write |
| pdfplumber | Latest | PDF text extraction |
| probablepeople | 0.5.5+ | CRF-based name parsing |
| phonenumbers | 8.13+ | Phone normalization to E.164 |

### Database

| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 16+ | Primary data store |
| pgvector | 0.5+ | Vector similarity search |
| fuzzystrmatch | Built-in | Soundex for entity resolution blocking |

### ML/Embeddings

| Technology | Version | Purpose |
|------------|---------|---------|
| sentence-transformers | 2.2+ | Text embeddings |
| all-MiniLM-L6-v2 | 384-dim | Name embedding model (M06) |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| pgsql01 (10.25.20.8) | PostgreSQL hosting |
| Cloudflare | DNS, CDN for epsteinfiles.dev |
| GitHub | Version control, project management |

## Database Configuration

### Connection Details

```
Host: 10.25.20.8
Port: 5432
Database: epsteinfiles_ard
```

### Schemas

| Schema | Purpose |
|--------|---------|
| `core` | L0 source of truth (immutable) |
| `l1` | Layer 1 scalar transforms |
| `l2` | Layer 2 vectors (M06) |
| `l3` | Layer 3 graphs (M07) |
| `ingest` | Staging area if needed |

### Extensions Enabled

```sql
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;  -- For soundex()
CREATE EXTENSION IF NOT EXISTS vector;         -- For pgvector
```

## Development Environment

### Prerequisites

```bash
# Python environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Core dependencies (L0)
pip install pandas pdfplumber jsonschema

# L1 dependencies
pip install psycopg[binary] python-dotenv
pip install probablepeople phonenumbers python-Levenshtein

# M06+ dependencies
pip install sentence-transformers torch
```

### Environment Variables

Project `.env` file (gitignored):

```bash
# PostgreSQL Connection (pgsql01)
PGSQL_HOST=10.25.20.8
PGSQL_PORT=5432
PGSQL_USER=clusteradmin_pg01
PGSQL_PASSWORD=<from-global-env>
PGSQL_DATABASE=epsteinfiles_ard

# Processing defaults
BATCH_SIZE=1000
LOG_LEVEL=INFO
```

Global environment reference: `D:\development-environments\.global-env\.env`

### Directory Conventions

| Directory | Contents | Git Status |
|-----------|----------|------------|
| `data/raw/` | Original DOJ files | .gitignored |
| `data/layer-0-canonical/` | Cleaned CSVs, schemas | Committed |
| `pipelines/` | Processing scripts | Committed |
| `pipelines/ddl/` | Database DDL | Committed |
| `notebooks/` | Exploration | Committed (outputs cleared) |
| `src/` | Production code | Committed |
| `scratch/` | Temporary work | .gitignored |
| `research/` | GDR artifacts, analysis | Committed |

## Constraints

### Technical Constraints

- **File sizes:** Raw corpus could exceed Git limits; use .gitignore for raw
- **Cluster resources:** Shared infrastructure; be mindful of compute/storage
- **pgvector dimensions:** 384-dim for MiniLM, placeholder exists in schema

### Ethical Constraints

- **No fine-tuning:** Do not train/fine-tune generative models on this corpus
- **Redaction respect:** Honor all redactions in source documents
- **Victim protection:** `suppress_from_public` flag, K-anonymity views
- **No commercial use:** Public interest and educational purposes only

### Data Constraints

- **Provenance required:** Every L1 record links to L0 source
- **Reproducibility:** Pipelines re-runnable; DDL script in `pipelines/ddl/`
- **Validation gates:** Each layer has validation script

## Current Tables (as of M05)

### Core Schema (L0)

| Table | Records | Key |
|-------|---------|-----|
| `core.flight_logs` | 5,001 | `id` (integer) |
| `core.black_book` | 2,324 | `record_id` (uuid) |

### L1 Schema

| Table | Records | Purpose |
|-------|---------|---------|
| `l1.flight_events` | 1,491 | Deduplicated flights |
| `l1.flight_passengers` | 5,001 | Passenger instances |
| `l1.contacts` | 2,324 | Contact records |
| `l1.contact_persons` | 2,610 | Decomposed persons |
| `l1.phone_numbers` | 5,585 | Normalized phones |
| `l1.identity_mentions` | 6,783 | Entity resolution input |

## External Resources

### Data Sources

| Source | URL | Content |
|--------|-----|---------|
| DOJ Epstein Library | justice.gov/epstein | Official releases |
| Internet Archive | archive.org | Flight logs PDF |
| epsteinsblackbook.com | Wayback Machine | Black book scans |

### Reference Projects

| Project | URL | Relevance |
|---------|-----|-----------|
| ARD methodology repo | local | Layer model reference |
| GDR research | `research/gdr-artifacts/` | Schema architecture |

### Learning Resources

| Resource | Purpose |
|----------|---------|
| IBM RAG and Agentic AI cert | Primary learning path |
| Sentence-transformers docs | Embedding implementation |

## Setup Checklist

For new contributors or fresh environment:

- [ ] Clone repository
- [ ] Create Python virtual environment
- [ ] Install dependencies (see Prerequisites)
- [ ] Copy `.env` from template (configure credentials)
- [ ] Verify database connectivity: `psql -h 10.25.20.8 -d epsteinfiles_ard`
- [ ] Run validation: `python pipelines/validation/validate_l1.py`
