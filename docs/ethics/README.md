<!--
---
title: "Ethics Documentation"
description: "Ethical framework and data handling guidelines"
author: "VintageDon"
orcid: "0009-0008-7695-4093"
date: "2026-02-01"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: ethics
---
-->

# Ethics Documentation

Ethical framework governing data handling, processing decisions, and acceptable use.

---

## 1. Contents

```
ethics/
├── framework.md            # Core ethical principles
├── redaction-policy.md     # Handling of redacted content
├── victim-protection.md    # Anonymization requirements
├── acceptable-use.md       # Permitted and prohibited uses
└── README.md               # This file
```

---

## 2. Core Principles

| Principle | Implementation |
|-----------|----------------|
| **Respect Redactions** | Honor all redactions in source documents |
| **Protect Victims** | Scrub/anonymize discovered victim-identifying information |
| **No Fine-Tuning** | Do not train generative models on this corpus |
| **No Commercial Use** | Public interest and educational purposes only |
| **Verify Facts** | Present RAG outputs as leads, not established truth |
| **Provenance** | Every processed record links to its source |

---

## 3. Redaction Handling

Some source documents have visual-only redactions where underlying text remains in the PDF. When discovered:

1. Do not extract or expose the hidden text
2. Document the finding (file, page) without content
3. Apply equivalent redaction to processed output

---

## 4. Victim Protection

If processing reveals information that could identify victims:

1. Halt processing of that record
2. Flag for manual review
3. Apply anonymization before including in dataset
4. Document the anonymization (not the content)

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [case-study/](../case-study/) | Methodology documentation |
| [brief.md](../../.kilocode/rules/memory-bank/brief.md) | Project principles |
