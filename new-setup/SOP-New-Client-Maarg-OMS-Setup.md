SOP: New Client OMS (Maarg) Setup & Data Onboarding
Purpose. Standardize how we onboard a new client onto the Maarg OMS — from collecting business data, to preparing and loading data files, to verifying the system is ready for go-live. This SOP is written to be repeatable across many stores/brands/markets in a single engagement (the model proven on ADOC, which spanned multiple brands across five countries).

Scope. Applies to every new client instance and to each new brand, market, or batch of stores added to an existing instance. Covers OMS instance configuration, Shopify connection, data-file preparation, EXIM/ImportData loading, and pre-go-live verification.

Owner. Implementation / Onboarding team. Engineering supports environment and integration steps.

Status. Draft v0.1 — synthesized from existing HotWax Drive documentation (see Source Documents at the end). Sections marked [CONFIRM] need a process owner to validate before this becomes official.


0. How to use this SOP
The onboarding runs in five stages. Each stage has an entry gate (what must be true before you start) and an exit gate (what must be verified before moving on). Do not skip the load sequence in Stage 3 — it exists because later entities depend on earlier ones (e.g. POs reference suppliers and facilities that must already exist).

Stage
Name
Outcome
1
Intake & discovery
All client business data collected and confirmed
2
Instance & integration setup
OMS instance live, Shopify connected, mappings done
3
Data-file preparation & load
All master and transactional data loaded in sequence
4
Verification
Data reconciled, exceptions cleared
5
Go-live readiness
Department checklists passed, sign-off obtained



1. Stage 1 — Intake & Discovery
Goal: collect every piece of client business data needed before any configuration begins. This is the front end the existing setup guide refers to as the "client onboarding form."
1.1 Company & legal
Collect and record:

Legal company name, brand/trade name (this appears on packing slips and system emails)
Company logo (high-resolution)
Registered business address (primary)
Primary contact emails and phone numbers
Operating countries (drives DBIC, tax, shipping, address validation)
Base currency, country, and — for non-US retailers — weight units (kg vs lbs)
1.2 Commercial structure
List of brands to set up
List of markets/countries each brand sells in
The brand × market matrix (this defines the rollout scope — see ADOC model in §6)
Sales channels in use (e.g. web, POS, mobile/android, marketplaces)
Payment methods accepted (e.g. PayPal, Afterpay, credit card)
1.3 Facilities / stores
For each warehouse and retail store (this is the bulk of the work for multi-store clients):

Facility name (must match the Shopify location name exactly)
Facility type (WAREHOUSE or RETAIL_STORE)
Full address including zip code (critical — drives zone-based carrier routing)
Phone number (used on carrier labels)
Latitude & longitude (required for distance-based brokering and BOPIS store lookup)
Operating hours and time zone
Fulfillment role: ships online orders? offers pickup (BOPIS)? uses native fulfillment app or external WMS? days-to-ship; daily fulfillment capacity
Shopify Location ID (from Shopify Admin → Settings → Locations)

Tip for many stores: capture all of the above in one spreadsheet up front. It becomes the source for the IMP_FACILITY and 2-Facility-Locations files in Stage 3, and avoids re-collecting data per store.
1.4 Source systems & integrations
E-commerce platform (Shopify assumed; confirm version/plan)
ERP / product master source (e.g. NetSuite) — or whether products originate in Shopify
WMS, if any
SFTP credentials / file-exchange method, if the client delivers data files
Carrier accounts and shipping methods used
1.5 Catalog & inventory
Product master source and identifier convention (SKU vs UPCA)
Special product types (gift cards → DIGITAL_GOOD; kits / BOMs / assemblies / non-inventory items)
Brand-name handling (no direct brand sync from NetSuite/Shopify — plan for the IMP_PRD_BRAND_NAME correction step)
Suppliers / vendors list (needed for PO load)
Inventory snapshot source and cut-over timing
1.6 Order policy / business rules
Sales order ID prefix (e.g. HC-)
Auto-approve orders? auto-cancel days?
BOPIS partial-order rejection policy, brokering shipment threshold, customer self-service (cancel / change address / change pickup) flags
Returns restocking facility, default carrier

