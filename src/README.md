<!--
---
title: "Source Code"
description: "Production code for API, web interface, and shared utilities"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: development
---
-->

# Source Code

Production code for the web interface, API, and shared utilities.

---

## 1. Contents

```
src/
├── api/                    # REST API for data access
├── web/                    # Frontend for epsteinfiles.dev
├── lib/                    # Shared utilities
└── README.md               # This file
```

---

## 2. Planned Components

| Component | Purpose | Status |
|-----------|---------|--------|
| `api/` | Query interface for processed data | Planned (M08) |
| `web/` | Public search interface | Planned (M08) |
| `lib/` | Shared code (schemas, validators) | As needed |

---

## 3. Development Notes

Code here is production-grade:

- Tested
- Documented
- Deployable

Experimental code belongs in `notebooks/` or `pipelines/`.

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [pipelines/](../pipelines/) | Data preparation |
| [data/](../data/) | Data source |
| [tech.md](../.kilocode/rules/memory-bank/tech.md) | Technology stack |
