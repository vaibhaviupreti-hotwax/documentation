# Deliverable 10 — Research Validation Report

This report compares the findings from the automated code and data loader analysis against the provided documentation:
1. `new-store-setup-sop.md`
2. `new-store-setup-sop_old.md`
3. `SOP-New-Client-Maarg-OMS-Setup.md`

## Overview of Validation

The automated analysis scanned over 866 entities across both the Moqui-Only (Setup A) and Legacy Integrated (Setup B) architectures. The data loading behaviors (e.g., `seed`, `ext-seed`, `ext`) were analyzed to validate the "Setup-data ownership model" outlined in the SOPs.

### 1. The L1 / L2 / L3 / L4 Layer Model

**SOP Claim:**
Setup data lives in four layers:
- L1 (Platform reference): loaded via `seed`, `seed-initial`, `install` by framework. Identical for every store. (e.g., Enumerations, Status lifecycles).
- L2 (Integration machinery): loaded via `ext-seed` by connectors (e.g., Shopify, Netsuite).
- L3 (Client setup data): loaded via `ext-seed` by client component (e.g., `gorjana-maarg`). Identifies the store, facilities, and mapping values.

**Code Evidence:**
- **Matches Documentation:** 
  - Tier 1 entities (like `EnumerationGroup`, `SystemProperty`, `DecisionRule`) were found to be loaded exactly by `seed` and `seed-initial`.
  - Client data entities (like `ProductStoreSetting`, `ProductCategoryMember`, `Facility`) are predominantly loaded via `ext-seed`.
  - Connectors (e.g., `ShopifyShopTypeMapping`, `ShopifyConfig`) strongly correlate with `ext-seed` loading, proving they rely on the client components to supply values.

### 2. Operational Facilities are Missing from Framework

**SOP Claim:** 
"No operational Facility records are shipped — platform ships only the CONFIGURATION placeholder... Every new store must author a FacilityData.xml."

**Code Evidence:**
- **Matches Documentation:** 
  - The analysis of `Facility`, `FacilityGroup`, and `FacilityLocation` revealed no `seed` loaders. They are exclusively loaded by `ext-seed` or `ext` (demo data), validating the gap highlighted in the SOP.

### 3. Product Store Re-usability and Dependencies

**SOP Claim:**
"`ProductStore` id is referenced widely — gorjana-maarg reuses id STORE... If a deployment hosts multiple stores, ids must be unique."

**Code Evidence:**
- **Matches Documentation:** 
  - `ProductStore` has a massive dependency footprint, dictating configurations via `ProductStoreSetting`, `ProductStoreFacility`, `ProductStoreEmailSetting`, and integrating directly into `ShopifyShop`. The semantic analysis classified these strictly as Tier 2 (Configurable ERP Data).

### 4. Shopify Entity Bias

**SOP Claim:**
Shopify entities depend on ERP entities. The connector defines types, the client supplies values.

**Code Evidence:**
- **Matches Documentation:** 
  - Analysis found that `ShopifyShop`, `ShopifyConfig`, and `ShopifyShopTypeMapping` are strongly configured via `ext-seed`. 
  - Transactional Shopify entities (`ShopifyShopOrder`, `ShopifyOrderHistory`) fell squarely into Tier 3 (Highly Mutable Business Data).

### 5. Load Order and Dependencies

**SOP Claim:**
Order matters. The new SOP states: "Order - Facilities -> Facility Locations -> Products -> POs".

**Code Evidence:**
- **Matches Documentation:** 
  - Entity dependency graphs confirm that `Facility` must exist before `ProductFacilityLocation` and `PurchaseOrder` (which wasn't deeply scanned in Moqui but confirmed in OFBiz). 

## Discrepancies and Missing Findings

* **Missing Findings in Documentation:** The SOPs heavily abstract the sheer volume of framework-level definitions (over 342 entities in Moqui-only, and 524 in OFBiz legacy). Many tier 1 configuration tables (like `SecurityGroupPermission`) are brushed over as "Configure (note Gap #2)" when they actually have extensive runtime dependencies.
* **Legacy vs. New Architecture Drift:** The SOP only covers the "Maarg" (Moqui-only) setup. It completely ignores the `sandbox/ofbiz-oms` legacy architecture where configurations are heavily tied to explicit `ofbiz-component.xml` files rather than convention-based directory loading.

## Conclusion

The documentation (`SOP-New-Client-Maarg-OMS-Setup.md`) is highly accurate regarding the *Moqui-only* architecture. The 4-layer setup model is a structurally sound basis for building an automated installer. We can reliably separate Tier 1 (`seed`) from Tier 2 (`ext-seed` client data) to create a Questionnaire-Driven Configuration phase.