Exit gate (Stage 1): Intake spreadsheet complete and signed off by the client. Admin credentials for the OMS instance obtained from the HotWax support team.


2. Stage 2 — Instance & Integration Setup
Reference: hotwax-commerce-setup-guide (the canonical step-by-step). Below is the sequenced summary.
2.1 Initial OMS setup (Phase 1)
Log in at /commerce/control/main; reset the default password immediately.
Create dedicated admin users; disable the default user.
Update Company Profile (ViewParty?partyId=COMPANY): name, logo, status Enabled, primary address, emails/phones, role (e.g. INTERNAL_ORGANIZATIO).
Add DBIC for each operating country (Settings → DBIC Configuration).
For non-US retailers, set System Property Data (ImportData?configId=SETUP_SYSTEM_PROPERTY): currency, country, shipment weight units.
2.2 Shopify shop setup (Phase 2)
Installing the HotWax Commerce Shopify app auto-creates a Shopify Shop record in OMS.

Verify the Shopify Shop record exists (ViewShopifyShop?shopId=<id>).
Set Shopify access scope to Read and write.
Link the Shopify Shop to the correct Product Store (do this before order/inventory sync).
Configure product type mappings before the first product download (e.g. Gift Card → Digital Good).
Configure sales channel mappings (web, pos, android → OMS equivalents).
Configure payment method mappings.
Import Shopify shipping methods → map each to an OMS carrier + shipment method.
Import Shopify locations → create/map corresponding OMS facilities (one-to-one).
Trigger the initial order sync.
2.3 Product Store & General Settings (Phase 3)
Set Product Store name to the brand name (ViewStore?productStoreId=<id>).
Configure currency, auto-approve order, auto-cancel days, sales order ID prefix, product identifier (SKU/UPCA).
Do not change these defaults unless instructed: Enable Brokering (Y), Reserve Inventory (Y), Explode Order Items (Y).
Set advanced Product Store settings per §1.6 (e.g. BOPIS_PART_ODR_REJ, BRK_SHPMNT_THRESHOLD, CUST_ALLOW_CNCL, DEFAULT_CARRIER).
Confirm General Settings (/GeneralSettings): default country/currency, date formats, mail notifications, base URL, image management URL.
Add shipping methods to the Product Store (carrier + shipment method + gateway).

Exit gate (Stage 2): Shopify Shop linked to Product Store; mappings (channel, type, payment, shipping, locations) complete; test order syncs successfully.


3. Stage 3 — Data-File Preparation & Load
All bulk data enters the OMS via EXIM / ImportData, each import keyed by a configId. Download the sample template for each config, fill it from the Stage 1 intake spreadsheet, and import at the same URL. Load in the sequence below — the numeric prefixes on our standard templates (2-…, 10-…) encode this dependency order.
3.1 Standard load sequence
Order
Entity
Template / config
Key columns
1
Facilities
IMP_FACILITY
Facility ID, External Facility ID, Facility Name, Facility Type ID (RETAIL_STORE / WAREHOUSE), Address, Phone, Facility Group, Product Store
2
Facility storage locations
2-Facility-Locations.csv
warehouse-id, area-id, aisle-id, section-id, level-id, position-id
3
Facility calendars
calendarDataSetup.csv
calendar-id, description, per-day start time + capacity (Mon–Sun)
4
Products
NetSuite/Shopify sync (see §3.3)
—
5
Product brand names (correction)
IMP_PRD_BRAND_NAME
SKU, Brand Name
6
Product–facility stock rules
importProductFacility.csv
facility-id, facility-external-id, product-id, product-sku, facility-minimum-stock, reorder-quantity
7
Suppliers
[CONFIRM config — load before POs]
supplier external-id, name, contact
8
Requirements (demand)
requirementDataSetup.csv
requirement-id, requirement-type-id, facility-id, product-id, description, quantity, start-date, by-date, status-id
9
Inventory snapshot
[CONFIRM mechanism — sync vs import]
product, sku, facility, QOH/ATP
10
Purchase orders
10-poDataSetup.csv
external-id, supplier-external-id, product-store-id, facility-id, sku, quantity, buying-uom (QTY_ea / QTY_CASE), unit-price, arrival-date, units-included


