# Epstein Files ARD Architecture

<!-- 
Purpose: High-level structural decisions
Audience: AI agents needing to understand how the project is organized
Update Frequency: When structure changes
Last Updated: 2026-02-01
-->

## System Architecture

### ARD Layer Model

The project follows the Analysis Ready Dataset layer model, informed by GDR "Forensic Lakehouse" architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Graphs                                            │
│  Entity resolution, relationship typing, co-occurrence      │
│  Query: "Who appears in both flight logs and black book?"   │
│  Implementation: Recursive CTEs, materialized views         │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Vectors                                           │
│  Embeddings, similarity search, semantic clustering         │
│  Query: "Documents similar to this one"                     │
│  Implementation: pgvector, HNSW indexes                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Scalars                                           │
│  Entity extraction, doc classification, temporal markers    │
│  Query: "All flight logs mentioning person X in 2005"       │
│  Implementation: probablepeople, normalized PostgreSQL      │
├─────────────────────────────────────────────────────────────┤
│  Layer 0: Canonical                                         │
│  Deduplicated, cleaned, uniform schema, provenance          │
│  Query: "Give me all records from source file Y"            │
│  Implementation: CSV with JSON Schema validation            │
├─────────────────────────────────────────────────────────────┤
│  Raw: Source Files                                          │
│  DOJ releases, original formats, checksums                  │
│  Implementation: data/raw/ (gitignored)                     │
└─────────────────────────────────────────────────────────────┘
```

Each layer builds on the one below. Embeddings (Layer 2) over enriched features (Layer 1) capture more meaning than embeddings over raw text alone.

### PostgreSQL Schema Organization (L1+)

Per GDR architecture, PostgreSQL uses three schemas:

| Schema | Purpose | Contents |
|--------|---------|----------|
| `ingest` | Staging area | JSONB-heavy, permissive validation |
| `core` | Source of truth | Strict referential integrity, normalized |
| `analytics` | Query optimization | Materialized views, graph edges |

### Repository Structure

```
epsteinfiles-dev/
├── data/
│   ├── raw/                    # Original files (gitignored)
│   ├── layer-0-canonical/      # Cleaned, schema'd outputs
│   │   ├── flight-logs.csv     # 5,001 records
│   │   ├── black-book.csv      # 2,324 records
│   │   └── schema/             # JSON Schema definitions
│   ├── layer-1-scalars/        # Derived quantities
│   ├── layer-2-vectors/        # Embeddings
│   └── layer-3-graphs/         # Relationship structures
├── pipelines/
│   ├── ingestion/              # Acquisition scripts
│   ├── processing/             # Layer transformations
│   │   ├── extract_flight_logs.py
│   │   └── normalize_black_book.py
│   └── validation/             # Quality checks
│       └── validate_l0_schemas.py
├── notebooks/                  # Exploratory analysis
├── src/                        # Production code (API, web)
├── docs/
│   ├── case-study/             # ARD methodology documentation
│   ├── ethics/                 # Data handling guidelines
│   └── documentation-standards/
├── research/
│   ├── gdr-artifacts/          # GDR prompts and outputs
│   └── source-analysis/        # Provenance documentation
└── [standard scaffolding]
```

### Data Flow

```
Source URLs ──► raw/ ──► Layer 0 ──► Layer 1 ──► Layer 2 ──► Layer 3
     │              │         │          │           │           │
     │              │         │          │           │           │
  download      validate   JSON      extract     embed       resolve
  checksum     provenance  Schema    entities   vectors     relationships
                           draft-07  (mentions)  (pgvector)  (CTEs)
