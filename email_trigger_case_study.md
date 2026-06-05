# Case Study: Triggering Emails After Order Shipment

This document explores the architectural choices for triggering an email notification after an order changes its status to "Shipped". It compares standard approaches against OFBiz-specific constraints.

## The Core Concept: Avoid "Invisible Triggers" When Possible

Before diving into the email case, it is important to understand the concept of ECAs and SECAs.

*   **ECA (Entity Condition Action):** "When a database row is created/updated/deleted, automatically run some code."
*   **SECA (Service Event Condition Action):** "When a service finishes running, automatically run some other service."

They act as **invisible triggers** — things happen automatically in the background when data changes or services run. 

**"Don't rely on them" means:** ECAs and SECAs are hidden side-effects. You might look at the code and think, "I'm just updating an order status," but behind the scenes, an ECA fires off an email, creates a shipment, and sends a message to Shopify. When something breaks, it is difficult to trace because the connection isn't visible in the main code path.

**The Ideal Alternative:** `SystemMessage` + `ServiceJob`. This makes everything explicit:
*   The job is visible in the `ServiceJob` table (you can see the schedule, pause it, check run history).
*   The message is visible in the `SystemMessage` table (you can see payload, status, errors).
*   Nothing is hidden — if it breaks, you query a table rather than hunting through XML trigger configs.

> **One-liner:** ECAs/SECAs are magic that happens invisibly; `SystemMessage` + `ServiceJob` is the same work done *visibly and traceably*.

---

## Scenario 1: The General Approach (Unconstrained)

**Requirement:** Send an email to the customer when the order status becomes "Shipped".

### Approach A: The ECA/SECA Approach
> "When `OrderHeader.statusId` changes to `ORDER_COMPLETED`, automatically call `sendShipmentEmail`"

**What could go wrong:**

| Problem | What happens |
| :--- | :--- |
| **Email server is down** | The trigger fires, the email fails, and your order status update **rolls back** (if in the same transaction) — the order isn't marked shipped. |
| **Customer didn't get email** | No record anywhere. You have no idea it failed. |
| **Bulk Updates (500 orders)** | 500 triggers fire simultaneously; the email server chokes. |
| **Pausing Emails** | You have to edit an XML config file and redeploy. |
| **Debugging** | "Why did this customer get 2 emails?" — Good luck tracing invisible triggers. |

### Approach B: SystemMessage + ServiceJob Approach
> Ship the order normally. A `ServiceJob` runs every 5 minutes, picks up newly shipped orders, creates a `SystemMessage` for each, and sends the email.

**Why this is better:**

| Benefit | How |
| :--- | :--- |
| **Order update never fails because of email** | They are decoupled — shipping succeeds regardless of email server status. |
| **Automatic Retries** | If the email fails, the message stays in `SmsgProduced`, and the job retries on its next run. |
| **Full Audit Trail** | The `SystemMessage` table shows: which customer, what was sent, when, and if it succeeded. |
| **Safe Bulk Processing** | The job picks them up in manageable batches at its own pace. |
| **Easy to Pause** | Set `paused="Y"` on the `ServiceJob` in the database — no redeploy needed. |
| **Easy Debugging** | Query `SystemMessage` where `type=ShipmentEmail` and `status=SmsgError`. |

**Verdict:** For anything involving **external systems** (email servers, APIs, webhooks), always prefer `SystemMessage` + `ServiceJob`. The decoupling ensures core business logic (shipping) isn't blocked by external failures.

---

## Scenario 2: The OFBiz-Constrained Approach

**New Constraints:**
1. You are restricted to using OFBiz's `CommunicationEvent` flow.
2. The requirement explicitly states to **remove `SystemMessage` handling from the complete email workflow**.

*(Note: Usually, OFBiz bridges `CommunicationEvent` with `SystemMessageRemote` to handle the actual delivery. But since `SystemMessage` is banned entirely by the requirement, we must adapt.)*

You still need a way to *trigger* the creation and sending of that `CommunicationEvent` when an order ships. Your choices are **SECAs (Service ECAs)** or a **Scheduled ServiceJob**.

### The Best Approach Under Constraints: Async SECA + CommunicationEvent

In standard OFBiz, you don't use a data-level ECA (Entity ECA); you use a **SECA (Service ECA) with `mode="async"`**.

**How it works:**
1. You ship the order (the `updateShipment` service runs).
2. A SECA listens for `updateShipment` to finish successfully.
3. The SECA triggers your email service (e.g., `sendShipmentEmail`) but specifies `mode="async"`.
4. Your email service creates the `CommunicationEvent` and sends the email directly.

### Why Async SECA wins over a Scheduled Job here:

| Benefit | Why Async SECA wins |
| :--- | :--- |
| **Immediate Delivery** | Async SECAs run immediately in the background. A Scheduled Job makes the customer wait 5-15 minutes for their confirmation email until the next cron tick. |
| **No "Tracking" Logic Needed** | With a Scheduled Job, you have to write complex logic to find "shipped orders where we haven't sent an email yet." With a SECA, you just pass the `orderId` directly to the email service right when it ships. |
| **Built-in OFBiz Async** | By setting `mode="async"` on the SECA, OFBiz automatically drops the email task into its Job Sandbox (JMS/async queues). **If the email fails, it does NOT roll back your shipment.** The shipment transaction is already committed. |

### Mitigating the "Invisible Trigger" Problem

While an Async SECA solves the rollback problem and provides immediate delivery, it is still an "invisible trigger." A developer looking at the `updateShipment` Java code won't see the email logic.

**How to handle this:**
Since you are restricted to this flow, you must rely heavily on the `CommunicationEvent` status to provide traceability.

*   If the email succeeds, ensure the `CommunicationEvent` is created with status `COM_COMPLETE`.
*   If the email fails (e.g., bad email address, SMTP down), your service must ensure the `CommunicationEvent` is still created (or updated) to reflect the failure, setting the status to `COM_BOUNCED` or `COM_ERROR`, and logging the exact error messages.

### Summary Verdict for OFBiz

If `SystemMessage` is banned, use a **Service ECA (SECA) set to `mode="async"`** to trigger the `CommunicationEvent` workflow. It gives you the immediate delivery customers expect, prevents shipment rollbacks if the email server crashes, and avoids the complexity of building a custom scheduled batch job to hunt down un-emailed orders.
