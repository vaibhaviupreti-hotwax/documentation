# DELIVERABLE 12: Unified Installer Architecture Proposal

## 1. Automated Bootstrap Stages

To achieve rapid, error-free onboarding for new clients, the automated installer must orchestrate the data flow through 5 distinct stages:

1.  **Stage 1 (L1 Load):** Execute framework bootloader. Inject all Tier 1 `seed` and `seed-initial` reference data.
2.  **Stage 2 (L2 Load):** Inject integration connectors (e.g., standard Shopify mapping frameworks, AfterShip Webhook channels).
3.  **Stage 3 (L3 Questionnaire):** Prompt the operator for client-specific details (Store Name, Shopify ID, Facility mapping) to dynamically generate L3 `ext-seed` configurations.
4.  **Stage 4 (L3 Load):** Execute the generated L3 definitions, utilizing Moqui's UPSERT idempotency to safely merge the client specifics atop the L1/L2 baseline.
5.  **Stage 5 (L4 Secrets):** Inject runtime variables (API Tokens, database credentials) securely into the Docker environment.

## 2. Implementation by Architecture

### Setup A (Moqui-Only)
*   **Trigger:** Utilizes `gradlew load types=seed,seed-initial,install,ext-seed`.
*   **Mechanism:** Component hierarchy inherently protects sequence. L3 overrides load seamlessly from the generated client component (`[client]-maarg`).
*   **Tooling:** A CLI questionnaire gathers Shopify IDs. Nunjucks templates dynamically generate the `ExtSeedData.xml` directly into the component's `data/` directory prior to load.

### Setup B (Legacy OFBiz)
*   **Caveats:** Because all data resides in a single monolithic component, the installer *must* programmatically rename generated XML files using artificial prefixes (e.g., `Z1_ExtSeedData.xml`) to force them to load alphabetically after the L1 `A1_`/`B1_` base.

## 3. Automated Installer Responsibilities

| Responsibility | Action | Validated Layer |
| :--- | :--- | :--- |
| **Schema Integrity** | Execute pure `seed` data loader first. | L1 |
| **Dynamic Generation**| Build `Facility`, `ContactMech`, and `ShopifyShopTypeMapping` via templates. | L3 |
| **Data Merge** | Trigger the `ext-seed` phase safely utilizing `createOrUpdate`. | L2 / L3 |
| **Credential Injection**| Provide `.env` files for the Docker runtime boundary. | L4 |

## 4. Risks Mitigated

*   **Gap #1 (No Facility):** The installer strictly prompts the operator for Facility data during Stage 3 and generates it dynamically.
*   **Gap #2 (Security Parity):** The installer auto-generates `artifactGroups` alignment based on the client ID.
*   **Collisions:** Prevented natively via Moqui's `createOrUpdate()` logic.
*   **Credential Leaks:** Zero secrets are written to XML files. All secrets remain strictly in L4 environments.
*   **Foreign Key Violations:** Prevented in Setup A by Component Graphs, and in Setup B by automated alphabetical file prefixing.
*   **Idempotency (Re-runs):** The installer can be run multiple times safely without crashing the database.

## 5. Success Criteria & Tech Stack

**Tech Stack Recommendation:**
*   Node.js (CLI Prompt interface).
*   Nunjucks (XML Payload generation).
*   Moqui `EntityDataLoaderImpl` (The execution engine).
*   Docker & Docker Compose (Container Orchestration).
*   Selenium (Post-install UI testing).

**Success Checkpoints:**
1.  [ ] Framework loads 100% of T1 schemas without errors.
2.  [ ] CLI accurately builds the Facility and Store configs.
3.  [ ] L3 XML executes via `createOrUpdate` successfully.
4.  [ ] Docker initializes without logging Fatal `EntityExceptions`.
5.  [ ] Operator can log in via generated credentials.
6.  [ ] Shopify Webhook test successfully triggers a Tier 3 Order load.

### Ultimate Success Measure
**"One new client from discovery to live sync < 4 hours."**
