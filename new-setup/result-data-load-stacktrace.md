# Final Result: End-to-End Data Load Stacktrace

This document provides a comprehensive, sequential trace of exactly how the data loading engine executes during a Docker container startup for both Moqui architectures. Because both setups run on the Moqui Framework engine, the underlying Java/Groovy execution trace is identical.

## The Data Loading Pipeline

### Phase 1: Docker Initialization & Bootloader
1.  **`moqui-run.sh`**: The Docker container starts and executes the bash script. This script maps volume directories and triggers the JVM.
2.  **`MoquiStart.java` (`main()`)**: The entry point of the Java application. The bootloader parses command-line arguments (e.g., `load types=seed,seed-initial,install`).
3.  **`Moqui.java` (`loadData()`)**: If the `load` command is detected, the bootloader invokes the core `Moqui` class to initialize the framework context and trigger data loading.
4.  **`ExecutionContextFactoryImpl.groovy` (`checkEmptyDb()`)**: The ECFI verifies if the database is completely empty. If it is, it orchestrates the `EntityDataLoader` to execute an initial bootstrap using the types specified in `MoquiDefaultConf.xml` (`empty-db-load="seed,seed-initial,install"`).

### Phase 2: Component Scanning & File Discovery
5.  **`EntityDataLoaderImpl.groovy` (`load()`)**: The data loader is initialized.
6.  **Component Dependency Graph**: The loader reads `MoquiDefaultConf.xml` and every component's `MoquiConf.xml`. It constructs a strict dependency graph. Core framework components (e.g., `moqui-framework`) are placed at the top of the queue. Downstream client components (e.g., `gorjana-maarg`) are placed at the bottom.
7.  **Directory Traversal**: The loader iterates through the components in the defined dependency sequence.
8.  **Alphabetical File Collection**: Inside each component's `data/` directory, it searches for `.xml` files and sorts them alphabetically. *(This is where Legacy Setup B relies on `A1_`, `A2_` prefixes to force foreign key compliance).*
9.  **Type Filtering**: For each XML file, it parses the root node: `<entity-facade-xml type="...">`. If the `type` does not match the arguments requested by `MoquiStart` (e.g., `ext-seed`), the file is skipped.

### Phase 3: Transaction Execution & Parsing
10. **Transaction Boundary (`loadSingleFile()`)**: For each valid file, the loader initiates an independent database transaction. This ensures that a failure in one file does not corrupt the entire database or crash the Docker startup sequence.
11. **SAX XML Parsing (`EntityXmlHandler.groovy`)**: The XML file is streamed and parsed event-by-event.
12. **Entity Resolution (`startElement()`)**: When the handler encounters an XML node (e.g., `<ProductStore>`), it dynamically looks up the Entity Definition in the framework's entity dictionary.
13. **Data Hydration (`endElement()`)**: The handler reads the attributes of the XML node (e.g., `productStoreId="STORE"`) and hydrates a native `EntityValue` object.

### Phase 4: Entity Engine Persistence (Idempotent Upsert)
14. **Service vs Entity Logic (`handleValue()`)**: The loader checks if the XML node explicitly called a service (e.g., `<create#ProductStore>`). In 99% of cases, it did not, so it defaults to direct Entity Engine persistence.
15. **The Idempotent Check (`EntityValueBase.java -> createOrUpdate()`)**: 
    *   The Entity Engine takes the `EntityValue` and performs a `SELECT` query against the database using its Primary Key.
    *   **If the record DOES NOT exist**: The engine executes an `INSERT`.
    *   **If the record DOES exist**: The engine gracefully resolves the conflict by executing an `UPDATE`. This allows `ext-seed` files in Tier 2 to safely override `seed` files in Tier 1.
16. **The Immutability Exception**: During the `createOrUpdate()` flow, the engine checks the schema for the `create-only="true"` constraint. If the attribute is `true` (e.g., `EntityAuditLog`) AND the record already exists, the engine throws an `EntityException` ("Cannot update create-only fields"), failing the record.
17. **Transaction Commit / Rollback**: If all nodes in the file process successfully, the transaction is committed. If a fatal `EntityException` or `SQLException` (like a missing foreign key) occurs, the exception is caught, a "Skipping to next file" error is logged, the transaction rolls back, and Phase 3 begins again on the next file.

## Final Summary
The Moqui Data Loader is not a rigid insertion engine; it is a highly resilient, idempotent synchronization tool. By combining **Component Dependency Sequencing** with **Idempotent Upserting**, it achieves a dynamic layered architecture without requiring complex external installation scripts.