```

### Storage Strategy

| Layer | Format | Storage | Reasoning |
|-------|--------|---------|-----------|
| Raw | Original (PDF, images) | Local, gitignored | Large, reproducible from source |
| Layer 0 | CSV + JSON Schema | Git | Human-readable, version-controlled |
| Layer 1 | PostgreSQL (core schema) | Cluster DB | Relational queries, entity extraction |
| Layer 2 | PostgreSQL + pgvector | Cluster DB | Vector search requires DB |
| Layer 3 | PostgreSQL (analytics schema) | Cluster DB | Recursive CTEs for graph queries |

### Integration Points

- **Cluster infrastructure:** PostgreSQL 16+ on astronomy cluster (existing pgvector setup)
- **ARD methodology repo:** This project becomes third case study
- **IBM RAG cert:** Techniques learned apply directly to pipeline development
- **epsteinfiles.dev:** Public interface with K-anonymity views

---

## Layer 0 Schemas (Current)

JSON Schema draft-07 definitions in `data/layer-0-canonical/schema/`.

### Flight Logs Schema

22 columns preserving Internet Archive format:

| Field | Type | Notes |
|-------|------|-------|
| ID | integer | Row identifier |
| Date | string | M/D/YYYY format |
| Aircraft Tail # | string | Pattern: ^N[0-9A-Z]+$ |
| Pass 1-10 | string | Passenger names (nullable) |
| Known | enum | Yes/No |
| Year, Month, Day | integer | Decomposed date |
| # of Seats | integer | Aircraft capacity |
| Data Source, Comment | string | Metadata |

### Black Book Schema

17 columns preserving epsteinsblackbook.com structure:

| Field | Type | Notes |
|-------|------|-------|
| record_id | uuid | Deterministic from content hash |
| Page | integer | Source page (1-95) |
| Page-Link | uri | Wayback Machine URL |
| Name | string | Primary contact name |
| Phone-1 through Phone-5 | string | Inconsistent formats |
| Email-1 through Email-3 | string | 17% coverage |
| Address, City, State, Zip, Country | string | 34% country missing |

---

## Layer 1+ Architecture (Planned)

From GDR research (`research/gdr-artifacts/epstein-schema-architecture.md`):

### Entity Resolution Model

Bifurcated approach separating observation from interpretation:

```
┌─────────────────────┐     ┌─────────────────────┐
│  identity_mentions  │────►│  resolved_entities  │
│  (what doc says)    │ N:M │  (what we believe)  │
└─────────────────────┘     └─────────────────────┘
         │                           │
         │                           │
    artifact_id               entity_id
    raw_text                  canonical_name
    parsed_components         entity_type
    embedding_vector          is_verified
```

**Resolution Pipeline:**
1. **Parse:** probablepeople CRF extracts name components
2. **Block:** Soundex on surname groups candidates
3. **Compare:** pgvector cosine similarity within blocks
4. **Link:** Threshold-based clustering to entity_id

### Key PostgreSQL Patterns

| Pattern | Purpose | Implementation |
|---------|---------|----------------|
| SCD Type 2 | Aircraft ownership history | DATERANGE + GiST index |
| Fuzzy dates | Partial dates ("June 1999") | Composite type (year, month, day, raw) |
| K-anonymity | Victim protection | Public schema views with generalization |
| Graph edges | Relationship queries | Materialized view + recursive CTEs |
| Co-occurrence | Inner circle analysis | Sparse matrix materialized view |

### Core Tables (L1)

```sql
-- Provenance
source_artifacts (artifact_id, file_hash_sha256, source_classification)

-- Entities
identity_mentions (mention_id, artifact_id, raw_text, parsed_components JSONB, embedding_vector vector(768))
resolved_entities (entity_id, canonical_name, entity_type, is_verified)
entity_mention_map (entity_id, mention_id, confidence_score)

-- Aviation
aircraft_registry_history (n_number, serial_number, owner_name, valid_period DATERANGE)
flight_events (flight_id, aircraft_serial, departure_time, origin_icao, destination_icao)
flight_passengers (flight_id, mention_id, role, notes)
```

### Analytics Views (L3)

```sql
-- Graph structure
network_edges VIEW (source, target, type, weight)

-- Co-occurrence matrix (sparse)
mv_flight_cooccurrence MATERIALIZED VIEW (person_a, person_b, flight_count)
```

---

## Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| L0 validation | JSON Schema draft-07 | Standards-based, tooling support |
| Database | PostgreSQL 16+ pgvector | Aligns with cluster, unified engine |
| Primary L0 format | CSV | Human-readable, universal tooling |
| Name parsing | probablepeople | CRF-based, handles messiness |
| Embedding model | all-MiniLM-L6-v2 | Fast, 768-dim, sentence-transformers |
| Entity resolution | Soundex blocking + vector similarity | Scalable, probabilistic |
| Graph storage | PostgreSQL recursive CTEs | Avoid premature Neo4j complexity |
| Temporal queries | DATERANGE + GiST | Native PostgreSQL, efficient |
| Victim protection | K-anonymity views | Public schema generalization |
| Web framework | TBD | Decide during M08 |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [context.md](context.md) | Current state and next steps |
| [tech-stack.md](tech-stack.md) | Technology choices |
| [GDR Architecture](../../research/gdr-artifacts/epstein-schema-architecture.md) | Full L1+ design reference |
| [L0 Schema README](../../data/layer-0-canonical/schema/README.md) | Schema documentation |
