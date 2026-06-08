# DELIVERABLE 9: Architecture Comparison Report

## 1. Entity Tier Alignment

| Entity | Setup B (OFBiz) Tier | Setup A (Moqui) Tier | Alignment | Note |
| :--- | :--- | :--- | :--- | :--- |
| `EntityAuditLog` | T1 | T1 | **MATCH** | Hardcoded immutability. |
| `Enumeration` | T2 | T2 | **MATCH** | UPSERT override usage exists in both. |
| `ShoppingList` | T3 | N/A | **DEPRECATED** | Legacy OFBiz entity dropped in Moqui. |
| `Facility` | T2 | T2 | **MATCH** | Missing L1 seed in both; L3 requirement. |
| `ShopifyShopTypeMapping`| N/A | T2 | **NEW** | Added exclusively in Setup A for integration. |

## 2. Key Differences

*   **Immutability & Resolution:** Both architectures utilize the Moqui data engine, meaning both benefit from idempotent UPSERTs (`createOrUpdate()`). Neither fails on Primary Key collisions.
*   **Customization Method (Load Resilience):** 
    *   **OFBiz (Setup B):** Customizations in `ext-seed` are injected into monolithic, flattened directories. The loading resilience is highly brittle and relies entirely on artificial alphabetical filename prefixes (`A1_`, `A2_`) to prevent FK errors.
    *   **Moqui (Setup A):** Customizations cleanly separate into downstream components. Moqui guarantees that framework L1 data parses before L3 client data purely through the `depends-on` component graph.
*   **Schema Bloat:** Setup B carries hundreds of deprecated, tightly coupled legacy schemas. Setup A's Universal Data Model is significantly leaner and purpose-built for API-first ERP operations.

## 3. Tier Distribution Comparison

| Tier Classification | Setup B (OFBiz) | Setup A (Moqui) | Shift |
| :--- | :--- | :--- | :--- |
| **Tier 1 (Core)** | ~75% (approx 600+) | ~60% (approx 350) | **Massive Reduction** (Legacy Bloat Removed) |
| **Tier 2 (Configurable)** | ~10% | ~20% | **Increased** (Heavier L2 integration footprint) |
| **Tier 3 (Transactional)**| ~15% | ~20% | **Steady** |

## 4. Migration Implications
*   **T1 (Core):** No client action needed. Loads seamlessly from `seed`.
*   **T2 (Configurable):** The installation script logic will completely change. Setup A requires building isolated downstream components for clients instead of appending prefixed files to a monolith.
*   **T3 (Transactional):** Separate sync. Legacy ECA hooks in OFBiz must be migrated to explicit Moqui `SystemMessage` integrations.

## 5. Recommendation
**Mandatory adoption of Setup A (Moqui-Only) for all new clients.** The Moqui-native approach offers robust, deterministic data loading via component dependency graphs, natively preventing the foreign key failures plaguing the legacy OFBiz monolithic loads.
