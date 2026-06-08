# Docker Data Loading Mechanism & Service Interaction

Based on deep source-code analysis of `moqui-framework/framework/src/main/groovy/org/moqui/impl/entity/EntityDataLoaderImpl.groovy` and `ExecutionContextFactoryImpl.groovy`, the following report details exactly how data is loaded, sequenced, and persisted during Docker startup. 

## TASK A: Configuration & Load Order

**Configuration Files Found:**
- `moqui-framework/framework/src/main/resources/MoquiDefaultConf.xml` (Defines `<entity-facade>` defaults, empty DB load types, and `<load-data>` core paths).
- `moqui-framework/docker/moqui-run.sh` (The Docker entry point triggering the bootloader).
- `EntityDataLoaderImpl.groovy` (The actual execution engine for file parsing).

### Load Sequence and Mechanics

1. **In what order do data files load? (seed → ext-seed → ext?)**
   Data files do **not** load purely based on their data type tags (`seed`, `ext-seed`). Instead, they are loaded strictly based on:
   - **Component Dependency Order:** The framework components (e.g., `moqui-framework`) load first, followed by downstream custom components (e.g., `ofbiz-oms` or `hotwax-commerce`).
   - **Alphabetical Filename Order:** Within each component's `data/` directory, files are collected into a `TreeMap` and parsed **alphabetically by filename**. 
   - Note: The data loader scans files in this alphabetical order and skips any file where the `<entity-facade-xml type="...">` attribute doesn't match the requested types for the current startup phase.

2. **Is load order FIXED or configurable?**
   It is **FIXED** by component hierarchy and file naming. This is exactly why legacy setup files are prefixed with `A1_`, `A2_`, etc., to artificially force alphabetical sorting for foreign key integrity.

3. **Do `seed` files ALWAYS load before `ext-seed`?**
   **No.** Their order is determined by their component location and filename. However, because core `seed` files reside in framework components and `ext-seed` files reside in downstream components, framework `seed` data inherently loads before downstream `ext-seed` data. If both types existed in the same component, an `ext-seed` file named `A_ext-seed` would actually load *before* a `seed` file named `B_seed`.

4. **What happens if a load fails? (entire setup fails or continue?)**
   **It Continues.** `EntityDataLoaderImpl.groovy` processes each file in an independent database transaction. If an error occurs (e.g., a Foreign Key violation), the loader catches the `Throwable`, logs `"Skipping to next file after error..."`, rolls back the transaction for that specific file, and proceeds to the next file.

---

## TASK B: Find Data Load Services & Idempotency

**Services Found:**
There are **no explicit named services** (like `load-data` or `import-entity`) used to process these XML files during boot. The Moqui `EntityXmlHandler` uses the Entity Engine API directly (`EntityValue` manipulation) rather than routing through the Service Facade.

### Idempotency & Conflict Resolution

*Important Clarification on the "Key Insight":* Moqui does **not** fail on primary key collisions by default. It uses an incredibly flexible **Idempotent Upsert** architecture. 

1. **What service creates records from data files?**
   The `ValueHandler` inside `EntityDataLoaderImpl.groovy` intercepts XML tags, dynamically resolves them to Entity Definitions, and pushes them straight to the database layer.

2. **Which entities use CREATE-OR-UPDATE? (can be updated)**
   **Almost All Entities.** By default, `EntityValue.createOrUpdate()` is executed. This method first performs a `SELECT` using the Primary Key. If the record exists, it resolves the conflict by performing an `UPDATE`. If the data file specifically requests `use-try-insert="true"`, the system attempts an `INSERT`, catches the resulting `EntityException` on PK collision, and falls back to an `UPDATE`. This means Tier 2 (Configurable) entities are safely overwritten by newer files in the load sequence.

3. **Which entities use plain INSERT? (cannot be overridden)**
   Entities that are marked as **immutable** at the schema level. Specifically, entities defined with the `create-only="true"` XML attribute (e.g., `EntityAuditLog` in `EntityEntities.xml`). For these entities, if `createOrUpdate()` detects an existing record and attempts an `UPDATE`, the Entity Engine intercepts it and throws an `EntityException` ("Cannot update create-only (immutable) fields"), which causes that record/file to fail. 

4. **Do data files explicitly call these services, or does Moqui auto-detect?**
   **Moqui Auto-Detects.** The XML node name is matched directly against the entity dictionary (e.g., `<ProductStore>` maps to the `ProductStore` entity). While the XML handler *can* theoretically route a node to a service if the tag perfectly matches a service name, or if it uses the `operation#Entity` syntax (e.g., `<create#ProductStore>`), standard bootstrap files rely purely on auto-detection and direct Entity Engine persistence.
