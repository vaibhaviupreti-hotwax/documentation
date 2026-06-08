# Final Result: Setup B (Legacy OFBiz Architecture)

## 1. Architecture Overview
Setup B represents the legacy Hotwax Commerce architecture, which ported the monolithic Apache OFBiz data model (`sandbox/ofbiz-oms`) onto the Moqui framework engine. This architecture contains a vast, highly-coupled schema with hundreds of legacy entities (e.g., `ShoppingList`, `Survey`, `Subscription`) that are often unused by modern workflows but remain present for backward compatibility.

## 2. Data Loading Sequence & Strategy
Unlike Setup A, the Legacy OFBiz architecture relies heavily on artificial file sorting to maintain foreign key integrity during the boot process. 

**The Prefix Sorting Mechanism:**
Because OFBiz data files were historically massive and tightly coupled, dropping them into Moqui's alphabetical data loader caused frequent foreign key crashes (e.g., trying to load a `ProductStore` before a `Facility` existed). To bypass this without rewriting the entire data structure, developers prefixed files sequentially:
- `A1_CommonL10nData.xml`
- `A2_SecurityTypeData.xml`
- `B1_ProductSeedData.xml`

This forces the Moqui `EntityDataLoaderImpl.groovy` to parse the files in a strict alphabetical order that manually resolves foreign key dependencies, bypassing the elegant component-dependency system utilized in Setup A.

## 3. Entity Classification (Tiers)

### Tier 1: Core Framework (Immutable / Seed-Only)
In OFBiz, Tier 1 encompasses a massive dictionary of standard ERP constructs. 
- **System Properties:** The OFBiz setup heavily utilizes `<SystemProperty>` entities to control global configurations (e.g., FedEx API endpoints, order thresholds). These act as critical Tier 1 configuration points.
- **Status Workflows:** Complex legacy `StatusFlowTransition` configurations for order workflows (e.g., Picklist states, Shipment states) are deeply embedded in the base data.

### Tier 2: Configurable & Merged Data
Client customizations (`ext-seed`) in the legacy architecture often require duplicating or mimicking the `A1_`/`A2_` structure to ensure their store-specific overrides load after the base OFBiz seed files. 
- Overrides are still handled by Moqui's idempotent `createOrUpdate()` mechanism, ensuring that store-specific configurations safely replace the defaults without throwing constraints.

### Tier 3: Transactional Data
Standard OFBiz transactional tables (`OrderHeader`, `InventoryItem`, `Shipment`) act as Tier 3. However, due to OFBiz's tightly coupled nature, many transactional flows trigger secondary Entity ECA (Event Condition Action) rules that auto-generate secondary records, making data import much more complex than in Setup A.

## 4. Conclusion & Migration Outlook
The Legacy Setup B requires significantly more manual oversight during data loading due to the alphabetical prefixing hack. The transition to Setup A (Moqui-Only) successfully eradicated the need for this pattern by relying on proper component boundaries and dropping the monolithic OFBiz schemas.
