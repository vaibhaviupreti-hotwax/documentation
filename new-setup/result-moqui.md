# Final Result: Setup A (Moqui-Only Architecture)

## 1. Architecture Overview
Setup A represents the modernized, Moqui-native ERP architecture. It completely decouples from the legacy OFBiz monolithic data model, dropping hundreds of unused entities (e.g., `ShoppingList`, `Survey`, `Subscription`). The architecture is highly component-driven, heavily relying on the `mantle-udm` (Universal Data Model) and custom integrations like Shopify.

## 2. Data Loading Sequence & Strategy
In the Moqui-Only setup, data ownership is strictly layered (The L1-L4 model):
- **L1 (Platform Reference):** Loaded via `seed` and `seed-initial` types. These reside in `moqui-framework/framework/data` and `mantle-udm/data`. They define the unchangeable core of the system (e.g., `StatusType`, `EnumerationType`).
- **L2 / L3 (Client Config & Integration):** Loaded via `ext-seed` types. These reside in downstream client components like `gorjana-maarg/data/`. 

**The Component Loading Advantage:**
Because Moqui's data loader inherently processes files in **component dependency order** before sorting alphabetically, the framework guarantees that `mantle-udm` seed data loads *before* `gorjana-maarg` ext-seed data. This eliminates the need for the hacky `A1_`, `A2_` file prefixes seen in legacy systems.

## 3. Entity Classification (Tiers)

### Tier 1: Core Framework (Immutable / Seed-Only)
These entities provide structural integrity and are never modified by client setups.
*   **Create-Only Constraint:** `EntityAuditLog` is the only entity mathematically proven to be 100% immutable at the schema layer (`create-only="true"`).
*   **Seed-Exclusive Entities:** `ProductCategoryType`, `FacilityType`, `ReturnAdjustmentType`, `Uom`, etc.

### Tier 2: Configurable & Merged Data
These entities have base definitions in `seed`, but are actively customized or extended in `gorjana-maarg`'s `ext-seed`. Moqui's idempotent `createOrUpdate` allows them to merge safely.
*   **Upsert Overrides (PK Overlap):** `Enumeration` (e.g., `ECOM_RTN_CHANNEL`), `ShipmentMethodType` (e.g., `SECOND_DAY`), `ProductStoreSetting`.
*   **Additive Extensions (No PK Overlap):** `ContactMech`, `DataManagerConfig`, `Facility`, `PartyIdentificationType`, `ServiceJob`, `SystemMessageRemote`.

### Tier 3: Transactional Data
Volatile business data (Orders, Inventory, Shipments) never defined in XML seed files. Synced exclusively via `SystemMessage` integrations or runtime APIs.

## 4. Shopify Bias
In Setup A, Shopify is treated as a first-class citizen. Entities like `ShopifyShopTypeMapping` and `ShopifyShopCarrierShipment` act as absolute anchors for Tier 2 integration. A new client onboarding requires extensive `ext-seed` configurations explicitly mapped to their Shopify Shop ID.
