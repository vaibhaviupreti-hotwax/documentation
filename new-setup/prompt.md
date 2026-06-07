# Objective

You are acting as a software archaeologist and ERP data architect.

You are analyzing two large enterprise systems that are based on Apache OFBiz and Moqui/Mantle. These systems contain significant company-specific customizations and client-specific implementations.

The goal is NOT to immediately classify data.

The goal is to discover, justify, and classify ERP data into tiers that can eventually support a guided installation/bootstrap process.

You must gather evidence first, then classify.

---

# Desired Outcome

Produce a classification catalog of ERP entities and, where necessary, specific records.

Initial classification tiers:

Tier 1 - Common Framework Data

Data that should be identical or nearly identical across clients.

Examples:

* Status types
* Status items
* UOM definitions
* Enumeration types
* System constants
* Framework reference data

Tier 2 - Configurable ERP Data

Data that varies between clients but is generally configured during implementation.

Examples:

* Product stores
* Warehouses
* Tax authorities
* Accounting setup
* Catalog structures
* Fulfillment configuration
* Store configuration
* Shopify integration configuration

Tier 3 - Highly Mutable Business Data

Data that belongs to a specific client and usually changes frequently.

Examples:

* Products
* Customers
* Inventory
* Orders
* Promotions
* Vendor-specific information

Do not assume these examples are correct.

Verify everything through evidence.

---

# Analysis Scope

Analyze EVERYTHING available.

Including but not limited to:

* Entity definitions
* Entity relationships
* View entities
* Services
* Service implementations
* Groovy scripts
* Java classes
* Screens
* Forms
* Transitions
* Workflows
* Data XML files
* Seed data
* Seed-initial data
* Demo data
* Install data
* Runtime imports
* Mantle data loaders
* OFBiz data loaders
* Git history if available
* Existing databases if available
* Documentation if available

Do not limit analysis to entity definitions.

Business logic frequently determines whether data is configurable.

---

# Classification Methodology

Use the following evidence hierarchy in order.

## Phase 1 - Semantic Classification

Analyze entity purpose.

Questions:

* What business concept does this entity represent?
* Is it a framework concept?
* Is it a configuration concept?
* Is it operational business data?

Record findings.

Do not classify yet.

---

## Phase 2 - Data Loader Analysis

Analyze all data files.

Identify:

* seed
* seed-initial
* install
* demo
* tenant
* bootstrap
* framework setup
* custom setup

For each entity determine:

* loaded by framework?
* loaded during installation?
* loaded by implementers?
* loaded by client imports?

Record evidence.

---

## Phase 3 - Code Reference Analysis

Find all references to entities and records.

Examples:

statusId = "ORDER_APPROVED"

enumId = "XYZ"

roleTypeId = "CUSTOMER"

Questions:

* Are records treated as constants?
* Are records assumed by framework logic?
* Are records required for application startup?
* Are records hardcoded in workflows?

If yes, increase Common score.

---

## Phase 4 - Relationship Analysis

Build an entity dependency graph.

Determine:

* parent entities
* dependent entities
* configuration ownership
* transaction ownership

Example:

If ProductStore is configurable and multiple related entities exist solely to support ProductStore, those entities may inherit configurability.

Document inheritance chains.

---

## Phase 5 - Shopify Analysis

Identify all Shopify-related entities.

Search:

* Shopify
* shop
* store
* fulfillment
* webhook
* product sync
* inventory sync
* order sync
* metafield
* market
* location

Assume nothing.

Determine actual relationships.

Classification rule:

If an entity exists primarily to support Shopify integration, assign strong configurable bias.

If ERP entities are tightly coupled to Shopify entities, note inherited configurability.

Provide evidence for every conclusion.

---

## Phase 6 - Historical Variability Analysis

If multiple client implementations exist:

Compare:

* data files
* configuration files
* setup scripts
* databases

Determine:

* always same
* usually same
* frequently modified
* always modified

Use this as a major classification signal.

---

# Confidence Model

Every classification must include:

* Tier
* Confidence score (0-100)
* Evidence

Example:

Entity: ProductStore

Tier: Configurable ERP Data

Confidence: 92

Evidence:

* Appears in install data
* Modified in 14 client implementations
* Referenced by configuration screens
* Not required by framework startup

---

# Record-Level Classification

Some entities contain mixed data.

Example:

Enumeration
StatusItem
PartyRoleType

When necessary:

Classify individual records instead of entire entities.

Example:

StatusItem.ORDER_APPROVED -> Common

StatusItem.CLIENT_CUSTOM_REVIEW -> Configurable

Do not force entity-wide classification when record-level classification is more accurate.

---

# Deliverables

Produce:

1. Entity Inventory

List every entity discovered.

2. Classification Catalog

Entity
Tier
Confidence
Evidence

3. Record-Level Exceptions

Entities requiring record-level classification.

4. Dependency Graph

Show inheritance and configuration propagation.

5. Shopify Influence Report

Entities directly and indirectly affected by Shopify integration.

6. Installer Architecture Proposal

Recommend:

Core Load
↓
ERP Configuration Load
↓
Questionnaire-Driven Configuration
↓
Client Data Load

Identify which entities belong in each stage.

---

# Critical Rules

Do not guess.

Do not classify from entity names alone.

Do not assume OFBiz conventions are preserved in customized code.

When evidence conflicts, document the conflict.

If classification becomes uncertain, stop and ask targeted questions rather than inventing conclusions.

