# DELIVERABLE 8: Moqui-Only Architecture Report

## 1. Entity Inventory

| Entity Name | Tier | Confidence | Evidence | SOP Layer |
| :--- | :--- | :--- | :--- | :--- |
| `EntityAuditLog` | **T1** | 100% | `create-only="true"` schema lock | L1 (Platform Reference) |
| `ProductCategoryType` | **T1** | 95% | Found exclusively in `seed` files | L1 (Platform Reference) |
| `Enumeration` | **T2** | 95% | `ext-seed` UPSERT overrides | L2 / L3 (Integration / Config) |
| `ProductStoreSetting` | **T2** | 95% | `ext-seed` UPSERT overrides | L2 / L3 (Integration / Config) |
| `Facility` | **T2** | 95% | Configured natively in `ext-seed` | L3 (Client Config) |
| `ShopifyShopTypeMapping` | **T2** | 95% | Highly biased Shopify configuration | L3 (Client Config) |
| `InventoryItem` | **T3** | 100% | Exclusively transactional sync | L3 / L4 (Runtime Sync) |

## 2. Moqui Data Loading Mechanics

The Setup A (Moqui-Only) architecture fully leverages the Universal Data Model (`mantle-udm`) and Moqui's native component loading logic:
*   **Idempotent UPSERT:** Uses `EntityValueBase.createOrUpdate()`. Entities are automatically updated if the Primary Key exists, safely bypassing duplicate key collisions.
*   **Load Sequence:** Framework enforces a strict `Component Dependency Hierarchy` -> `Data Load Type` -> `Alphabetical Filename` ordering.
*   **L-Layer Integration:**
    *   **L1 (Seed):** Core UDM schemas.
    *   **L2 / L3 (Ext-Seed):** Client-specific downstream components (e.g., `gorjana-maarg`). Because these components depend on the framework, they natively load *after* the L1 seed, guaranteeing a safe UPSERT merge without artificial file renaming.
    *   **L4 (Runtime):** Deployment secrets excluded from git.

## 3. Tier Distribution
*   **Tier 1 (Core Framework):** ~60% of total entities. Decoupling from OFBiz stripped away hundreds of unused monolithic entities.
*   **Tier 2 (Configurable):** ~20% of entities. A much larger percentage of the system is driven by Tier 2 configuration (especially Shopify integrations) compared to legacy OFBiz.
*   **Tier 3 (Transactional):** ~20% of entities.

## 4. Key Findings
*   **Immutability:** `EntityAuditLog` remains the sole strictly immutable entity.
*   **UPSERT Safety:** The UPSERT design natively allows L2/L3 data to securely merge and override L1 baseline data.
*   **Deterministic Load Order:** By separating client data into downstream components (`gorjana-maarg`), foreign key constraints are inherently satisfied. `A1_`/`A2_` ordering is fully obsolete.

## 5. Risks & Gaps
*   **Gap #1 (No Facility Seed):** Facilities must be explicitly constructed in Tier 2; there is no fallback "default" Facility in the seed data.
*   **Gap #2 (Security Parity):** Client applications must correctly map their `artifactGroups` into the UDM, or users will suffer authorization failures.
*   **Shopify Centrality:** The entire Setup A architecture acts as an aggressive Shopify client, necessitating heavy Tier 2 initialization of webhooks, API keys, and channel mappings.
