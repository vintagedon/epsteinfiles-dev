<!--
---
title: "Milestone 02: GitHub Project Frameout"
description: "GitHub Project setup with milestones, labels, and tasks for ARD pipeline"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Complete"
tags:
  - type: worklog
  - domain: project-management
related_documents:
  - "[Previous Phase](../01-ideation-and-setup/README.md)"
  - "[Next Phase](../03-source-evaluation-import/README.md)"
---
-->

# Milestone 02: GitHub Project Frameout

## Summary

| Attribute | Value |
|-----------|-------|
| Status | ✅ Complete |
| Sessions | 1 |
| Artifacts | 1 PowerShell script, 10 labels, 6 milestones, 18 tasks |

**Objective**: Transform project scope into actionable GitHub Project with milestones and discrete work units.

**Outcome**: GitHub Project populated with M03-M08 milestones and 18 tasks covering the full ARD pipeline from source evaluation through web deployment.

---

## 1. Contents

```
02-github-project-frameout/
├── create-github-project.ps1   # Setup script (labels, milestones, issues)
└── README.md                   # This file
```

---

## 2. Work Completed

| Task | Description | Result |
|------|-------------|--------|
| Raw data assessment | Examined downloaded PDFs (118pg flight logs, 92pg black book) | Confirmed OCR challenges |
| Existing dataset research | Searched for pre-processed datasets | Found multiple quality sources |
| Milestone revision | Revised M03+ to leverage existing Layer 0 work | 6 milestones defined |
| Label taxonomy | Defined labels for work types, layers, document types | 10 labels created |
| Task breakdown | Created discrete tasks for each milestone | 18 tasks created |
| Script creation | Built PowerShell script for gh CLI setup | Script executed successfully |

---

## 3. Key Decisions

| Decision | Rationale |
|----------|-----------|
| Leverage existing datasets | theelderemo/FULL_EPSTEIN_INDEX and epsteinsblackbook.com already have quality OCR'd data; ARD value is in Layers 1-3, not re-doing Layer 0 |
| Tasks as work units | Project scale doesn't warrant sub-task hierarchy; tasks are session-sized |
| No due dates | Dynamic schedule; milestones ordered but not time-boxed |
| Flight Logs + Black Book scope | Maintained bounded scope from M01; other DOJ releases deferred |

---

## 4. Existing Datasets Identified

| Source | Content | Notes |
|--------|---------|-------|
| theelderemo/FULL_EPSTEIN_INDEX | HuggingFace dataset, all DOJ releases | MIT licensed, same ethical guidelines |
| epsteinsblackbook.com/files | Structured CSVs for both document types | Clean, queryable format |
| Martin-dev-prog/Full-Epstein-Flights | Flight routes with airports.csv | Geographic data |
| Archive.org | Raw flight log scans | Reference/validation |

---

## 5. GitHub Project Structure

**Labels:**
- Work type: `Task`
- Document: `flight-logs`, `black-book`
- Layer: `layer-0`, `layer-1`, `layer-2`, `layer-3`
- Category: `infrastructure`, `documentation`, `research`

**Milestones:**
- M03: Source Evaluation & Import
- M04: Layer 0 Validation
- M05: Layer 1 Scalars
- M06: Layer 2 Vectors
- M07: Layer 3 Graphs
- M08: Web Interface

---

## 6. Issues Encountered

| Issue | Resolution |
|-------|------------|
| Raw PDFs poor for direct processing | Pivoted to sourcing pre-processed datasets |
| Procedures doc referenced missing methodology file | Worked from procedures doc content directly |

---

## 7. Next Phase

**Handoff**: GitHub Project is configured and ready for work. All tasks visible in Kanban view.

**Next Steps**:

1. Begin M03 Task 3.1: Evaluate existing datasets against project criteria
2. Download and assess theelderemo HuggingFace dataset
3. Compare with epsteinsblackbook.com structured CSVs
4. Document evaluation findings in research/
