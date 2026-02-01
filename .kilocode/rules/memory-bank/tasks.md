# Epstein Files ARD Tasks and Workflows

<!-- 
Purpose: Repetitive workflows, procedures, and operational patterns
Audience: AI agents executing common tasks within this scope
Update Frequency: As new patterns emerge or workflows change
-->

## Common Workflows

### Data Acquisition

**When to use:** Adding new source documents to the corpus  
**Frequency:** Per release batch (DOJ releases are episodic)

**Steps:**

1. Download files from source (DOJ Library, existing GitHub repos)
2. Generate SHA-256 checksums for all files
3. Create provenance record:
   - Source URL
   - Download date
   - Release batch identifier
   - File count and total size
4. Store in `data/raw/{batch-identifier}/`
5. Update `data/raw/MANIFEST.md` with batch details
6. Validate checksums match if re-downloading

**Expected Outcome:** Raw files stored with full provenance trail  
**Common Issues:** Large downloads may timeout; use wget with resume capability

---

### Layer Processing

**When to use:** Transforming data from one layer to the next  
**Frequency:** Per layer, per corpus expansion

**Steps:**

1. Verify input layer is complete and validated
2. Run processing pipeline: `python pipelines/processing/layer_{n}_to_{n+1}.py`
3. Run validation: `python pipelines/validation/validate_layer_{n+1}.py`
4. Review validation report
5. If passing, commit outputs to appropriate `data/layer-{n+1}-*/` directory
6. Update `context.md` with completion status

**Expected Outcome:** New layer data with validation report  
**Common Issues:** Entity extraction may produce false positives; spot-check results

---

### Embedding Generation

**When to use:** Creating or updating Layer 2 vectors  
**Frequency:** After Layer 1 changes or model updates

**Steps:**

1. Load Layer 1 records with text content
2. Apply chunking strategy (document-type dependent)
3. Generate embeddings using configured model
4. Store vectors in pgvector table with record linkage
5. Validate embedding dimensions and null checks
6. Run similarity sanity checks (known-similar documents should cluster)

**Expected Outcome:** Vectors stored and queryable via pgvector  
**Common Issues:** Memory limits with large batches; process in chunks of 1000

---

## Memory Bank Maintenance

### Updating context.md

**When:** After every significant work session  
**What to update:**

1. Move completed items from "Next Steps" to "Recent Accomplishments"
2. Update "Current Phase" if phase changed
3. Update "Next Steps" with new actionable items
4. Document any new decisions in "Active Decisions"
5. Add/resolve blockers as appropriate
6. Update "Last Updated" date

**Quality check:** Does context.md accurately reflect current state?

---

## Ethical Review Workflow

**When to use:** Before publishing or sharing any processed data  
**Frequency:** Per release or significant update

**Steps:**

1. Run automated PII scan on output data
2. Spot-check sample of records for victim-identifying information
3. Verify all source redactions are preserved
4. Confirm no fine-tuning artifacts are included
5. Review against ethical framework in `docs/ethics/`
6. Document review in release notes

**Expected Outcome:** Data cleared for public sharing  
**Common Issues:** OCR may recover text from visual-only redactions; flag for manual review

---

## Quality Checklists

### Pipeline Quality Checklist

- [ ] Input validation passes before processing
- [ ] Provenance links maintained through transformation
- [ ] Output schema matches layer specification
- [ ] Validation script runs without errors
- [ ] Sample records spot-checked for accuracy
- [ ] Performance acceptable (document processing time)

### Documentation Quality Checklist

- [ ] Methodology documented in `docs/case-study/`
- [ ] Schema definitions current in `architecture.md`
- [ ] Ethical considerations documented
- [ ] Reproducibility instructions complete
- [ ] Version/date stamps updated