Legacy PO template purchaseOrderDataSetup.csv (po_number, product_cd, open_po_qty, location_cd, availability_date, Landed_cost, status_id, new_style_po) predates 10-poDataSetup.csv. Use the 10- version for new clients unless a client-specific reason requires the legacy layout.
3.2 Facility groups (after facilities load)
Create the system facility groups and add facilities to each:

BROKERING — eligible-for-routing facilities; sequence/priority matters (drag-drop order).
CHANNEL FAC GROUP — facilities whose inventory contributes to online ATP.
PICKUP — facilities offering BOPIS.
Plus, as needed: Same Day Shipping, OMS Fulfillment, Generate Shipping Label.

Then map each facility to its Shopify Location ID via Facility Details → External Mappings, and associate each facility with the correct Product Store (mark the brand's main facility as Primary).
3.3 Product sync (NetSuite or Shopify source)
Reference: SOP: Product Setup.

NetSuite → OMS: create product in NetSuite (keep "Sync Product to HotWax" unchecked until validated) → validate active → run export script HC_MR_ExportSyncNewProduct (id 7311) or wait for the 15-min job → after ~10 min verify in PIM: NetSuite Product Identification, NetSuite Sales Description, Shopify Product Identification.

Shopify → OMS: create product in Shopify → Job Manager → Product → "Import New Product" → verify the same PIM identifiers.

Brand names: there is no direct brand-name sync. Use the Tathya/Superset "Missing Brand Name" report → export SKUs → fill brand names → upload via IMP_PRD_BRAND_NAME. (Missing brand names break category-based pick-wave filters.)

Common fixes:

Missing NetSuite Product Identification → run NetSuite Generate/Upload Product jobs, then Product Identification Job; verify file IMP_PROD_IDENT.
Missing Sales Description → run Generate (6489) / Upload (6490) Sales Description jobs, then Import NetSuite Sales Description Job; verify NETSUITE_SALES_DESC.

Exit gate (Stage 3): every file in §3.1 imported with Processed status (no Pending/errors); facility groups populated; products visible in PIM with correct identifiers.


4. Stage 4 — Verification
Reference: Verify Production Data Import workbook.

Facility inventory check — export FacilityInventory (Product ID, SKU, Facility ID, Total ATP, QOH, Minimum Stock, Max Order Limit, Pending Qty) and reconcile against the client's snapshot.
Brokered/online inventory check — export FacilityGroupInventory (queues, excluded ATP, Total ATP/QOH, Threshold, Online ATP) and confirm online-sellable quantities are correct.
Product transformation exceptions — clear "component not found" / "type missing" items (e.g. marketing-package SKUs not mapping to their kit product IDs).
Catalog reconciliation — compare imported product catalog against the source export (name, type, price, channels, categories, URL, etc.).
Order flow smoke test — place a test order, confirm brokering, fulfillment routing, and that it syncs back to Shopify/NetSuite.

Exit gate (Stage 4): inventory reconciles; zero unresolved transformation exceptions; test order completes end-to-end.


5. Stage 5 — Go-Live Readiness
Reference: SOP List by Department (go-live readiness checklist). Confirm each department can perform its core operations before sign-off:

Product Development — create product, create category, create/update BOMs
Purchase Orders — create suppliers (by CSV), attach product to supplier, create/update POs, send PO emails, min/max stock by facility
Warehouse — receive PO (over/under), undo receive, put away, replenishment, move stock
Inventory — cycle count, adjustments, lookup, min/max by location
Picking / Packing — pick by area, packing cart, label/notecard re-print
Troubleshooting — void shipment, undo pick wave, transfer orders between facilities, change ship-via, run pick-wave schedulers

Run department demos and SOC training per the readiness schedule, then obtain client sign-off to go live.

Exit gate (Stage 5): all department checklists green; training complete; sign-off recorded.


6. Running this at scale (the ADOC pattern)
ADOC proved the repeatable model: one engagement covering multiple brands (ADOC, CAT, Hush Puppies, Par2, The North Face) across multiple markets (El Salvador, Guatemala, Nicaragua, Costa Rica, Honduras), each brand × market combination rolled through UAT then PROD on a scheduled wave.

What makes it repeatable:

One intake spreadsheet per engagement, with a row per facility/store, drives all the Stage-3 CSV files. Collecting facility data once (address, geocode, hours, Shopify Location ID) is what lets us stamp out dozens of stores quickly.
Bulk CSV import via EXIM (IMP_FACILITY + 2-Facility-Locations) instead of creating facilities one at a time. This is the single biggest time-saver for high store counts.
A brand × market rollout matrix tracking UAT and PROD status per combination, so waves go live on a schedule without losing track of any store.
The fixed load sequence (§3.1) applied identically to every brand, so the process is mechanical and reviewable.

Recommended tracker columns: Brand · Market/Country · # Facilities · UAT date · UAT status · PROD date · PROD status · Owner.


7. Quick reference — EXIM config IDs & URLs
Purpose
Path / config
OMS login
/commerce/control/main
Company profile
ViewParty?partyId=COMPANY
Shopify shop
ViewShopifyShop?shopId=<id>
Product store
ViewStore?productStoreId=<id>
General settings
/GeneralSettings
Import facilities
ImportData?configId=IMP_FACILITY
System property setup
ImportData?configId=SETUP_SYSTEM_PROPERTY
Brand-name import
ImportData?configId=IMP_PRD_BRAND_NAME
Product identification
configId=IMP_PROD_IDENT
Sales description
configId=NETSUITE_SALES_DESC



8. Open items to confirm before publishing
[CONFIRM] Supplier load template/config ID and its exact position in the sequence (must precede PO load).
[CONFIRM] Inventory snapshot mechanism for go-live (initial Shopify sync vs. dedicated import file) and cut-over timing.
[CONFIRM] Whether a formal client intake form already exists; if so, link it here and align §1 to its fields.
[CONFIRM] Role ownership per step (which steps are client-side vs. HotWax-side).
[CONFIRM] Where SFTP/NiFi fit for clients delivering files via SFTP (production NiFi setup docs exist per-client, e.g. Krewe/NEC/UCG).


Source Documents (HotWax Google Drive)
hotwax-commerce-setup-guide — 4-phase OMS instance + Shopify + Product Store + Facility setup. https://docs.google.com/document/d/1SsfB2AW6VvVpDH6VELv1PWjEaGOdEFBdLmmqwy1N68o/edit
SOP: Product Setup — NetSuite/Shopify product sync, brand-name fix, troubleshooting. https://docs.google.com/document/d/1Dhp5n6yn9JzZd4kdP8zkDHGHaGjZ7Hfb6-m-xIdj5ss/edit
ADOC Brand Setup — brand × country rollout matrix (UAT/PROD). https://docs.google.com/spreadsheets/d/1a6lnre6h1T-t9GuQaJsoufb7lhnNe_lcHydyy2RfKM0/edit
Verify Production Data Import — post-import verification workbook. https://docs.google.com/spreadsheets/d/1CZMaw0soip9fle-1ILVo_EnokM6g2hdh04DURoZWef0/edit
SOP List by Department — go-live readiness checklist. https://docs.google.com/spreadsheets/d/1EIO4Cq08Wq7MUaxBKTctGV71lYqPVkc9YSTw0nkkShk/edit
Import Sales Order Data — order import spec (legacy/N2N reference). https://docs.google.com/document/d/1tTvi_jowKA7THRuVJXL4gTvRHaYUHUymb28Wa6a6oRM/edit
Moqui-Maarg Setup — developer environment runbook (not client onboarding). https://docs.google.com/document/d/14onS2A_qr7Cbk_pfU7ZjhJKOWH0vZ-LwMqWwWqXe2M8/edit
Data-file templates: 2-Facility-Locations.csv, importProductFacility.csv, requirementDataSetup.csv, calendarDataSetup.csv, 10-poDataSetup.csv, purchaseOrderDataSetup.csv.

