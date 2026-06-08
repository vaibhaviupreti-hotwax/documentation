# In-Depth Data Loading Stack Trace: Moqui & Legacy OFBiz

This document provides a highly detailed, line-by-line execution trace of the data loading mechanisms operating beneath both Setup A (Moqui-Only) and Setup B (Legacy OFBiz/Hotwax). Because both setups run entirely on the Moqui Framework engine, their execution traces share the same core framework pathways. The differences emerge in how the framework is utilized and how files are structured.

---

## Phase 1: Docker Initialization & Bootloader

1. **`moqui-run.sh` / Docker Compose Execution:**
   - The Docker container launches. Based on `moqui-run.sh`, the container maps local directories (like `runtime/conf`, `runtime/db`, `runtime/txlog`) into `/opt/moqui/runtime/` via `-v` flags.
   - If utilizing `simple/Dockerfile`, the container boots using:
     `ENTRYPOINT ["java", "-cp", ".", "MoquiStart", "port=80"]`
     `CMD ["conf=conf/MoquiProductionConf.xml"]`

2. **`MoquiStart.java` (`main()` entry point):**
   - The JVM starts and hits the `MoquiStart` class.
   - The bootloader reads the command-line arguments (e.g., `port=80`, `conf=conf/MoquiProductionConf.xml`).
   - If the system detects a `load` argument (e.g., `load types=seed,seed-initial,install`), `MoquiStart` stores these execution commands to be processed during application startup.

3. **`Moqui.java` (Context Initialization):**
   - `MoquiStart` triggers the `Moqui` class to build the `ExecutionContextFactory` (ECF).
   - This class is a singleton interface that acts as the absolute root of the framework, bootstrapping caches, connections, transaction managers, and the service engine.

4. **`ExecutionContextFactoryImpl.groovy` (`checkEmptyDb()`):**
   - As part of the initialization, the ECFI verifies the health and population of the database schema.
   - It executes `checkEmptyDb()`. This method specifically queries the database for core entities (like `moqui.basic.Enumeration`).
   - **If the database is empty**, the ECFI automatically forces an initial data load. It pulls the default types defined in `MoquiDefaultConf.xml` under `<empty-db-load-types>`, which natively includes `"seed,seed-initial,install"`.
   - The ECFI instantiates the `EntityDataLoaderImpl`.

---

## Phase 2: Component Scanning & File Discovery
*The `EntityDataLoaderImpl.groovy` (Data Loader) takes over execution.*

5. **Dependency Graph Construction (`EntityDataLoaderImpl.load()`):**
   - Before reading any files, the loader must understand the architecture. It traverses `runtime/component/` and reads every `MoquiConf.xml`.
   - It builds a strict dependency graph based on the `<depends-on>` nodes. 
   - Core framework components (e.g., `moqui-framework`) are placed at the top. Downstream components (e.g., `gorjana-maarg` or `ofbiz-oms`) are placed below.

6. **Directory Traversal & Collection:**
   - The Data Loader iterates through the ordered component array.
   - Within each component, it specifically targets the `data/` directory.
   - It recursively scans for all `.xml` and `.csv` files.

7. **Sorting Mechanism (Crucial Architectural Difference):**
   - As files are collected *within* a component, they are inserted into a `TreeMap` structure, effectively **sorting them alphabetically by filename**.
   - **Setup A (Moqui-Only):** Relies natively on component boundaries. Framework data loads first (e.g., `BasicSeedData.xml`), followed by custom integration data (e.g., `ExtSeedData.xml`).
   - **Setup B (Legacy OFBiz):** Because OFBiz contains heavily coupled, monolithic files dropped into a single component, it bypasses component loading by intentionally renaming files alphabetically (e.g., `A1_CommonL10nData.xml`, `B1_ProductSeedData.xml`). This hack forces the `TreeMap` to sequence files to respect foreign-key constraints.

8. **File Filtering (`checkRootNode()`):**
   - The Data Loader pre-parses the XML document to read the root element: `<entity-facade-xml type="...">`.
   - It compares the `type` attribute (e.g., `seed`, `ext-seed`) against the active loader list. If the type is not requested, the entire file is discarded from the load sequence.

---

## Phase 3: File Execution & Transaction Management

