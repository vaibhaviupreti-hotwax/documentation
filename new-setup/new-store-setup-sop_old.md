# New Store Setup SOP — HotWax Commerce OMS (Maarg / Moqui)

**Status:** Draft v1 — derived from the gorjana deployment (platform suite + `gorjana-maarg` + integration connectors), cross-referenced with the legacy OFBiz `hotwax-gorjana` component.
**Last updated:** 2026-06-07
**Audience:** Engineers/operators standing up a new client store on Maarg.

This SOP does two things:
1. Defines the **setup-data ownership model** — who owns which data and when it loads.
2. Gives the **ordered procedure** to bring up a new store, plus the **inputs checklist** a new client must supply.

---

## Part 1 — The setup-data ownership model

Setup data lives in **four layers**. The golden rule: **a component defines TYPES and machinery; the client component supplies VALUES and identity; secrets/credentials are per-deployment runtime config (never in git).**

| Layer | Owned by | Load type | What it is | Customized per store? |
|---|---|---|---|---|
| **L1 — Platform reference (base)** | `ofbiz-oms-udm`, `ofbiz-oms-usl`, `oms`, `poorti`, `order-routing`, `maarg-util` | `seed`, `seed-initial`, `install` | Type systems, status lifecycles, enumerations, GEO/currency/UOM, contact-mech types, security permission defs, artifact groups, service-job templates | **No** — identical for every store |
| **L1b — Platform placeholders** | `ofbiz-oms-udm` (`ProductStoreData.xml`, type `ext`) | `ext` | Demo `ProductStore=STORE`, `Party=COMPANY`, `Facility=CONFIGURATION`, demo `CATALOG`, placeholder carriers/`_NA_`, bootstrap user | **Replaced/overridden** by the client component |
| **L2 — Integration machinery** | `mantle-shopify-connector`, `shopify-oms-bridge`, `shopify-delivery`, `mantle-netsuite-connector`, `aftership` | `ext-seed` | `SystemMessageType` defs (feeds/webhooks), integration-type **enumerations** (`NETSUITE_SHP_MTHD`, `NETSUITE_PMT_MTHD`, `NETSUITE_DMGD_LOC`…), empty `SystemMessageRemote` templates, service-job defs, webhook handlers | **No** (defs) — but each needs per-store **config rows + credentials** (L3/L4) |
| **L3 — Client setup data** | client component (e.g. `gorjana-maarg`) | `ext-seed` (+ `ext-upgrade` mirror) | Store **identity** (company, ProductStore, facilities, facility groups), **business rules** (return types/reasons, shipping rate rules, damage-location mappings), and integration **mapping values** (`IntegrationTypeMapping` NetSuite IDs, `ShopifyShop` + `ShopifyShopTypeMapping`) | **Yes** — this IS the store |
| **L4 — Runtime secrets & deploy config** | deployment (DB/API, **not** git) | n/a (entered live) | Credentials in `SystemMessageRemote` (Shopify token, NetSuite TBA, AfterShip key), `Facility.externalId` (NetSuite location IDs), sync-bookmark `SystemProperty` values, job enable/cron | **Yes** — secret, per environment |

### The connector-defines-types / client-supplies-values split (the crux)

This is the most important pattern to internalize:

- `mantle-netsuite-connector` **defines** the integration-type enumerations (`NETSUITE_SHP_MTHD`, `NETSUITE_PMT_MTHD`, `NETSUITE_DMGD_LOC`, `NETSUITE_GIFT_CARD`, …) and the feed/job machinery — **no client IDs**.
- `gorjana-maarg` **supplies** the `IntegrationTypeMapping` rows: *"in our NetSuite, shipping method `STANDARD` = `2830`, payment `EXT_SHOP_VISA` = `24`, damage `RTN_DMG_PLT` = location `84`."*
- Same for Shopify: the connector defines `ShopifyShop*` entities + `SystemMessageType`s; the client supplies the `ShopifyShop` row (`shopId`), the `ShopifyShopTypeMapping` rows (payment/order-source/product-type), and location/carrier mappings.

→ A new client reuses **all** of L1 and L2 unchanged, writes their own **L3**, and configures **L4** at deploy time.

### Load order (how the data lands correctly)

1. **Component dependency order** (`component.xml` `depends-on`): `ofbiz-oms-udm` → `ofbiz-oms-usl`/`oms` → `maarg-util`/`order-routing` → `poorti` → connectors → **client component last** (`gorjana-maarg` depends-on `shopify-delivery`, `poorti`).
2. **Within a component, by load type:** `seed`/`seed-initial` (first install) → `install`/`ext`/`ext-user` (install+upgrade) → `ext-seed` (install only).
3. **Within a type, alphabetical by filename.** This is why the client component prefixes files to force order: `A1CompanyPartyData.xml` (creates `Party COMPANY`) **must** load before `A2ProductStoreData.xml` (ProductStore FK → company). Follow the `A1/A2…` convention for any FK-dependent client data.
4. `ext-seed` is **not** applied on upgrades — anything that must reach existing environments needs an `ext-upgrade` mirror (see `maarg-sd/CLAUDE.md`).

