# Maarg Setup (Steps by Deepak Sir)
Refer to the official guide here: [Setup Moqui on Local Machine](https://github.com/hotwax/hotwax-maarg-docker-config/blob/main/docs/setup_moqui_on_local_machine.md)

---

## 📋 3 Important Entities
These must be populated in sequence:
1. `ShopifyConfig`
2. `ShopifyShop`
3. `SystemMessageRemote`

Fill them with the correct data (this can be prompted).

---

## 🎯 Objective: Sync Shopify Shop and Products to Local Maarg Setup

### 1. Sync Shopify Shop
1. Go to the NextGen Maarg production environment: [NextGen Maarg Entity List](https://nextgen-maarg.hotwax.io/qapps/tools/Entity/DataEdit/EntityList)
2. Search for the primary entities: `ShopifyConfig`, `ShopifyShop`, and `SystemMessageRemote`.
3. Copy the data from these entities and paste them into the equivalent tables in your local setup:
   [Local Entity List](http://localhost:8080/qapps/tools/Entity/DataEdit/EntityList)
   *(Ensure you do this for all 3 entities, maintaining the correct sequence).*
4. **Note on main FK reference:** Fill in the required fields. Leaving them blank will throw an error later that needs to be rectified (send a chat to Avnindra Sir if this happens). 
   > [!IMPORTANT]
   > The **Product Store** is required before creating the Shopify Shop.

### 2. Seed Services for Product Import
Import the seed services data using the local data import tool:
[Local Data Import](http://localhost:8080/qapps/tools/Entity/DataImport)

#### Note / Issue Encountered:
- **Foreign Key Constraint:** When you run the service for importing products into your system, there is a foreign key constraint on `SYSTEM_MESSAGE_REMOTE_ID`.
- **System Message Remote ID (SmrId):** When seeding data, it requires `SmrId` (System Message Remote ID) in the parameter `parameterName="consumeSmrId"`.
- You can handle this in one of two ways:
  - Add it manually in the entity: `SystemMessageTypeParameter`
  - Or, if you have already set it, you can remove this line:
    ```xml
    <parameters parameterName="consumeSmrId" parameterValue="SHOP_CONFIG_OMS" systemMessageRemoteId="SHOP_CONFIG_OMS"/>
    ```
  - Or change it to:
    ```xml
    <parameters parameterName="consumeSmrId" parameterValue="M100000" systemMessageRemoteId="M100000"/>
    ```
  > [!WARNING]
  > This workaround can cause ambiguity and will not behave consistently across setups for every developer. It depends on which of the methods mentioned above is chosen. Ideally, there should be a single standardized way to do this because the data is identical everywhere.

### 3. Run the 3 Services/Jobs for Product Import
Run the following service jobs in order:
- `queue_BulkQuerySystemMessage_BulkProductAndVariantsById`
- `send_BulkProductAndVariantsByIdQueryProducedSystemMessages`
- `poll_BulkOperationResult_ShopifyBulkQuery`

#### Verification:
You can verify that the products were successfully imported through your terminal or directly via database tables in MySQL.
*Example query to verify products were added:*
```sql
SELECT count(*) FROM maarg_new_setup2.product; -- Expected count: 344
```

#### ⚠️ Issue: Automated vs Manual Execution
* **Scenario:** Ran all 3 jobs.
* **Problem/Question:** Why didn't these jobs run automatically once it was confirmed that the seeded data was present? Why does the data need to be seeded manually here?

---

## 📦 Next Step: Import Shopify Orders to Local Setup
Import Shopify orders from a specific set date or bring all orders to your local instance.

### ⚠️ Issue: `fromDate` Configuration Settings
This issue may occur if you have set the `fromDate` too far in the past:
- **Behavior:** Orders will still import, but performance varies based on the date range:
  
#### Case 1: If the date is too old
- It will sync orders starting from that old date, which requires more processing time to pull and process the latest order batch. 
- *Note:* By the way, the orders are imported to MDM (Multi-Domain MDM), they are just not reflected in your system. You can verify this in MDM / Shopify admin. Staging orders to MDM is an independent flow, which is why it displays. However, they aren't reflected in NextGen because `fromDate` was set to 2023, which slowed down the processing of recent orders.

#### Case 2: If the date is recent or left null
- It will pull updated orders only.
- *Open Question:* What if there is an update to an older order? Will that update get reflected?

---

## 🔄 Automated Order Sync Test
Create an order on Shopify, and it should reflect in your system automatically (only updated orders are synced to the system).

### Verification
If your local system is up, a job runs every 5 minutes via cron to pull updated orders from Shopify. Verify this behavior locally.





