# DELIVERABLE 7: Legacy OFBiz Architecture Report

## 1. Entity Inventory

| Entity Name | Tier | Confidence | Evidence | SOP Layer |
| :--- | :--- | :--- | :--- | :--- |
| `EntityAuditLog` | **T1** | 100% | `create-only="true"` schema lock | L1 (Platform Reference) |
| `FacilityType`, `Uom` | **T1** | 95% | Found exclusively in `seed` files | L1 (Platform Reference) |
| `Enumeration` | **T2** | 95% | `ext-seed` UPSERT overrides | L2 / L3 (Integration / Config) |
| `ShipmentMethodType` | **T2** | 95% | `ext-seed` UPSERT overrides | L2 / L3 (Integration / Config) |
| `ContactMech`, `Facility` | **T2** | 95% | Configured natively in `ext-seed` | L3 (Client Config) |
| `OrderHeader`, `Shipment` | **T3** | 100% | Exclusively transactional sync | L3 / L4 (Runtime Sync) |

## 2. Data Loading Strategy

The Legacy OFBiz Architecture (Setup B) relies heavily on a monolithic data structure wrapped inside the Moqui loader engine.

*   **L1 (Platform Reference):** Sourced from hundreds of framework `seed` files. Establishes the unchangeable core (e.g., Status flows, system enumerations).
*   **L2 (Integration Machinery):** Connectors and framework-level integration defaults loaded via `ext-seed`.
*   **L3 (Client Setup Data):** Store-specific overrides. In OFBiz, this relies heavily on artificial alphabetical prefixing (`A1_`, `A2_`) to force proper foreign key resolution.
*   **T3 (Transactional Data):** Order and inventory history managed entirely outside the loader via API syncs.

## 3. Tier Distribution
*   **Tier 1 (Core Framework):** ~75% of total entities (Highly monolithic schema).
*   **Tier 2 (Configurable):** ~10% of entities (Extensively mapped via manual data load files).
*   **Tier 3 (Transactional):** ~15% of entities.

## 4. Key Findings
*   **Immutability:** `EntityAuditLog` is the *only* mathematically immutable entity across the entire platform.
*   **UPSERT Idempotency:** The system heavily utilizes Moqui's native `createOrUpdate` mechanism. Customizations placed in `ext-seed` cleanly override `seed` configurations if primary keys overlap.
*   **Framework Baseline:** The vast majority of the schema acts purely as an uncustomized L1 base.

## 5. Risks & Gaps
*   **Gap #1 (No Facility Seed):** The `Facility` entity inherently lacks a `seed` definition. It is strictly a Tier 2 (L3) construct, meaning the installer *must* explicitly provide it.
*   **Gap #2 (Security Parity):** `artifactGroups` mapping must perfectly align between L1 and L3, otherwise warehouse managers lose access to fundamental UIs.
*   **Foreign Key Volatility:** The legacy system's reliance on `A1_`/`A2_` alphabetization makes automated injections brittle if filenames are not perfectly formatted.