---

## Part 2 — New store setup procedure

> Verification environment for reference: `/Users/anilpatel/maarg-sd/gorjana` (run via `./gradlew run`).

### Phase 0 — Provision the instance & components
- Stand up the Moqui framework + runtime (HotWax fork). JDK 11.
- Install the OMS suite component set and connectors:
  `./gradlew getComponentSet -PcomponentSet=oms-suite` then `getComponent` for `mantle-shopify-connector`, `shopify-oms-bridge`, `shopify-delivery`, `mantle-netsuite-connector`, `aftership`.
- Create/clone the **client component** (e.g. `notnaked` or `<client>-maarg`) using `gorjana-maarg` as the template (its `data/` file set is the canonical L3 checklist).
- Configure the datasource (`runtime/conf/MoquiDevConf.xml` / production conf).

### Phase 1 — Load platform reference data (L1) — *reused as-is*
- A first install (`./gradlew load -Ptypes=seed,seed-initial,install` or fresh-DB auto-load) brings in **all L1 reference data**: types, status flows, enumerations, GEO, currency, UOM, security permissions, artifact groups, service-job templates.
- **Do not customize.** Confirm the demo `STORE`/`COMPANY`/`CONFIGURATION` placeholders loaded (L1b) — the client component will override them.

### Phase 2 — Author client setup data (L3) in the client component
Create/adapt these `data/*.xml` files (load type `ext-seed`, ordered by filename). Modeled on `gorjana-maarg/data/`:

