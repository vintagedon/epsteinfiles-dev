# Epstein Files ARD Product Overview

<!-- 
Purpose: Why this exists, what problems it solves, how it works
Audience: AI agents needing to understand value proposition and approach
Update Frequency: Occasionally - when vision or approach evolves
-->

## Problems Solved

This project addresses:

- **Repeated compute waste:** Every researcher working the Epstein corpus independently performs the same expensive operations—entity extraction, name resolution, document classification. An ARD performs these once with high rigor, converting processor time into storage space.

- **Inaccessible raw data:** DOJ releases are scattered across formats (scanned PDFs, images, mixed encodings), poorly organized, and require significant preprocessing before any analysis. Layer 0 canonicalization makes the data queryable.

- **Missing relationship structures:** Existing projects stop at text search. The investigative value lies in relationships—who flew with whom, who appears in both flight logs and the black book, temporal patterns. Layer 3 graphs enable these queries.

- **Toy dataset learning:** RAG and agent techniques learned on sanitized examples don't transfer to real-world messiness. Building against actual government documents with OCR noise, redactions, and inconsistent formatting builds production-relevant skills.

## How It Works

Epstein Files ARD applies the four-layer ARD model developed in the Analysis Ready Dataset methodology:

**Layer 0 (Canonical):** Raw documents are ingested, deduplicated, OCR-corrected where possible, and normalized into a uniform schema. Provenance is tracked—every record links back to its source file and release batch.

**Layer 1 (Scalars):** Literature-driven derived quantities are computed. For this corpus: document type classification, named entity extraction (people, organizations, locations, dates), temporal markers, redaction percentage, and reference identifiers.

**Layer 2 (Vectors):** Embedding representations enable similarity search and anomaly detection. Chunking strategies account for document structure (flight log rows vs. contact book entries vs. narrative documents).

**Layer 3 (Graphs):** Entity resolution unifies mentions across documents ("J.E.", "Jeffrey", "Epstein" → canonical entity). Relationship typing distinguishes co-occurrence from explicit mention. Temporal graphs track when relationships appear in the record.

Key components:

- **Ingestion pipelines:** Acquisition scripts with checksums and provenance tracking
- **Processing pipelines:** Layer transformations with validation gates
- **PostgreSQL + pgvector:** Storage and vector search aligned with existing cluster infrastructure
- **Web interface:** Public search at epsteinfiles.dev

## Goals and Outcomes

### Primary Goals

1. **Bounded MVP:** Complete Layer 0-3 processing for Flight Logs + Black Book (~200 pages) as proof of architecture
2. **Skill development:** Apply each RAG/agent technique from certification coursework to real documents
3. **Methodology validation:** Demonstrate ARD pattern works for investigative/legal document corpora (third case study)

### User Experience Goals

- Researchers can query pre-computed entity relationships without building their own NER pipeline
- Similarity search surfaces related documents without manual keyword guessing
- Provenance links allow verification against original source files
- API access enables integration with other tools

### Success Metrics

- **Layer completion:** All four layers implemented for starter corpus
- **Entity resolution quality:** >90% precision on known entities (spot-checked against public reporting)
- **Query latency:** Similarity search returns in <500ms for typical queries
- **Documentation completeness:** Another team could reproduce the dataset from documentation alone
