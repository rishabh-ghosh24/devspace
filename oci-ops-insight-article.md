---
title: "Enable OCI Ops Insight on Oracle Autonomous Database Serverless"
author: "Rishabh Ghosh"
date: "2024-03-15"
source: "https://medium.com/@rishabhghosh24/enable-oci-ops-insight-on-oracle-autonomous-database-serverless-61efab78f927"
---

# Enable OCI Ops Insight on Oracle Autonomous Database Serverless

March 15, 2024
Oracle Cloud Infrastructure (OCI) **Ops Insights** provides comprehensive monitoring and analytics for your autonomous databases. This guide walks you through enabling it.

## Prerequisites

Before you begin, ensure you have:

- An active OCI tenancy with appropriate permissions
- An Autonomous Database Serverless instance
- Access to the OCI Console

## Step 1: Navigate to Ops Insights

Go to the [OCI Console](https://cloud.oracle.com) and find *Ops Insights* under the Observability menu.

## Step 2: Enable Database Insights

Click on the database and run the following command:

```sql
BEGIN
    DBMS_CLOUD_OCI_OBSERVABILITY.ENABLE_DATABASE_INSIGHT(
        compartment_id => 'ocid1.compartment.oc1..example'
    );
END;
/
```

> Note: This process may take a few minutes to complete. Be patient!

## Step 3: Verify Setup

You can verify the setup by checking the `DBA_OCI_INSIGHTS` view:

```sql
SELECT * FROM DBA_OCI_INSIGHTS WHERE status = 'ENABLED';
```

![The Ops Insights dashboard showing database metrics](https://miro.medium.com/example-image.png)
*The Ops Insights dashboard showing database metrics*

## Benefits of Ops Insights

1. Real-time performance monitoring
2. Historical trend analysis
3. Capacity planning recommendations
4. SQL performance analytics

---

## Conclusion

Ops Insights is a powerful tool for managing your **Autonomous Database**. With proper setup, you'll gain valuable insights into your database performance and capacity needs.

For more information, check the [official documentation](https://docs.oracle.com/en-us/iaas/ops-insights/home.htm).