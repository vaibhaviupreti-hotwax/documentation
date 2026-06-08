# The Self-Serve Onboarding Wizard: Business & Implementation Plan

## 1. The Business Case: Eradicating the PA Bottleneck
Currently, bringing a new client (Brand) online requires manual intervention by Product Associates (PAs). PAs must manually create facilities, map locations, define permissions, and configure environments. This introduces friction, human error, and delays time-to-market.

**The Wizard Strategy:** We will build a "One-Click Self-Serve Wizard" directly accessible by the Brand Associate.
*   **Zero Wait Time:** Brands can configure their ERP instance instantly.
*   **Reduced Operational Cost:** Removes the costly dependency on internal Product Associates for routine onboarding.
*   **Accelerated "Aha!" Moment:** Instead of dropping a new client into a terrifying, blank UI, the Wizard pre-loads "Template Data." The Brand Associate logs in and immediately sees a living system—dummy orders, pre-configured return reasons, and active shipping methods—showing them exactly how the platform operates.

---

## 2. What the Brand Associate Gets (The Pre-Configured UI)
When the Brand Associate completes the 3-minute Wizard form, the system generates and loads an L3 (`ext-seed`) Template package. 

They log into the UI and immediately get:
1.  **A Populated Dashboard:** Pre-configured visual widgets connected to template dummy data.
2.  **Pre-Mapped Facilities:** A "Primary Warehouse" and "Returns Center" already built and linked.
3.  **Active Business Rules:** Pre-loaded Return Reasons (e.g., "Too Small", "Damaged") and Shipping Methods (e.g., "Standard", "Expedited") that they can simply edit rather than creating from scratch.
4.  **Security Artifacts:** Their user account is already mapped to the `STORE_MANAGER` permission groups.

Instead of staring at a blank canvas and needing a PA to explain how to create a Facility, the client simply clicks "Edit" on the pre-made Template Facility and changes the address.

---

## 3. The "Foolproof" Engineering Guarantee: Why it Won't Crash
A critical concern in automated deployments is repeated execution. *What happens if the Brand Associate clicks "Import Data" three times in a row?* 

### Why the Legacy OFBiz Setup Crashed
In the legacy Setup B (OFBiz), running data imports multiple times was highly dangerous. The legacy system relied on strict `INSERT` logic and fragile Foreign Key sequences tied to alphabetical filenames (`A1_Company.xml`). If an associate re-ran a script or files loaded out of order, the database would throw **Duplicate Key Exceptions** or **Foreign Key Constraint Errors**, crashing the application and requiring a PA to manually intervene.

### Why the Modern Moqui Setup is Bulletproof
The Wizard is built exclusively on the Setup A (Moqui-Only) architecture, which utilizes **Idempotent Upsert (`createOrUpdate`)**.
*   **Run 1:** The Wizard generates the XML. The Moqui Data Loader checks the database, sees the IDs do not exist, and executes an `INSERT`.
*   **Run 2 to 100:** If the Brand Associate re-runs the Wizard to fix a typo, Moqui checks the database, sees the IDs already exist, and gracefully executes an `UPDATE` without throwing a single constraint error. 

**This idempotency is the ultimate safeguard.** The Wizard can be run infinitely without corrupting the database or causing duplicate PK crashes.

---

## 4. Implementation Roadmap

To build this capability, Engineering will execute the following 4-Phase Plan:

### Phase 1: The UI Questionnaire (Frontend)
Build a simple, 3-step web form for the Brand Associate:
*   **Step 1:** Brand Identity (Company Name, Store Name).
*   **Step 2:** Shopify Details (Shop ID, Domain).
*   **Step 3:** Logistics (Primary Warehouse Address).

### Phase 2: Template Payload Generation (Backend)
When the form is submitted, a Node.js/Java middleware receives the JSON. It passes this JSON into a templating engine (like Nunjucks, FreeMarker, or Groovy Templates).
*   The template merges the user's answers into a master `SetupData.xml` payload.
*   The template inherently places parent records (Company) before child records (Facilities), ensuring perfect Foreign Key compliance.

### Phase 3: The API Injection (The Data Loader)
The backend does not need to save the XML file to the disk. It can post the XML payload directly to the Moqui Framework's internal REST API for the Data Loader.
*   The `EntityDataLoader` receives the XML string.
*   It executes the Idempotent Upsert across the payload.
*   *Note on Secrets:* Shopify Tokens are extracted from the form and securely written directly to `.env` or the Moqui `SystemMessageRemote` table using field-level encryption, bypassing XML entirely.

### Phase 4: The "Go-Live" Scrub
Because the Wizard loads "Template Data" (dummy orders/products) so the client can learn the UI, we must provide a transition path to Production.
*   Add a "Go Live" button in the UI. 
*   When clicked, it triggers a system service that wipes the Tier 3 Transactional Data (the fake orders and shipments) while preserving the Tier 2 Configuration Data (Facilities, Return Reasons), giving the client a clean slate to begin receiving live Shopify webhooks.
