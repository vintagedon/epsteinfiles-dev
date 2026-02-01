# Epstein Files ARD Brief

<!-- 
Purpose: 2-3 paragraphs establishing foundational context
Audience: AI agents loading this at session start
Update Frequency: Rarely - only when fundamental purpose/scope changes
-->

Epstein Files ARD is an Analysis Ready Dataset applying the ARD layer model to publicly released DOJ documents from the Jeffrey Epstein investigation. The project transforms raw government releases—scattered across formats, riddled with OCR noise, and lacking structure—into a queryable, enriched dataset where expensive computations (entity resolution, document classification, relationship extraction) have been performed once with rigor.

This project exists as both a learning vehicle and a public utility. It serves as a hands-on application of RAG and agentic AI techniques learned through the IBM RAG and Agentic AI professional certification, using real documents instead of toy datasets. Simultaneously, it provides investigative journalists, researchers, and the OSINT community with a properly engineered dataset that absorbs the compute debt they would otherwise repeat individually. The project also functions as a third case study for the ARD methodology (following DESI and Steam), validating cross-domain applicability.

The initial scope is deliberately bounded: Flight Logs (~100 pages, tabular) and the Black Book (97 pages, contact directory). These two document sets are highly structured, naturally joinable (who in the book flew on the plane?), and provide concrete deliverables while the full 3M+ page corpus remains available for future expansion. The project operates under strict ethical guidelines: respect all redactions, scrub any discovered victim-identifying information, no fine-tuning generative models on this data, and no commercial exploitation.
