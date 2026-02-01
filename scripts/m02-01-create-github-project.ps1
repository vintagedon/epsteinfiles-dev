<#
.SYNOPSIS
    Creates GitHub Project infrastructure for Epstein Files ARD pipeline.

.DESCRIPTION
    Populates the epsteinfiles-dev repository with labels, milestones, and issues
    for the ARD (Analysis Ready Dataset) pipeline. Creates 10 labels for work
    categorization, 6 milestones (M03-M08), and 18 task issues with detailed
    descriptions. Intended as a one-time setup script for project initialization.

.NOTES
    Repository  : epsteinfiles-dev
    Author      : VintageDon (https://github.com/vintagedon)
    ORCID       : https://orcid.org/0009-0008-7695-4093
    Created     : 2026-02-01
    Milestone   : M02 - GitHub Project Frameout

.EXAMPLE
    .\m02-01-create-github-project.ps1

    Creates all labels, milestones, and issues in the configured repository.
    Run from any directory; uses $REPO variable for targeting.

.LINK
    https://github.com/vintagedon/epsteinfiles-dev
#>

# =============================================================================
# Configuration
# =============================================================================

# AI NOTE: Update this if the repository is forked or renamed. All gh CLI
# commands use this variable for targeting.
$REPO = "VintageDon/epsteinfiles-dev"

# =============================================================================
# Labels
# =============================================================================

Write-Host "=== Creating Labels ===" -ForegroundColor Cyan

# Work unit type - primary classification for all issues
gh label create "Task" --description "Discrete work unit" --color "1d76db" --repo $REPO

# Document types - scope boundaries for the starter corpus
gh label create "flight-logs" --description "Flight log documents" --color "d4c5f9" --repo $REPO
gh label create "black-book" --description "Black book contacts" --color "c5def5" --repo $REPO

# Processing layers - ARD methodology stages (green gradient for visual grouping)
gh label create "layer-0" --description "Canonical/raw processing" --color "0e8a16" --repo $REPO
gh label create "layer-1" --description "Scalar extraction" --color "1d7a16" --repo $REPO
gh label create "layer-2" --description "Vector embeddings" --color "2d8a26" --repo $REPO
gh label create "layer-3" --description "Graph relationships" --color "3d9a36" --repo $REPO

# Work types - what kind of effort the task requires
gh label create "infrastructure" --description "Setup, tooling, pipelines" --color "fbca04" --repo $REPO
gh label create "documentation" --description "Docs, case study, methodology" --color "fef2c0" --repo $REPO
gh label create "research" --description "Source evaluation, analysis" --color "d93f0b" --repo $REPO

# =============================================================================
# Milestones
# =============================================================================

Write-Host "=== Creating Milestones ===" -ForegroundColor Cyan

# AI NOTE: Milestones are created without due dates per project convention.
# M01 (Ideation) and M02 (this script) are already complete and not created here.
# Order matters for GitHub UI display - create in sequence.

gh api "repos/$REPO/milestones" --method POST -f title="M03: Source Evaluation & Import" -f description="Evaluate existing datasets, select sources, import with provenance"
gh api "repos/$REPO/milestones" --method POST -f title="M04: Layer 0 Validation" -f description="Schema alignment, quality checks, deduplication"
gh api "repos/$REPO/milestones" --method POST -f title="M05: Layer 1 Scalars" -f description="Entity extraction, date normalization, classification"
gh api "repos/$REPO/milestones" --method POST -f title="M06: Layer 2 Vectors" -f description="Embeddings, similarity search, semantic clustering"
gh api "repos/$REPO/milestones" --method POST -f title="M07: Layer 3 Graphs" -f description="Entity resolution, relationship typing, co-occurrence"
gh api "repos/$REPO/milestones" --method POST -f title="M08: Web Interface" -f description="API, search interface, epsteinfiles.dev deployment"

# =============================================================================
# Tasks - M03: Source Evaluation & Import
# =============================================================================

Write-Host "=== Creating Tasks ===" -ForegroundColor Cyan

# AI NOTE: Issue bodies use here-strings (@"..."@) for multi-line markdown.
# The --milestone flag requires exact title match including "M0X:" prefix.

gh issue create --repo $REPO --title "Task 3.1: Evaluate existing datasets" --label "Task,research" --milestone "M03: Source Evaluation & Import" --body @"
## Objective
Survey and evaluate existing Epstein document datasets for quality, completeness, and alignment with project scope.

## Sources to Evaluate
- [ ] theelderemo/FULL_EPSTEIN_INDEX (HuggingFace dataset)
- [ ] epsteinsblackbook.com structured CSVs
- [ ] Martin-dev-prog/Full-Epstein-Flights
- [ ] Archive.org flight logs collection

## Evaluation Criteria
- Coverage of Flight Logs and Black Book
- Data quality (OCR accuracy, structure)
- Provenance documentation
- License compatibility
- Schema usability

## Deliverable
Evaluation matrix in research/ documenting findings and recommendations.
"@

gh issue create --repo $REPO --title "Task 3.2: Select and document sources" --label "Task,documentation" --milestone "M03: Source Evaluation & Import" --body @"
## Objective
Based on evaluation, select authoritative sources for Flight Logs and Black Book data.

## Deliverables
- [ ] Source selection documented in data/raw/MANIFEST.md
- [ ] Provenance chain established (original DOJ -> intermediate dataset -> our import)
- [ ] License compliance verified
- [ ] Download/access instructions documented

## Dependencies
- Task 3.1 complete
"@

gh issue create --repo $REPO --title "Task 3.3: Import to repo structure" --label "Task,infrastructure" --milestone "M03: Source Evaluation & Import" --body @"
## Objective
Import selected datasets into repository structure with proper organization.

## Deliverables
- [ ] Flight logs data in data/layer-0-canonical/flight-logs/
- [ ] Black book data in data/layer-0-canonical/black-book/
- [ ] Checksums generated and recorded
- [ ] Import scripts in pipelines/ingestion/

## Dependencies
- Task 3.2 complete
"@

# =============================================================================
# Tasks - M04: Layer 0 Validation
# =============================================================================

gh issue create --repo $REPO --title "Task 4.1: Schema definition" --label "Task,layer-0,documentation" --milestone "M04: Layer 0 Validation" --body @"
## Objective
Define canonical schemas for Flight Logs and Black Book records.

## Deliverables
- [ ] flight_log_entry schema (date, aircraft, route, passengers, crew, notes)
- [ ] contact_entry schema (name, aliases, phones, emails, addresses, notes)
- [ ] Schema documentation in docs/schemas/
- [ ] Validation rules defined

## Reference
See architecture.md for initial schema sketches.
"@

gh issue create --repo $REPO --title "Task 4.2: Quality audit" --label "Task,layer-0,research" --milestone "M04: Layer 0 Validation" --body @"
## Objective
Audit imported data for quality issues requiring correction.

## Checks
- [ ] Field completeness rates
- [ ] OCR error patterns
- [ ] Date format consistency
- [ ] Name spelling variations
- [ ] Missing provenance links

## Deliverable
Quality report with issue categories and remediation recommendations.
"@

gh issue create --repo $REPO --title "Task 4.3: Deduplication and normalization" --label "Task,layer-0,infrastructure" --milestone "M04: Layer 0 Validation" --body @"
## Objective
Clean and normalize Layer 0 data based on quality audit findings.

## Tasks
- [ ] Deduplicate records (if applicable)
- [ ] Normalize date formats to ISO 8601
- [ ] Standardize airport codes
- [ ] Flag but preserve OCR uncertainties
- [ ] Maintain provenance links through transformations

## Dependencies
- Tasks 4.1, 4.2 complete
"@

# =============================================================================
# Tasks - M05: Layer 1 Scalars
# =============================================================================

gh issue create --repo $REPO --title "Task 5.1: Entity extraction pipeline" --label "Task,layer-1,infrastructure" --milestone "M05: Layer 1 Scalars" --body @"
## Objective
Build pipeline to extract named entities from Layer 0 records.

## Entity Types
- Persons (passengers, contacts)
- Organizations
- Locations (airports, addresses)
- Dates/times

## Deliverables
- [ ] Extraction pipeline in pipelines/processing/
- [ ] Entity output in data/layer-1-scalars/entities/
- [ ] Confidence scores for extracted entities
"@

gh issue create --repo $REPO --title "Task 5.2: Date and location normalization" --label "Task,layer-1,flight-logs" --milestone "M05: Layer 1 Scalars" --body @"
## Objective
Normalize temporal and geographic references to queryable formats.

## Tasks
- [ ] Parse flight dates to ISO 8601
- [ ] Resolve airport codes to coordinates
- [ ] Build location lookup table
- [ ] Handle ambiguous/partial dates
"@

gh issue create --repo $REPO --title "Task 5.3: Document classification" --label "Task,layer-1" --milestone "M05: Layer 1 Scalars" --body @"
## Objective
Classify and tag records for filtering and analysis.

## Classification Dimensions
- Document type (flight log page, contact entry)
- Time period
- Aircraft type
- Geographic region

## Deliverable
Classification metadata attached to Layer 0 records.
"@

# =============================================================================
# Tasks - M06: Layer 2 Vectors
# =============================================================================

gh issue create --repo $REPO --title "Task 6.1: Embedding strategy" --label "Task,layer-2,research" --milestone "M06: Layer 2 Vectors" --body @"
## Objective
Define embedding approach for semantic search over the corpus.

## Decisions
- [ ] Embedding model selection (sentence-transformers baseline vs domain-specific)
- [ ] Chunking strategy for flight logs vs contacts
- [ ] Dimensionality and storage format
- [ ] pgvector configuration

## Deliverable
Embedding strategy document in docs/case-study/
"@

gh issue create --repo $REPO --title "Task 6.2: Vector generation" --label "Task,layer-2,infrastructure" --milestone "M06: Layer 2 Vectors" --body @"
## Objective
Generate embeddings for all Layer 1 enriched records.

## Tasks
- [ ] Implement embedding pipeline
- [ ] Process flight logs
- [ ] Process contact entries
- [ ] Store in pgvector

## Dependencies
- Task 6.1 complete
- Layer 1 data available
"@

gh issue create --repo $REPO --title "Task 6.3: Similarity indexing" --label "Task,layer-2,infrastructure" --milestone "M06: Layer 2 Vectors" --body @"
## Objective
Build similarity search capabilities over embedded corpus.

## Deliverables
- [ ] pgvector indexes configured
- [ ] Similarity query API
- [ ] Clustering analysis (optional)
"@

# =============================================================================
# Tasks - M07: Layer 3 Graphs
# =============================================================================

gh issue create --repo $REPO --title "Task 7.1: Entity resolution" --label "Task,layer-3,research" --milestone "M07: Layer 3 Graphs" --body @"
## Objective
Resolve entity mentions across documents to canonical identities.

## Challenges
- Name variations (nicknames, misspellings)
- Disambiguation (common names)
- Cross-document matching

## Deliverable
Resolved entity table linking mentions to canonical IDs.
"@

gh issue create --repo $REPO --title "Task 7.2: Relationship typing" --label "Task,layer-3" --milestone "M07: Layer 3 Graphs" --body @"
## Objective
Extract and type relationships between resolved entities.

## Relationship Types
- Co-occurrence on flights
- Contact book association
- Temporal co-presence

## Deliverable
Typed relationship edges with provenance to source records.
"@

gh issue create --repo $REPO --title "Task 7.3: Graph storage" --label "Task,layer-3,infrastructure" --milestone "M07: Layer 3 Graphs" --body @"
## Objective
Store entity graph for traversal queries.

## Options
- PostgreSQL with recursive CTEs
- Neo4j (if complexity warrants)

## Deliverables
- [ ] Graph schema
- [ ] Import pipeline
- [ ] Query examples
"@

# =============================================================================
# Tasks - M08: Web Interface
# =============================================================================

gh issue create --repo $REPO --title "Task 8.1: API design" --label "Task,infrastructure" --milestone "M08: Web Interface" --body @"
## Objective
Design API for querying processed data.

## Endpoints (draft)
- Search (text, semantic)
- Entity lookup
- Relationship traversal
- Provenance chain

## Deliverable
API specification document.
"@

gh issue create --repo $REPO --title "Task 8.2: Search interface" --label "Task,infrastructure" --milestone "M08: Web Interface" --body @"
## Objective
Build web UI for public access to the ARD.

## Features
- Text search
- Faceted filtering
- Entity pages
- Source provenance links

## Tech
TBD based on requirements analysis.
"@

gh issue create --repo $REPO --title "Task 8.3: Deployment" --label "Task,infrastructure" --milestone "M08: Web Interface" --body @"
## Objective
Deploy to epsteinfiles.dev

## Tasks
- [ ] Hosting configuration (cluster vs static)
- [ ] Domain/DNS setup (already registered on Cloudflare)
- [ ] SSL/security
- [ ] Monitoring
"@

# =============================================================================
# Complete
# =============================================================================

Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Created: 10 labels, 6 milestones, 18 tasks" -ForegroundColor Gray
Write-Host "Next: Create GitHub Project board and add repository" -ForegroundColor Gray
