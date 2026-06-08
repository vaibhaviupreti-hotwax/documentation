# Final Result: Entity Classification Catalog

Based on the investigation into both Setup A and Setup B, as well as the Moqui Entity Engine's idempotent loading sequence, entities are classified into the following 3 Tiers for the automated installer.

## Tier 1: Immutable Core Framework (Seed Data)
These entities represent the foundation of the ERP. They are loaded purely by the framework's `seed` and `seed-initial` data loaders. They do not overlap with client configurations and must be loaded first to establish the database schema and structural references.

**100% Immutable Entity:**
- `EntityAuditLog` (Strictly configured with `create-only="true"` schema lock).

**Framework Structural Entities (Seed Only):**
- `ProductCategoryType`
- `VarianceReason`
- `FacilityType`
- `Uom` (Unit of Measure)
- `PartyRelationship`
- `ReturnAdjustmentType`
- `GoodIdentificationType`

## Tier 2: Configurable & Merged Data (Ext-Seed)
These entities form the "Setup" layer. They have base definitions in the framework (`seed`), but are actively customized and extended by client integrations (e.g., `gorjana-maarg/ext-seed/`). During startup, Moqui uses an idempotent `createOrUpdate` mechanism to safely merge these files.

**Additive Merge (No Primary Key Overlap):**
*The client `ext-seed` files introduce entirely new Primary Keys alongside the framework defaults.*
- `ContactMech` (e.g., `HAPPINESS_LOCATION`)
- `DataManagerConfig` (e.g., `SYNC_SHOPIFY_ORDER`)
- `EnumerationType` (e.g., `RULE_CONDITION_TYPE`)
- `Facility` (e.g., `GRJ_DMG_FL_CLOSURE`)
- `PartyIdentificationType` (e.g., `ADP_WORKER_ID`)
- `ServiceJob` (e.g., `sync_NetSuiteItemReceipts`)
- `StatusFlowTransition`
- `StatusItem` (e.g., `SHIP_RULE_ACTIVE`)
- `StatusType`
- `SystemMessageRemote` (e.g., `WONDERMENT_CONFIG`, `AFTERSHIP`)
- `SystemMessageType`
- `artifactGroups`

**Upsert Override (Primary Key Overlap):**
*The client `ext-seed` files reuse a Primary Key to intentionally override the framework's base definition.*
- `Enumeration` (Overriding `ECOM_RTN_CHANNEL`, `POS_RTN_CHANNEL`)
- `ProductStoreSetting` (Overriding `STORE` configurations)
- `ShipmentMethodType` (Overriding `SECOND_DAY` to remap to Shopify's naming)

## Tier 3: Transactional Sync Data
These entities represent volatile business records. They are never managed by the Docker XML Data Loaders. They are populated entirely via runtime APIs and synchronization services (e.g., Webhooks, System Messages).
- `OrderHeader`
- `OrderItem`
- `InventoryItem`
- `Shipment`
- `ProductReview`
- `ReturnHeader`

## Conclusion for Installer
The installer must orchestrate the deployment sequence securely:
1. **Phase 1:** Load Tier 1 (`seed`, `seed-initial`).
2. **Phase 2:** Inject Tier 2 (`ext-seed`) components, confident that Moqui's idempotent engine will merge without crashing.
3. **Phase 3:** Open Webhooks/API gateways to begin syncing Tier 3 transactional data.
