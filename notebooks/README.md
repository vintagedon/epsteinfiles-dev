<!--
---
title: "Notebooks"
description: "Exploratory analysis and development notebooks"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: analysis
---
-->

# Notebooks

Jupyter notebooks for exploratory analysis, prototyping, and documentation.

---

## 1. Contents

```
notebooks/
├── exploration/            # Initial data exploration
├── prototypes/             # Pipeline development
├── analysis/               # Analytical deep dives
└── README.md               # This file
```

---

## 2. Purpose

Notebooks serve three functions:

| Type | Purpose | Promotion Path |
|------|---------|----------------|
| Exploration | Understand data characteristics | Insights → docs |
| Prototypes | Test processing approaches | Working code → pipelines |
| Analysis | Answer specific questions | Findings → reports |

---

## 3. Conventions

- **Naming**: `YYYY-MM-DD_topic_description.ipynb`
- **State**: Notebooks should run top-to-bottom without error
- **Outputs**: Clear outputs before committing (reduce repo size)
- **Promotion**: Working code moves to `pipelines/` or `src/`

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [data/](../data/) | Data inputs |
| [pipelines/](../pipelines/) | Promoted code destination |
| [research/](../research/) | Related analysis artifacts |
