# Epstein Files ARD Context

<!-- 
Purpose: Current state, next steps, active decisions - the most frequently updated file
Audience: AI agents needing to understand "where are we now?"
Update Frequency: After every significant work session
CRITICAL: Keep this current. Stale context is worse than no context.
-->

## Current State

**Last Updated:** 2026-02-01

### Recent Accomplishments

- M01 complete: Repository scaffolded, memory bank populated, scope bounded
- M02 complete: GitHub Project configured with milestones M03-M08, 18 tasks created
- Discovered existing processed datasets (theelderemo/FULL_EPSTEIN_INDEX, epsteinsblackbook.com)
- Revised milestone structure to leverage existing Layer 0 work

### Current Phase

We are currently in **Milestone 03: Source Evaluation & Import** which involves evaluating existing datasets, selecting authoritative sources, and importing with provenance documentation.

### Active Work

Next session should begin:

1. **Task 3.1:** Evaluate existing datasets against project criteria
2. Download and assess theelderemo HuggingFace dataset
3. Compare with epsteinsblackbook.com structured CSVs
4. Document evaluation findings in research/

## Next Steps

### Immediate (Next Session)

1. Download theelderemo/FULL_EPSTEIN_INDEX from HuggingFace
2. Download epsteinsblackbook.com CSVs (flight-manifest-rows.txt, black-book-lines.txt)
3. Assess coverage, quality, and schema usability
4. Create evaluation matrix in research/

### Near-Term (M03-M04)

- Task 3.2: Select and document sources with provenance chain
- Task 3.3: Import to repo structure (data/layer-0-canonical/)
- M04: Schema definition and quality audit

### Future / Backlog

- M05: Layer 1 entity extraction and normalization
- M06: Layer 2 vector embeddings
- M07: Layer 3 graph relationships
- M08: Web interface at epsteinfiles.dev
- Cross-reference with ARD methodology repo as case study

## Active Decisions

### Pending Decisions

- **Primary data source:** theelderemo HuggingFace vs. epsteinsblackbook.com vs. combination. Decide in Task 3.1.
- **Vector database choice:** pgvector (aligned with cluster) vs. dedicated vector DB. Leaning pgvector for simplicity.
- **Graph storage:** Neo4j vs. PostgreSQL with recursive CTEs. Defer until M07.

### Recent Decisions

- **2026-02-01 - Leverage existing Layer 0:** Multiple quality datasets exist with OCR'd content. ARD value is in Layers 1-3, not re-doing canonicalization work. Revised milestones accordingly.
- **2026-02-01 - Tasks as work units:** Project scale doesn't warrant sub-task hierarchy. Tasks are session-sized discrete units.
- **2026-02-01 - No due dates:** Dynamic schedule; milestones ordered but not time-boxed.
- **2026-02-01 - Bounded starter corpus:** Flight Logs + Black Book maintained as scope. Other DOJ releases deferred.

## Blockers and Dependencies

### Current Blockers

- None

### External Dependencies

- **theelderemo/FULL_EPSTEIN_INDEX:** HuggingFace dataset availability
- **epsteinsblackbook.com:** Structured CSV downloads
- **DOJ Epstein Library:** Reference for provenance chain (justice.gov/epstein)

## Notes and Observations

### Existing Datasets Identified (M02)

| Source | Content | Notes |
|--------|---------|-------|
| theelderemo/FULL_EPSTEIN_INDEX | HuggingFace dataset, all DOJ releases | MIT licensed, same ethical guidelines |
| epsteinsblackbook.com/files | Structured CSVs for both document types | Clean, queryable format |
| Martin-dev-prog/Full-Epstein-Flights | Flight routes with airports.csv | Geographic data |

### Context for Next Session

Begin M03 Task 3.1. GitHub Project is configured—use issue tracking for progress. Reference `work-logs/02-github-project-frameout/README.md` for M02 decisions.
