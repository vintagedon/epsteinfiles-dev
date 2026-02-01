<!--
---
title: "Scripts"
description: "Automation and setup scripts for the Epstein Files ARD project"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: automation
---
-->

# Scripts

Automation and setup scripts for the Epstein Files ARD project. Scripts are named with milestone prefixes (`mNN-`) to indicate when they were created and what phase they support.

---

## 1. Contents

```
scripts/
├── m02-01-create-github-project.ps1   # GitHub Project setup (labels, milestones, issues)
└── README.md                          # This file
```

---

## 2. Scripts

| Script | Milestone | Description | Status |
|--------|-----------|-------------|--------|
| [m02-01-create-github-project.ps1](m02-01-create-github-project.ps1) | M02 | Creates GitHub labels, milestones, and task issues | ✅ Complete |

---

## 3. Naming Convention

Scripts follow the pattern: `mNN-SS-description.ps1`

| Component | Meaning |
|-----------|---------|
| `mNN` | Milestone number (e.g., `m02` = Milestone 02) |
| `SS` | Sequence within milestone (e.g., `01` = first script) |
| `description` | Brief kebab-case description |

---

## 4. Usage Notes

**Prerequisites:**
- PowerShell 5.1+ or PowerShell Core
- GitHub CLI (`gh`) authenticated: `gh auth status`

**Execution:**
```powershell
# From repo root
.\scripts\m02-01-create-github-project.ps1
```

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [Work Logs](../work-logs/README.md) | Milestone documentation |
| [Documentation Standards](../docs/documentation-standards/README.md) | Script header template |
