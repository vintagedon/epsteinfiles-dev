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

- Project concept developed through discussion (onboarding chat for IBM RAG cert project)
- Domain registered: epsteinfiles.dev (Cloudflare, free plan)
- Repository created from project template
- Directory structure defined
- Scope bounded to Flight Logs + Black Book as starter corpus
- Ethical framework established

### Current Phase

We are currently in **Milestone 01: Ideation and Setup** which involves finalizing repository scaffolding, writing memory bank files, creating the primary README, and making the initial commit.

### Active Work

Currently working on:

1. **Memory bank population:** Writing brief, product, context, architecture, tech files
2. **Primary README:** Pending after memory bank complete
3. **Worklog documentation:** Capture M01 decisions and handoff to M02

## Next Steps

### Immediate (This Session)

1. Complete memory bank files
2. Write primary README
3. Create interior READMEs for new directories
4. Write M01 worklog
5. Initial commit

### Near-Term (Next Few Sessions)

- M02: GitHub Project frameout (milestones, tasks, sub-tasks)
- M03: Data acquisition—download Flight Logs and Black Book from DOJ, document provenance
- Begin Layer 0 canonicalization

### Future / Backlog

- Layer 1-3 implementation
- Web interface at epsteinfiles.dev
- Expansion beyond starter corpus (if warranted)
- Cross-reference with ARD methodology repo as case study

## Active Decisions

### Pending Decisions

- **Vector database choice:** pgvector (aligned with cluster) vs. dedicated vector DB (Qdrant, etc.). Leaning pgvector for simplicity.
- **Graph storage:** Neo4j vs. PostgreSQL with recursive CTEs vs. both. Defer until Layer 3.
- **Hosting for processed data:** Git LFS vs. external hosting vs. cluster storage. Decide during M03 based on actual file sizes.

### Recent Decisions

- **2026-02-01 - Bounded starter corpus:** Flight Logs + Black Book selected for initial scope. Rationale: structured, joinable, ~200 pages, high public interest.
- **2026-02-01 - Decoupled from cert:** Project phases are independent of certification progress. Can move ahead on ARD work regardless of coursework pace.
- **2026-02-01 - Ethical framework:** Adopted community guidelines—respect redactions, scrub victim info, no fine-tuning, no commercial use.

## Blockers and Dependencies

### Current Blockers

- None

### External Dependencies

- **DOJ Epstein Library:** Source data availability at justice.gov/epstein
- **Existing datasets:** theelderemo repos on GitHub, HuggingFace datasets as reference/comparison

## Notes and Observations

### Recent Insights

- Multiple consolidation projects exist but none apply ARD methodology
- January 30, 2026 DOJ release (3M+ pages) is largely unprocessed—opportunity for differentiation
- Existing projects found redaction failures in DOJ PDFs (visual overlay without text removal)—ethical consideration for handling discovered content

### Context for Next Session

M01 should complete this session. Next session begins M02: GitHub Project frameout. Reference `work-logs/milestones-one-and-two-procedures.md` for process.