| Order | File (convention) | Defines | New-client action |
|---|---|---|---|
| A1 | `A1CompanyPartyData.xml` | Company `Party`/`PartyGroup` + roles | **Replace** with client legal entity, name, roles |
| A2 | `A2ProductStoreData.xml` | `ProductStore` (+ `ProductStoreShipmentMeth`, settings) | **Replace** store id/name, `payToPartyId`, `inventoryFacilityId`, default locale/currency/channel, approval statuses |
| — | `FacilityData.xml` *(NEW — see Gap #1)* | Operational warehouses/stores (`Facility`) | **Create** — neither platform nor `gorjana-maarg` ships real facilities |
| — | `*SeedData.xml` (store settings, facility groups, sales channels, special parties) | Facility groups, `ProductStoreSetting`, sales channels, return special-customers | **Configure** to client policy |
| — | `ReturnReasonData.xml` | `ReturnType`, `ReturnReason`, `ReturnTypeReason` | **Configure** client return policy |
| — | `ShippingData.xml` + `ShippingRateRulesData.xml` | Carriers, `ShipmentMethodType`, rate thresholds/rules | **Configure** client carriers & rates |
| — | Security groups/permissions | `SecurityGroup`, `SecurityGroupPermission` (e.g. store-manager role) | **Configure** (note Gap #2) |

Load order ties to FK dependencies: company → product store → facilities → facility groups/settings → returns/shipping.

### Phase 3 — Integration mapping values (L3, integration side)
Still in the client component (`ext-seed`):

- **NetSuite** — `NetSuiteIntegrationTypeData.xml`: one `IntegrationTypeMapping` row per shipping method, payment method, price level, discount method, damage/discontinued location, gift card → **the client's NetSuite internal IDs**. Plus `NetSuiteDamageFacilityData.xml` (damage sub-location facilities) and `NetSuiteFloorDamageLocationMappingData.xml` (AfterShip reason → NS location).
- **Shopify** — `ShopifyShop` row (`shopId`, `productStoreId`), `ShopifyShopTypeMapping` rows (`SHOPIFY_PAYMENT_TYPE`, `SHOPIFY_ORDER_SOURCE`, `SHOPIFY_PRODUCT_TYPE`, …), `ShopifyShopLocation` (Shopify location → OMS facility), `ShopifyShopCarrierShipment` (Shopify method → OMS carrier+method).

### Phase 4 — Runtime credentials & deploy config (L4) — *never in git*
Set these **live** (via admin UI / REST / DB), per environment:

- **Shopify** `SystemMessageRemote` (e.g. `ShopifyConfig`): `sendUrl` (`https://<shop>.myshopify.com/admin/api/<version>`), access token (`password`/`sendSharedSecret`), webhook `sharedSecret`, `accessScopeEnumId`. Register webhooks; configure feed SFTP remote + `SystemMessageTypeParameter` overrides.
- **NetSuite** `SystemMessageRemote` (`NS_SCRIPT_RESTLET`, `NETSUITE_REST_API`): account id, TBA consumer key/secret + token id/secret, base URLs. Set `Facility.externalId` = NetSuite location id for each facility in the NS/floor-damage flow. Set sync-bookmark `SystemProperty` values (`netsuite_order_sync_from_date`, …).
- **AfterShip** `SystemMessageRemote` (`AFTERSHIP`): `sendUrl=https://api.aftership.com`, API key (`privateKey`), `authHeaderName=as-api-key`. Register the warranty webhook endpoint; set `shopId` parameters on the warranty `SystemMessageType`s.
- Secret fields on `SystemMessageRemote` use Moqui field-level `encrypt="true"` (framework ships `OmsEntityCrypto`) — **confirm the encryption key is configured** for the environment so secrets are encrypted at rest.

### Phase 5 — Activate jobs & enable
- Enable/cron the relevant `ServiceJob`s (Shopify order/inventory/fulfillment sync, NetSuite feeds `NS_EXP_*`/`NS_IMP_*`, ADP worker history, etc.). They ship `paused`/disabled — turn on per store.

### Phase 6 — Verify
- Confirm `ProductStore`, company, facilities resolve; place a test order through the Shopify path; run a NetSuite feed dry-run; fire an AfterShip test webhook; print a picklist/packing slip. Use the running Maarg instance to validate before go-live.

---

## Part 3 — "What a new client must provide" (inputs checklist)

Hand this to the client / collect before Phase 2:

**Identity**
- [ ] Legal company entity (name, addresses, tax IDs) → `Party COMPANY`
- [ ] Product store id + name, default currency/locale/sales channel → `ProductStore`
- [ ] Operational facilities: warehouses, retail stores, DCs (ids, addresses) → `Facility` *(Gap #1)*
- [ ] Facility groups / routing tiers (priority/volume/warehouse) → facility groups

**Business rules**
- [ ] Return types & reasons (policy) ; return channels
- [ ] Carriers + shipping methods + rate thresholds
- [ ] Security roles/permissions for client staff

**Integration mapping values**
- [ ] NetSuite internal IDs: shipping methods, payment methods, price level, discount methods, damage/discontinued locations, gift card item; facility → NS location ids
- [ ] Shopify: `shopId`, domain, payment-method names → OMS types, sales-channel ids → OMS channels, product-type strings, location ids → facilities, checkout shipping methods → OMS carriers
- [ ] AfterShip: warranty page→channel names; floor-damage reason codes

**Runtime secrets (collect securely; enter in L4, not git)**
- [ ] Shopify access token + webhook secret + granted scopes
- [ ] NetSuite TBA (consumer key/secret, token id/secret, account id, base URLs)
- [ ] AfterShip API key
- [ ] SFTP / AWS SQS credentials for feeds (if used)

---

## Part 4 — Gaps & cautions (carry into the SOP)

1. **No operational Facility records are shipped** — platform ships only the `CONFIGURATION` placeholder; `gorjana-maarg` ships facility *groups* and *damage sub-locations*, not real warehouses/stores. **Every new store must author a `FacilityData.xml`.** This is the most common omission.
2. **Security/permission parity** — the legacy OFBiz component had a detailed `HG_STORE_MANAGER` permission set; the Moqui side has a thinner artifact-group model. Confirm client staff roles are fully expressed before go-live.
3. **`ProductStore` id is referenced widely** — `gorjana-maarg` reuses id `STORE` (anchored by `ShopifyShop`, facility groups, shipment methods). If a deployment hosts multiple stores, ids must be unique and references updated consistently.
4. **`ext-seed` ≠ upgrades** — store data that must reach already-installed environments needs an `ext-upgrade` mirror.
5. **Secrets discipline** — credentials belong in L4 (`SystemMessageRemote`, encrypted), never in committed `data/*.xml`. Demo/seed files ship those fields **empty** on purpose.
6. **Rippling is retired** (→ ADP); don't carry Rippling config into new stores. SAML SSO is platform-level (`moqui-sso`).

---

## Source references
- Platform: `runtime/component/{ofbiz-oms-udm,ofbiz-oms-usl,oms,poorti,order-routing,maarg-util}/data` & `component.xml`
- Integration: `runtime/component/{mantle-shopify-connector,shopify-oms-bridge,shopify-delivery,mantle-netsuite-connector,aftership}/data`
- Client (template): `runtime/component/gorjana-maarg/data` (esp. `A1CompanyPartyData`, `A2ProductStoreData`, `NetSuiteIntegrationTypeData`, `GorjanaSeedData`)
- Legacy reference: `hotwax/hotwax-gorjana` (OFBiz) `data/`
- Load-type rules & domain patterns: `maarg-sd/CLAUDE.md`, `docs/udm-domain-object-practices.md`
