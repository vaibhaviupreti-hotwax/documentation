# Walkthrough: ERP Data Classification Investigation

## Changes Made

This task successfully concluded the exhaustive investigation and classification of ERP data entities across both generations of the company's architecture:
1. **Setup A:** Moqui-Only Architecture (`moqui-framework`)
2. **Setup B:** Legacy Integrated Architecture (`sandbox/ofbiz-oms`)

### Automated Architecture Extraction
To efficiently parse and classify over 866 XML entity schemas, a custom Python script (`analyze_and_classify.py`) was developed and executed. This analyzer:
- Extracted entity metadata and structural relationships.
- Mapped all `seed`, `seed-initial`, `ext-seed`, and `ext` data loader files to their parent entities.
- Applied the heuristic grading system (Tier 1, Tier 2, Tier 3) derived from naming semantics, integration bias (Shopify), and installation methodologies.

### Generated Deliverables
The following deliverables were generated. Due to their large size (hundreds of rows of entities), they have been placed in the `scratch/` directory:
- [Deliverable 7 — Legacy Integrated Architecture Report](file:///home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/scratch/deliverable_7.md)
- [Deliverable 8 — Moqui-Only Architecture Report](file:///home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/scratch/deliverable_8.md)
- [Deliverable 9 — Architecture Comparison Report](file:///home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/scratch/deliverable_9.md)

Additionally, a comprehensive [Deliverable 10 — Research Validation Report](file:///home/vaibhaviupreti/.gemini/antigravity/brain/1c87c106-3aaf-4577-9467-6828f432fc33/deliverable_10.md) was created as an artifact, comparing our codebase findings against the updated store setup SOPs.

## Validation Results

> [!TIP]
> **Installer Architecture Proposal**
> Based on the verification in Deliverable 10, the recommended boot sequence for client onboarding is:
> 1. **Core Framework Load (Tier 1):** Deploy `seed` and `seed-initial` data (e.g., `EnumerationGroup`, `SystemProperty`).
> 2. **Client Config Load (Tier 2):** Deploy generated `ext-seed` files for identity mapping (e.g., `ProductStore`, `Facility`, `ShopifyShop`).
> 3. **Transactional/Mutable Synchronization (Tier 3):** Live runtime synchronizations and CSV imports (e.g., `PurchaseOrder`, `InventoryItem`).

### Key Discoveries
- **Setup B Deprecations:** Hundreds of legacy OFBiz entities (e.g., `ShoppingList`, `Survey`, `Subscription`) have been completely decoupled or omitted in the newer Setup A (Moqui-only) schema.
- **Facility Gap Validation:** Confirmed that `Facility` records inherently lack `seed` configurations across both platforms, validating the "Gap #1" listed in the client setup SOP.
- **Shopify Bias:** In Setup A, Shopify configurations (`ShopifyShopTypeMapping`) act as the absolute anchor for Tier 2 integration, necessitating heavy implementation load via `ext-seed` files inside components like `gorjana-maarg`.