The objective is correctness, not completeness.

Evidence always wins over assumptions.
--------------------------------------------------

# Additional Repository Context

You have been provided access to a repository that contains **two different ERP platform setups** representing two generations of the company's architecture.

These setups must be analyzed independently before any comparison or conclusions are made.

Do not merge findings prematurely.

Treat them as separate systems that may have different data ownership models, loading strategies, configuration patterns, bootstrap mechanisms, and implementation philosophies.

---

# Repository Structure Context

## Setup A — Moqui-Only Architecture

Folder:

`moqui-framework`

This contains the company's newer architecture.

Important context:

The company has built its own platform and business solutions on top of Moqui.

This setup represents the direction the company intends to move toward for future client onboarding.

The goal of this architecture is to support onboarding clients using a Moqui-centric approach rather than the older tightly-coupled architecture.

Assume that:

* Moqui framework behavior may have been extended
* Mantle conventions may have been modified
* Custom loaders may exist
* Bootstrap processes may differ from standard Moqui practices
* Entity ownership may differ from historical implementations

Do not assume standard Moqui behavior without verification.

Always verify through code, configuration, data loaders, services, and runtime references.

---

## Setup B — Legacy Integrated Architecture

Folder:

`sandbox`

This contains the older production architecture used by the company.

This environment contains a more tightly-coupled implementation involving:

* OFBiz
* Moqui
* Solr
* Custom integrations
* Historical implementation patterns

This architecture is still important because:

* Existing clients may still use it
* Historical configuration decisions may originate here
* Data classification decisions may have been inherited into newer systems
* Migration planning may depend on understanding this architecture

Do not assume data ownership is the same as in the Moqui-only setup.

Analyze independently.

---

# Historical Research Files

The repository also contains two Markdown files:

* `new-store-setup-sop.md`
* `new-store-setup-sop_old.md`

These documents were created by another engineer who previously performed research related to store setup, onboarding, configuration, or installation workflows.

These documents are reference material only.

You may use them to:

* Understand prior reasoning
* Understand prior investigation methodology
* Identify areas worth validating
* Discover entities, services, loaders, workflows, or configurations that require deeper inspection

However:

Do NOT treat these documents as authoritative truth.

Do NOT inherit classifications from these documents.

Do NOT copy conclusions from these documents without validating them against actual code, entities, services, data files, and runtime behavior.

Code evidence always takes precedence over documentation.

If documentation and code disagree:

* Document the disagreement
* Explain the discrepancy
* Prefer code-derived conclusions

---

# Dual-System Analysis Requirement

Perform the full classification process independently for both architectures.

Generate findings separately.

Do not combine classifications until both analyses are complete.

The same entity may receive different classifications in different architectures if evidence supports it.

Document such differences explicitly.

---

# Additional Deliverables

In addition to all deliverables defined above, produce the following reports.

---

## Deliverable 7 — Legacy Integrated Architecture Report

Analyze the OFBiz + Moqui + Solr environment independently.

Produce:

* Entity inventory
* Classification catalog
* Record-level exceptions
* Dependency graph
* Data loading strategy
* Bootstrap sequence
* Configuration ownership model
* Client onboarding flow
* Shopify influence analysis
* Evidence-based conclusions

Focus on how data behaves in the tightly-coupled legacy architecture.

---

## Deliverable 8 — Moqui-Only Architecture Report

Analyze the Moqui-only environment independently.

Produce:

* Entity inventory
* Classification catalog
* Record-level exceptions
* Dependency graph
* Data loading strategy
* Bootstrap sequence
* Configuration ownership model
* Client onboarding flow
* Shopify influence analysis
* Evidence-based conclusions

Focus on how onboarding, installation, configuration, and ERP setup are handled in the newer architecture.

---

## Deliverable 9 — Architecture Comparison Report

Compare the two architectures.

For every major finding identify:

* Same behavior
* Different behavior
* Migration impact
* Classification impact
* Bootstrap impact
* Configuration impact
* Installer impact

Highlight:

* Entities that changed ownership
* Entities that changed tiers
* Entities that became more configurable
* Entities that became framework-owned
* Entities that became client-owned

Document all evidence.

---

## Deliverable 10 — Research Validation Report

Compare:

1. Findings from actual code analysis
2. Findings from `new-store-setup-sop.md`
3. Findings from `new-store-setup-sop_old.md`

For each significant observation:

* Matches documentation
* Partially matches documentation
* Contradicts documentation
* Not mentioned in documentation

Provide supporting evidence.

Identify:

* Missing findings in documentation
* Incorrect assumptions in documentation
* Areas where documentation remains accurate
* Areas where code evolved beyond documentation

---

# Reporting Rules

When generating reports:

1. Keep legacy architecture findings separate from Moqui-only findings.
2. Never merge classifications unless explicitly performing comparison analysis.
3. Cite evidence sources for every major conclusion.
4. Distinguish between:

   * Code evidence
   * Data-loader evidence
   * Runtime evidence
   * Documentation evidence
5. If an entity behaves differently in the two architectures, document both behaviors rather than forcing a single classification.
6. When uncertainty exists, explain the uncertainty and identify the exact files, entities, services, loaders, or workflows that require further investigation.

The primary objective is to produce a defensible ERP data classification model that supports both:

* Existing client migrations from the legacy architecture
* Future client onboarding on the Moqui-only architecture

Evidence from actual implementation must always outweigh assumptions, conventions, or documentation.
