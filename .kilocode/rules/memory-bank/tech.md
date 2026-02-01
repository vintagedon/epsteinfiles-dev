# Epstein Files ARD Tech Stack

<!-- 
Purpose: Technologies, setup, constraints
Audience: AI agents needing to understand technical environment
Update Frequency: When stack changes
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
| pytesseract | Latest | OCR for images |
| spaCy | Latest | NER, entity extraction |

### Database

| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 16+ | Primary data store |
| pgvector | 0.5+ | Vector similarity search |
| pg_trgm | Built-in | Fuzzy text matching |

### ML/Embeddings

| Technology | Version | Purpose |
|------------|---------|---------|
| sentence-transformers | Latest | Text embeddings (baseline) |
| all-MiniLM-L6-v2 | - | Default embedding model |
| BGE-M3 | - | Candidate for evaluation |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| Astronomy cluster | PostgreSQL hosting, compute |
| Cloudflare | DNS, CDN for epsteinfiles.dev |
| GitHub | Version control, project management |

## Development Environment

### Prerequisites

```bash
# Python environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Core dependencies
pip install pandas polars pyarrow pdfplumber pytesseract spacy
pip install sentence-transformers psycopg2-binary pgvector

# spaCy model
python -m spacy download en_core_web_lg
```

### Environment Variables

```bash
# Database connection (cluster)
EPSTEIN_DB_HOST=<cluster-pg-host>
EPSTEIN_DB_PORT=5432
EPSTEIN_DB_NAME=epstein_ard
EPSTEIN_DB_USER=<user>
EPSTEIN_DB_PASSWORD=<password>

# Data paths
EPSTEIN_DATA_RAW=./data/raw
EPSTEIN_DATA_PROCESSED=./data/layer-0-canonical
```

### Directory Conventions

| Directory | Contents | Git Status |
|-----------|----------|------------|
| `data/raw/` | Original DOJ files | .gitignored |
| `data/layer-*/` | Processed outputs | Committed or LFS |
| `pipelines/` | Processing scripts | Committed |
| `notebooks/` | Exploration | Committed (outputs cleared) |
| `src/` | Production code | Committed |
| `scratch/` | Temporary work | .gitignored |

## Constraints

### Technical Constraints

- **File sizes:** Raw corpus could exceed Git limits; use .gitignore for raw, evaluate LFS for processed
- **Cluster resources:** Shared infrastructure; be mindful of compute/storage consumption
- **pgvector dimensions:** Currently using 1024-dim embeddings; model choice affects this

### Ethical Constraints

- **No fine-tuning:** Do not train/fine-tune generative models on this corpus
- **Redaction respect:** Honor all redactions in source documents
- **Victim protection:** Scrub/anonymize any discovered victim-identifying information
- **No commercial use:** Public interest and educational purposes only

### Data Constraints

- **Provenance required:** Every processed record must link to source file
- **Reproducibility:** Pipelines must be re-runnable from raw inputs
- **Validation gates:** Each layer transformation includes quality checks

## External Resources

### Data Sources

| Source | URL | Content |
|--------|-----|---------|
| DOJ Epstein Library | justice.gov/epstein | Official releases |
| theelderemo/Epstein-files | GitHub | Pre-processed 20K docs |
| tensonaut/EPSTEIN_FILES_20K | HuggingFace | Dataset version |
| epstein-docs.github.io | GitHub Pages | Searchable archive |

### Reference Projects

| Project | URL | Relevance |
|---------|-----|-----------|
| epstein-rag-mcp | GitHub | MCP server for RAG |
| epstein-network | GitHub | Network visualization |
| ErikVeland/epstein-archive | GitHub | Full-stack platform |

### Learning Resources

| Resource | Purpose |
|----------|---------|
| IBM RAG and Agentic AI cert | Primary learning path |
| ARD methodology repo | Layer model reference |
| Sentence-transformers docs | Embedding implementation |

## Setup Checklist

For new contributors or fresh environment:

- [ ] Clone repository
- [ ] Create Python virtual environment
- [ ] Install dependencies
- [ ] Download spaCy model
- [ ] Configure environment variables
- [ ] Verify database connectivity (if working on Layer 1+)
- [ ] Run `pipelines/validation/check_environment.py` (when created)
