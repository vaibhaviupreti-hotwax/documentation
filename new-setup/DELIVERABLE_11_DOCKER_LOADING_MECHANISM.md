# DELIVERABLE 11: Docker Data Loading Mechanism

## 1. Executive Summary

The Docker boot sequence orchestrates the core framework initialization via `MoquiStart`. A comprehensive code analysis proves the Moqui data engine relies heavily on **UPSERT semantics**. This guarantees a safe, idempotent, layered bootstrap where Client Configuration (L3) can seamlessly override Framework Reference (L1) data without failing constraints.

## 2. Loading Sequence

The `EntityDataLoaderImpl.groovy` executes in three deterministic phases:
1.  **Component Dependency Graph:** Sorts components hierarchically (e.g., `moqui-framework` → `mantle-udm` → `gorjana-maarg`).
2.  **Load Type Filtering:** Discards XML files that do not match the requested type (e.g., ignores `ext-test` if `seed` is requested).
3.  **Alphabetical Sorting:** Within each valid component's `data/` directory, files are sorted and executed alphabetically.

## 3. Idempotent UPSERT Mechanics

The data loading engine processes each XML node through `EntityValueBase.createOrUpdate()`:
*   **Step 1:** The engine executes a `SELECT` query utilizing the exact Primary Key.
*   **Step 2:** If the record exists, the engine dynamically generates an SQL `UPDATE`.
*   **Step 3:** If the record does not exist, the engine dynamically generates an SQL `INSERT`.

Each file is parsed inside an isolated, atomic **Transaction Boundary**. If a file fails due to an external constraint (like missing a foreign key), it logs an error, safely rolls back that single file, and proceeds to the next.

## 4. Immutability Enforcement

The framework avoids strict database immutability constraints. The only mechanism that explicitly forces a failure is the `create-only="true"` schema attribute.
*   The sole entity across both architectures utilizing this constraint is `EntityAuditLog` (T1).
*   If `createOrUpdate()` attempts an `UPDATE` on this entity, an `EntityException` is thrown and the file rolls back.

## 5. L1 → L2 → L3 → L4 Safety Model

| Layer | Safety Mechanism | Impact |
| :--- | :--- | :--- |
| **L1 (Seed)** | Executed first via Framework component position. | Guarantees foundational integrity (100% Core Data). |
| **L2 / L3 (Ext-Seed)** | Executed last via Downstream component position. UPSERT enabled. | Guarantees safe overrides of L1 configurations without PK collisions. |
| **L4 (Runtime)** | Not stored in git; injected natively via Docker environmental variables. | Zero footprint in the bootloader. |

## 6. Risk Assessment

*   **Idempotency Errors:** **LOW.** The `createOrUpdate` mechanism prevents deployment crashes upon subsequent re-runs of the data loaders.
*   **Foreign Key Violations:** **LOW.** Moqui's component dependency sequencing natively protects foreign keys. Legacy OFBiz installations maintain safety via strictly structured alphabetical filename prefixes.
*   **Credential Leaks:** **LOW.** API tokens and Webhook secrets are correctly isolated from XML and handled via L4 Environment variables.

## 7. Recommendation

**Safe and Ready for Automation.** The Moqui initialization pipeline is completely deterministic and highly resilient. It natively supports a scripted, multi-stage Automated Installer.
