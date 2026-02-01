# Epstein Files ARD Architecture

<!-- 
Purpose: High-level structural decisions
Audience: AI agents needing to understand how the project is organized
Update Frequency: When structure changes
-->

## System Architecture

### ARD Layer Model

The project follows the Analysis Ready Dataset layer model:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Graphs                                            │
│  Entity resolution, relationship typing, co-occurrence      │
│  Query: "Who appears in both flight logs and black book?"   │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Vectors                                           │
│  Embeddings, similarity search, semantic clustering         │
│  Query: "Documents similar to this one"                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Scalars                                           │
│  Entity extraction, doc classification, temporal markers    │
│  Query: "All flight logs mentioning person X in 2005"       │
├─────────────────────────────────────────────────────────────┤
│  Layer 0: Canonical                                         │
│  Deduplicated, cleaned, uniform schema, provenance          │
│  Query: "Give me all records from source file Y"            │
├─────────────────────────────────────────────────────────────┤
│  Raw: Source Files                                          │
│  DOJ releases, original formats, checksums                  │
└─────────────────────────────────────────────────────────────┘
```

Each layer builds on the one below. Embeddings (Layer 2) over enriched features (Layer 1) capture more meaning than embeddings over raw text alone.

### Repository Structure

```
epsteinfiles-dev/
├── data/
│   ├── raw/                    # Original files (gitignored)
│   ├── layer-0-canonical/      # Cleaned, schema'd outputs
│   ├── layer-1-scalars/        # Derived quantities
│   ├── layer-2-vectors/        # Embeddings
│   └── layer-3-graphs/         # Relationship structures
├── pipelines/
│   ├── ingestion/              # Acquisition scripts
│   ├── processing/             # Layer transformations
│   └── validation/             # Quality checks
├── notebooks/                  # Exploratory analysis
├── src/                        # Production code (API, web)
├── docs/
│   ├── case-study/             # ARD methodology documentation
│   ├── ethics/                 # Data handling guidelines
│   └── documentation-standards/
├── research/                   # Source analysis, GDR artifacts
└── [standard scaffolding]
```

### Data Flow

```
DOJ Library ──► raw/ ──► Layer 0 ──► Layer 1 ──► Layer 2 ──► Layer 3
     │              │         │          │           │           │
     │              │         │          │           │           │
  download      validate   clean     extract     embed       resolve
  checksum     provenance  schema    entities   vectors     relationships
```

### Storage Strategy

| Layer | Format | Storage | Reasoning |
|-------|--------|---------|-----------|
| Raw | Original (PDF, images) | Local, gitignored | Large, reproducible from source |
| Layer 0 | Parquet/CSV | Git or LFS | Moderate size, version-controlled |
| Layer 1 | Parquet/CSV + PostgreSQL | Git + cluster DB | Query patterns need SQL |
| Layer 2 | PostgreSQL + pgvector | Cluster DB | Vector search requires DB |
| Layer 3 | PostgreSQL or Neo4j | Cluster DB | Graph queries |

### Integration Points

- **Cluster infrastructure:** PostgreSQL on astronomy cluster (existing pgvector setup)
- **ARD methodology repo:** This project becomes third case study
- **IBM RAG cert:** Techniques learned apply directly to pipeline development
- **epsteinfiles.dev:** Public interface served from cluster or static hosting

## Document Type Schemas

### Flight Logs (Layer 0)

```
flight_log_entry:
  source_file: string        # Original PDF part
  page_number: int
  date: date
  aircraft: string
  route_from: string
  route_to: string
  passengers: list[string]   # Raw names as written
  crew: list[string]
  notes: string
  raw_text: string           # Original OCR text
```

### Black Book (Layer 0)

```
contact_entry:
  source_file: string
  page_number: int
  name: string               # Primary name
  aliases: list[string]      # Alternate names if present
  phone_numbers: list[string]
  emails: list[string]
  addresses: list[string]
  notes: string
  raw_text: string
```

### Unified Entity (Layer 1+)

```
entity:
  entity_id: uuid
  canonical_name: string
  entity_type: enum[person, organization, location]
  mentions: list[mention_ref]   # Links to Layer 0 records
  attributes: dict              # Extracted metadata
  confidence: float
```

## Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | PostgreSQL + pgvector | Aligns with cluster, avoids new infra |
| Primary format | Parquet | Columnar, efficient, pandas-native |
| Embedding model | TBD (sentence-transformers baseline) | Start simple, evaluate domain-specific later |
| Graph storage | PostgreSQL first, Neo4j if needed | Avoid premature complexity |
| Web framework | TBD | Decide during M08 based on requirements |