9. **Transaction Boundary Initiation (`loadSingleFile()`):**
   - The Data Loader executes a `for` loop over the sorted file list.
   - For each file, it initiates an independent `Transaction`. 
   - **Idempotent Isolation:** By scoping the transaction strictly to the file, a crash or foreign-key error in one data file will *only* roll back that specific file. The rest of the Docker startup sequence will continue uninterrupted.

10. **SAX Parser Invocation:**
    - The Data Loader instantiates `EntityXmlHandler.groovy`, which extends the standard SAX parser.
    - Instead of loading the entire XML into memory (DOM), it streams the file event-by-event (Element by Element), drastically reducing memory footprint.

---

## Phase 4: SAX Event Handling & Resolution

11. **Element Discovery (`startElement()`):**
    - The `EntityXmlHandler` encounters a node (e.g., `<moqui.basic.Enumeration>`).
    - It triggers `edli.efi.getEntityDefinition()`, routing the node name to the Entity Facade to verify if it represents a valid database table.
    - **Fallback Check (Service Routing):** If the node name is *not* an entity, the Handler checks if it is a Service Definition. (e.g., `<create#ProductStore>`). If it matches a service format, it prepares a `ServiceCallSync` instead.

12. **Attribute Parsing:**
    - The SAX parser extracts all XML attributes for the current node (e.g., `enumId="ECOM_RTN_CHANNEL"`, `description="Shopify Admin"`).
    - It compiles these attributes into a generic Java `Map`.

13. **Hydration (`endElement()`):**
    - The `endElement()` method is triggered. The Handler instantiates a blank `EntityValue` using the Entity Definition.
    - It hydrates the `EntityValue` by calling `.setAll(valueMap)`.

14. **Delegation to ValueHandler:**
    - The fully populated `EntityValue` is passed from the XML Handler to the internal `ValueHandler.handleValue()`.

---

## Phase 5: Entity Engine Persistence (Idempotent Upsert)

15. **Execution Routing (`EntityValueBase.java`):**
    - The `ValueHandler` submits the `EntityValue` back to the core Entity Engine layer (`EntityValueBase.java`).
    - Unless the XML explicitly passed a `use-try-insert="true"` or `onlyCreate=true` directive, the loader natively triggers `createOrUpdate()`.

16. **The Idempotent UPSERT (`createOrUpdate()` logic):**
    - **Query Execution:** The Entity Engine constructs a `SELECT` query utilizing the exact Primary Key defined in the `EntityValue` (e.g., `enumId="ECOM_RTN_CHANNEL"`).
    - **Conflict Check:** 
      - If `one() == null` (Record does not exist): The engine triggers `.create()`, dynamically generating an SQL `INSERT` statement.
      - If `one() != null` (Record exists): The engine compares the existing data with the incoming data. If changes are detected, it dynamically generates an SQL `UPDATE` statement.
    - **Architectural Implication:** This is why Tier 2 Configurable Data (`ext-seed`) can safely override Tier 1 Core Data (`seed`) without crashing. The engine natively handles collisions by overwriting.

17. **Immutability Enforcement (`create-only="true"` constraint):**
    - During the `createOrUpdate()` flow, the Entity Engine checks the `EntityDefinition` metadata.
    - If the definition contains `create-only="true"` (which is extremely rare, primarily used only by `EntityAuditLog`):
      - And the record *already exists* (meaning `UPDATE` is required).
      - The Entity Engine intercepts the `UPDATE` and immediately throws an `EntityException`: `"Cannot update create-only (immutable) fields."`

18. **Commit & Cleanup:**
    - Once every node in the file is successfully parsed and written via `createOrUpdate()`, the file's transaction is committed to the database (e.g., PostgreSQL).
    - If an exception was thrown (e.g., missing Foreign Key, Immutable Field edit), the `loadSingleFile()` catch block intercepts the `Throwable`, logs `"Skipping to next file after error"`, rolls back the transaction, and safely moves to the next file in the list.

---

## Final Review: OFBiz vs Moqui Paradigm Shift
Although both Setup A and Setup B use this exact Java stack trace, their data strategies fundamentally differ:
- **OFBiz (Setup B)** relies on rigid **Phase 2 File Sorting** (the `A1_` prefixes) to ensure monolithic data structures load without triggering transaction rollbacks.
- **Moqui (Setup A)** utilizes **Phase 2 Component Dependencies** and **Phase 5 Idempotent Upserts**, allowing developers to build modular, overridden integrations (like Shopify settings) securely atop the Universal Data Model framework.
