# Moqui Entity Tiering & Data Loading Analysis

This document outlines the findings regarding how Moqui handles data loading, entity immutability, and the classification of entities into automated installation tiers (T1/T2/T3). This intelligence forms the foundation for reliable, idempotent bootstrap sequences.

## 1. Moqui Data Loading Mechanics

A deep dive into the `EntityDataLoaderImpl.groovy` framework class revealed the following critical mechanics:

*   **Idempotent Upsert (`createOrUpdate`):** Moqui does **not** fail on primary key collisions by default. Instead, the `ValueHandler` uses an idempotent `createOrUpdate()` method that natively merges new data. It performs a `SELECT` by primary key, and if a collision occurs, it seamlessly updates the existing record via `UPDATE`. This allows custom definitions to override base definitions safely.
*   **Transaction Resilience:** Each data XML file is parsed and loaded within an isolated database transaction. If a file fails (e.g., due to a missing foreign key dependency), the loader logs an error, rolls back that specific file, and continues processing the rest of the startup sequence.
*   **Load Sequencing:** Data files do *not* load sequentially simply by their data type tags (e.g., `seed` vs. `ext-seed`). They load sequentially based on component hierarchy (Framework components load before downstream custom components), and then alphabetically by filename within each component's `data/` directory.

## 2. Immutable Entities (100% Core Data)

Because Moqui natively defaults to an idempotent UPSERT, very few entities are strictly protected at the framework layer.

To enforce immutability, an entity must be defined with the `create-only="true"` XML attribute. Attempting to update or override an existing primary key for these entities throws a fatal `EntityException`.

Based on a workspace-wide analysis, only one entity utilizes this constraint:
*   **`EntityAuditLog`** (Located in `moqui-framework/framework/entity/EntityEntities.xml` and `sandbox/maarg/framework/entity/EntityEntities.xml`).

All `create-only` entities are strictly classified as **Tier 1 (Immutable)**.

## 3. Seed vs. Ext-Seed Data Overlap (T1 vs. T2)

We analyzed the primary keys loaded in the core framework/base apps (`seed`) against the store-specific customizations in `gorjana-maarg/data` (`ext-seed`) to determine how entities merge. 

### Seed-Only Entities (Tier 1)
Hundreds of entities appear strictly in the `seed` directories without any customization in `gorjana-maarg`. These are pure framework-level structural entities and are treated as **Tier 1 (Core)**. Examples include:
*   `ProductCategoryType`
*   `VarianceReason`
*   `FacilityType`
*   `Uom`
*   `PartyRelationship`
*   `ReturnAdjustmentType`

### Merged Entities (Tier 2)
The following entities have data defined in *both* the core framework and the store-specific `ext-seed` files. These are classified as **Tier 2 (Configurable)**.

| Entity Name | PKs in `seed` (Samples) | PKs in `ext-seed` (Samples) | Conflict Resolution |
| :--- | :--- | :--- | :--- |
| **`ContactMech`** | `HC_USER_TN`, `HC_USER` | `HAPPINESS_LOCATION` | Added alongside seed |
| **`DataManagerConfig`** | `IMP_INCOMING_SHPMNT` | `SYNC_SHOPIFY_ORDER` | Added alongside seed |
| **`Enumeration`** | `ENTCO_IS_NULL` | `AFTSHIP_RTN_CHANNEL` | **Upsert Overrides** (e.g. `ECOM_RTN_CHANNEL`) |
| **`EnumerationType`** | `RETURN_CHANNEL` | `RULE_CONDITION_TYPE` | Added alongside seed |
| **`Facility`** | `CONFIGURATION` | `GRJ_DMG_FL_CLOSURE` | Added alongside seed |
| **`PartyIdentificationType`**| `SHOPIFY_CUST_ID` | `ADP_WORKER_ID` | Added alongside seed |
| **`ProductStoreSetting`** | (Various Settings) | (Various Settings) | **Upsert Overrides** (e.g. `STORE`) |
| **`ServiceJob`** | `generate_ReturnsFinancialFeed` | `sync_NetSuiteItemReceipts` | Added alongside seed |
| **`ShipmentMethodType`** | `STANDARD`, `EXPRESS` | `SECOND_DAY` (Expedited) | **Upsert Overrides** (e.g. `SECOND_DAY`) |
| **`StatusFlowTransition`** | `ORDER_CREATED->ORDER_COMPLETED` | `PICK_PROF_ACTIVE->PICK_PROF_DRAFT` | Added alongside seed |
| **`StatusItem`** | `INV_ON_ORDER` | `SHIP_RULE_ACTIVE` | Added alongside seed |
| **`StatusType`** | `COM_EVENT_STATUS` | `RULE_STATUS` | Added alongside seed |
| **`SystemMessageRemote`** | `RemoteSftp` | `WONDERMENT_CONFIG` | Added alongside seed |
| **`SystemMessageType`** | `SalesFinancialFeed` | `AftershipWarrantyApproved` | Added alongside seed |
| **`artifactGroups`** | `ADMIN_API` | `WAREHOUSE_MANAGER` | Added alongside seed |

## Conclusion
Moqui’s data loader allows Tier 2 (`ext-seed`) Configurable Data to be confidently layered on top of Tier 1 (`seed`) Framework Data. 
*   If the `ext-seed` introduces a new Primary Key, it is seamlessly merged.
*   If the `ext-seed` reuses an existing Primary Key, the `createOrUpdate` mechanism cleanly overrides the base data without crashing the startup process.
