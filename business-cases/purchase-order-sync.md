# Purchase Order Sync Incident

## Issue Summary
A purchase order was reported as imported in a cancelled state. The client received the issue notification roughly 15 minutes ago.

## Client Impact
- Affected order: `34867`
- Some order line items are still in the `Created` status even though the order is effectively cancelled.
- The client requires an immediate response and a safe correction for any remaining active line items.

## Root Cause Hypothesis
The issue appears to be caused by a partially cancelled purchase order where line items were not consistently updated. Specifically, the remaining items still in `Created` status were not transitioned to `ITEM_CANCELLED`.

## Recommended Action
Apply a targeted database update to cancel only the line items for order `34867` that are still in `ITEM_CREATED`.

### Safeguards
- Only change items with `STATUS_ID = 'ITEM_CREATED'`.
- Preserve items already in `ITEM_CANCELLED` or `ITEM_COMPLETED`.

## Fix Query
```sql
UPDATE order_item
SET STATUS_ID = 'ITEM_CANCELLED'
WHERE ORDER_ID = '34867'
  AND STATUS_ID = 'ITEM_CREATED';
```

## Next Steps for Client Communication
1. Confirm the fix and verify the order line item statuses after the update.
2. Notify the client that only the remaining `ITEM_CREATED` line items were safely cancelled.
3. Recommend adding validation to prevent partial cancellations in future imports.

## Draft Response for the Client
We have identified that purchase order `34867` was partially cancelled. A small subset of line items remained in `ITEM_CREATED`, so we will update only those line items to `ITEM_CANCELLED` while preserving any items already completed or previously cancelled. Once the update is applied, we will verify the order and confirm the status correction.

## Code Flow Recommendation
- To apply an approach that ensures only active, valid purchase orders reach the system, while cancelled orders are skipped and do not result in inconsistent partial imports.

### Key Validation Rules
- `ORDER_CANCELLED` purchase orders must not be imported normally.
- A blank or missing item status should default to `ITEM_CREATED`.
- Cancelled or completed items should be excluded from this create flow.


