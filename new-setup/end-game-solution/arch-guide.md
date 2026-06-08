# The End Game: Automated ERP Installer Architecture

## 1. Executive Summary

This document serves as the definitive architectural blueprint for automating the onboarding of new clients/stores into the ERP ecosystem. Over the course of a deep-dive investigation into the framework's codebase, data definitions, and Docker bootloader, we have successfully validated the target data ownership model (L1–L4) and mapped the underlying mechanics of the Moqui Entity Engine. 

The core revelation guiding this solution is **Idempotent Upsert Resilience**: the Moqui data engine natively resolves primary key collisions by seamlessly updating records rather than crashing. This enables a robust, layered automated installation sequence where store-specific customizations safely merge atop core framework data without requiring brittle file manipulations or strict immutability locks.

---

## 2. Architectural Context (Setup A vs Setup B)

The company currently straddles two distinct architectures. The installer must account for the mechanical differences in how they consume data.

### Setup A: Moqui-Only (Modern, Recommended)
*   **Structure:** Decoupled, API-first architecture heavily utilizing the Universal Data Model (`mantle-udm`) and downstream client components (e.g., `gorjana-maarg`).
*   **Loading Resilience:** Excellent. Relies on **Component Dependency Graphs**. The framework guarantees that core structural data loads prior to downstream client integrations, naturally preventing foreign key constraint violations.
*   **Focus:** Highly biased toward Shopify. Integration entities (e.g., `ShopifyShopTypeMapping`) act as the anchor for client installations.

### Setup B: Legacy OFBiz (Monolithic)
*   **Structure:** Heavily coupled architecture (`sandbox/ofbiz-oms`) that retains hundreds of deprecated schemas (e.g., `ShoppingList`, `Survey`).
*   **Loading Resilience:** Poor. Bypasses component dependency logic by forcing all files into a single monolith. Relies entirely on artificial **Alphabetical Prefixing** (`A1_CommonL10nData.xml`, `B1_ProductSeedData.xml`) to sequence loads and prevent foreign key crashes.

---

## 3. Data Ownership: The L1-L4 SOP Model

Static analysis of the XML files across both architectures validates the Standard Operating Procedure (SOP) data ownership model with **95%+ confidence**. 

| Layer | Definition | Ownership | System Action during Boot |
| :--- | :--- | :--- | :--- |
| **L1** | Platform Reference Data | Framework | Loaded universally via `seed` and `seed-initial`. Establishes the unchangeable core (e.g., `FacilityType`, `Uom`). |
| **L2** | Integration Machinery | Connectors | Loaded via `ext-seed`. Sets system-level integration defaults shared across tenants. |
| **L3** | Client Setup Data | Client Component | Loaded via `ext-seed`. Injects store-specific logic (`Facility`, `ContactMech`). |
| **L4** | Runtime Secrets | Deployment Environment | Not stored in XML or Git. Injected purely as Environmental Variables. |

---

## 4. Entity Classification (The 3 Tiers)

To construct the automated installer, every entity within the system was semantically classified into three tiers based on mutability and overlap between `seed` and `ext-seed` files.

### Tier 1: Immutable Core Framework (Seed Data)
These entities establish the foundation and are never touched by client configurations.
*   **Strictly Immutable:** `EntityAuditLog` (The only entity physically locked via `create-only="true"` schema metadata).
*   **Seed-Exclusive Entities:** `ProductCategoryType`, `VarianceReason`, `PartyRelationship`, `ReturnAdjustmentType`.

### Tier 2: Configurable & Merged Data (Ext-Seed)
These entities form the "Setup" layer and are the **primary target of the Automated Installer**.
*   **Additive Merge (No PK Overlap):** Client files inject new primary keys alongside the framework base. 
    *   *Examples:* `Facility`, `ContactMech`, `PartyIdentificationType`, `ServiceJob`, `SystemMessageRemote`, `artifactGroups`.
