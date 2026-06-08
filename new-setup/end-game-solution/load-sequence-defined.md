# The Load Sequence & Data Strategy

## 1. Validation of Your Blueprint
First, I have reviewed the text in `arch-simple-explanation.md`. **It is 100% correct, brilliantly clear, and perfectly summarizes the mechanical reality of the system.** You have accurately captured the idempotent nature of Moqui and exactly how an automated wizard can exploit it to bypass the legacy OFBiz fragility.

---

## 2. Common Data vs. Client Data & The "Dummy" Conflict

You correctly identified that the system ships with "dummy" data. This is located in the **L1b - Platform Placeholders** layer (loaded via `ext` type in files like `ProductStoreData.xml`). It injects placeholders such as:
- `Party`: ID = `COMPANY`
- `ProductStore`: ID = `STORE`
- `Facility`: ID = `CONFIGURATION`

### Will the new data overwrite it or cause conflict?
Because Moqui uses Idempotent UPSERT (`createOrUpdate`), **it will never cause a crash or conflict.** However, what happens to the data depends on how the Wizard is programmed to generate IDs:

1. **The Overwrite Strategy (Single-Tenant):** 
   If the wizard generates XML using the exact same ID (e.g., `<ProductStore productStoreId="STORE" storeName="Gorjana"/>`), Moqui will say *"Ah, STORE already exists!"* and perform an **UPDATE**. The dummy data is cleanly overwritten with the real client data. 
2. **The Append Strategy (Multi-Tenant):** 
   If the wizard generates XML with a new ID (e.g., `<ProductStore productStoreId="GORJANA_STORE" .../>`), Moqui performs an **INSERT**. The old dummy `STORE` simply remains in the database harmlessly and ignored. 

**Recommendation for the Wizard:** If this ERP instance will host *multiple* clients, you must use the Append Strategy to ensure unique IDs. If it hosts one client, the Overwrite Strategy is cleaner.

### What data MUST the Wizard always ask for?
To bring a new client online without conflicting with base setups, the Wizard must generate L3 `ext-seed` data containing:
1. **Store Identity:** Real Legal Company Name, Product Store ID/Name.
2. **Operational Facilities:** Moqui ships *no* real warehouses. The wizard must create actual Facilities.
3. **Integration Mappings:** The NetSuite Location IDs, Shopify Shop IDs, and Carrier mapping translations.
4. **Secrets (L4):** Shopify Tokens and Webhook Secrets (Destined strictly for `.env` files, *not* the XML).

---

## 3. All Data Loading Modes & The Exact Sequence

When the ERP boots up or runs a script like `./gradlew load -Ptypes=seed,ext,ext-seed`, Moqui executes a highly deterministic, 3-dimensional load sequence. 

### Dimension 1: Component Order
The framework reads `component.xml` and builds a graph.
1. Core Framework Components load first.
2. Downstream Client Components (like `gorjana-maarg` or your new Wizard-generated component) load last.

### Dimension 2: Data Readers (Load Types)
Within *each* component, Moqui enforces a hardcoded sequence of Data Load Types. Here are all the names and their sequence:

| Sequence | Load Type | What It Does | Safe for Production? |
| :--- | :--- | :--- | :--- |
| **1** | `seed` | The absolute core L1 logic (Statuses, UOMs, Enum Types). | **Yes** |
| **2** | `seed-initial` | Base data run only once on an empty DB. | **Yes** |
| **3** | `install` | Base framework features and permissions. | **Yes** |
| **4** | `ext` | L1b Extension baseline. *This is where dummy `STORE` loads.* | **Yes** |
| **5** | `ext-seed` | **L2 & L3 Integration/Client Setup.** This is where your Wizard's XML lives. | **Yes** |
| **6** | `ext-user` | Bootstraps initial admin login users. | **Yes** |
| **7** | `ext-demo` | Fake transactional data (Orders, Inventory) for local developer testing. | **NO** (Never in Prod) |
| **8** | `ext-upgrade` | Specialized patches applied to running systems. | **Yes** (Upgrades only) |

### Dimension 3: Alphabetical File Order
Finally, if multiple XML files share the *same* component and the *same* Load Type, Moqui sorts them alphabetically by filename. (This is why the legacy OFBiz architecture used `A1_Company.xml`, `B1_Store.xml`—to force them to load in a specific sequence).

### "Production Load" vs "Developer Load"
*   **Production Load:** When deploying the Wizard to a live production server, the command will strictly be `load types=seed,seed-initial,install,ext,ext-seed,ext-user`. It explicitly omits `ext-demo` so no fake test orders pollute the live database.
*   **Developer Load:** When testing locally, engineers use `load types=all`, which sweeps through every type, including the `ext-demo` fake orders.

---

## Conclusion
By structuring your Wizard to generate XML specifically tagged as `<entity-facade-xml type="ext-seed">`, and placing it in a downstream component, you mathematically guarantee that it will load **after** all the `seed` and dummy `ext` data. Moqui will gracefully upsert your generated data without a single conflict.