*   **Upsert Override (PK Overlap):** Client files purposefully reuse a primary key to overwrite the framework baseline.
    *   *Examples:* `Enumeration` (Overriding `ECOM_RTN_CHANNEL`), `ShipmentMethodType` (Overriding `SECOND_DAY` to match Shopify definitions), `ProductStoreSetting`.

### Tier 3: Transactional Sync Data
Volatile business records managed entirely by runtime APIs (Webhooks). The automated installer does not touch these entities directly.
*   *Examples:* `OrderHeader`, `InventoryItem`, `Shipment`.

---

## 5. Under The Hood: The Data Loader Stack Trace

To understand *why* Tier 2 overrides are safe, we traced the exact execution path of the Docker boot sequence down to the core Java SQL handlers.

1.  **Docker Boot:** `moqui-run.sh` launches the JVM via `MoquiStart.java`, passing `load types=seed,seed-initial,install`.
2.  **Context Check:** `ExecutionContextFactoryImpl.groovy` detects an empty database and triggers the initial bootstrap.
3.  **Discovery & Sequencing:** `EntityDataLoaderImpl.groovy` builds the dependency graph, targeting framework components first, then client components. It sorts files alphabetically within each `data/` directory.
4.  **Transaction Boundary:** The loader wraps **every single file** in an isolated database transaction. If a foreign key fails, only that file rolls back; the container does not crash.
5.  **SAX Streaming:** `EntityXmlHandler.groovy` streams the XML event-by-event, hydrating generic `EntityValue` objects.
6.  **The Engine Upsert:** The `EntityValue` is passed to `EntityValueBase.createOrUpdate()`.
    *   The Engine executes a `SELECT` by Primary Key.
    *   If missing, it dynamically `INSERT`s.
    *   If existing, it compares and dynamically `UPDATE`s (This is the mechanism allowing L3 files to safely override L1 baselines).

---

## 6. The Automated Installer Proposal

With the mechanical constraints fully validated, the automated provisioning sequence is clear. The goal is to reduce onboarding from discovery to live sync to **< 4 hours**.

### Technical Stack
*   **Orchestration:** Node.js CLI to prompt the implementation engineer.
*   **Generation:** Nunjucks templating to dynamically build L3 `ext-seed` XML payloads based on CLI answers.
*   **Execution:** Moqui `gradlew load` sequence.

### The 5-Stage Bootstrap Sequence

1.  **Stage 1 (L1 Baseline):** 
    Execute framework data loaders (`seed`, `seed-initial`). This locks in the Tier 1 schema.
2.  **Stage 2 (L2 Integration):** 
    Load standardized connector mapping layers.
3.  **Stage 3 (L3 Generation Questionnaire):** 
    The CLI prompts the operator for the Shopify Shop ID, Store Name, and Return Location specifics. The CLI generates the `Facility`, `ContactMech`, and `ShopifyShopTypeMapping` entities into a new `ExtSeedData.xml`.
4.  **Stage 4 (L3 Client Injection):** 
    The generated L3 files are loaded via `ext-seed`. Relying on Moqui's idempotent Upsert, the client specifics seamlessly merge atop the baseline. *(For Legacy Setup B, the script must auto-prefix these files as `Z1_ExtSeedData.xml` to force alphabetical compliance).*
5.  **Stage 5 (L4 Secrets & Handover):** 
    API keys and webhooks are mapped to `.env` files. The system is securely handed over to Tier 3 transactional syncing.

### Risks Mitigated
*   **Data Collisions:** Prevented by native `createOrUpdate` idempotency.
*   **Missing Facilities (Gap #1):** Solved via Stage 3 forced CLI generation.
*   **Broken UI Access (Gap #2):** `artifactGroups` mappings are dynamically generated alongside the store.
*   **Credential Leaks:** Zero tokens stored in XML setup files; purely managed in Stage 5 `.env` layers.
