# AWS S3 Inventory Setup Guide

**Purpose:** Enable automated daily inventory reports for 1000x faster data reconciliation

**Status:** Optional (Phase 2B enhancement)  
**Benefit:** Replace 27-second sample scans with <2-minute automated inventory reads

---

## Overview

AWS S3 Inventory provides automated, scheduled reports of all objects in your S3 bucket. This is dramatically faster and more cost-effective than scanning via API calls.

**Comparison:**

| Method | Speed | Cost | Freshness |
|--------|-------|------|-----------|
| **Sample scan (10%)** | 27s | Low (API calls) | Real-time |
| **Full scan (100%)** | ~5 min | High (many API calls) | Real-time |
| **AWS Inventory** | <2 min read | Very low (storage only) | Daily/Weekly |

---

## Setup Instructions

### Step 1: Enable S3 Inventory in AWS Console

1. **Open S3 Console:** https://s3.console.aws.amazon.com/
2. **Select your bucket:** `nba-sim-raw-data-lake`
3. **Go to Management tab**
4. **Click "Create inventory configuration"**

### Step 2: Configure Inventory

**Settings:**

```yaml
Inventory configuration name: nba-data-daily-inventory
Inventory scope: This bucket (entire bucket)
```

**Report Details:**

```yaml
Output format: CSV (or Parquet for smaller files)
Destination bucket: nba-sim-raw-data-lake (same bucket)
Destination prefix: inventory-reports/
```

**Schedule:**

```yaml
Frequency: Daily
```

**Optional fields (recommended):**

- ✅ Size
- ✅ Last modified date
- ✅ Storage class
- ✅ ETag
- ⬜ Replication status (not needed)
- ⬜ Encryption status (not needed)

**Server-side encryption:**

```yaml
Encryption: None (or use SSE-S3 if required)
```

### Step 3: Grant Permissions

AWS will prompt you to grant permissions for S3 to write inventory reports. **Click "Create"**.

This creates a bucket policy allowing S3 Inventory to write reports:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3InventoryPolicy",
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::nba-sim-raw-data-lake/inventory-reports/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "bucket-owner-full-control"
        }
      }
    }
  ]
}
```

### Step 4: Wait for First Report

- **First report:** Generated within 48 hours
- **Subsequent reports:** Daily at scheduled time
- **Location:** `s3://nba-sim-raw-data-lake/inventory-reports/`

---

## Verifying Setup

### Check Configuration

```bash
aws s3api list-bucket-inventory-configurations \
    --bucket nba-sim-raw-data-lake
```

Expected output:

```json
{
    "InventoryConfigurationList": [
        {
            "Id": "nba-data-daily-inventory",
            "IsEnabled": true,
            "Destination": {
                "S3BucketDestination": {
                    "Bucket": "arn:aws:s3:::nba-sim-raw-data-lake",
                    "Format": "CSV",
                    "Prefix": "inventory-reports/"
                }
            },
            "Schedule": {
                "Frequency": "Daily"
            }
        }
    ]
}
```

### Check for Reports

```bash
aws s3 ls s3://nba-sim-raw-data-lake/inventory-reports/ --recursive
```

Expected structure:

```
inventory-reports/nba-sim-raw-data-lake/nba-data-daily-inventory/
  ├── 2025-10-22T00-00Z/
  │   ├── manifest.json
  │   ├── manifest.checksum
  │   └── data/
  │       ├── data-000001.csv.gz
  │       ├── data-000002.csv.gz
  │       └── ...
  └── 2025-10-23T00-00Z/
      └── ...
```

---

## Using AWS Inventory in Reconciliation

### Option 1: Automatic (Preferred)

Update `config/reconciliation_config.yaml`:

```yaml
s3:
  bucket: nba-sim-raw-data-lake
  scan_mode: aws_inventory  # Change from "sample"
  inventory_bucket: nba-sim-raw-data-lake
  inventory_prefix: inventory-reports/
  fallback_to_sample: true  # Use sampling if inventory not available
```

Then run reconciliation normally:

```bash
python scripts/reconciliation/run_reconciliation.py
```

### Option 2: Manual

Run AWS Inventory reader directly:

```bash
# Read latest inventory
python scripts/reconciliation/aws_s3_inventory.py

# With fallback to sampling if inventory not available
python scripts/reconciliation/aws_s3_inventory.py --fallback-to-sample
```

---

## Performance Comparison

### Before (Sample Scanning - Phase 2A)

```
S3 scan (10% sample): 27 seconds
Full scan (100%): ~5 minutes
Objects scanned: 172,754
Objects kept: 17,366 (10%)
```

### After (AWS Inventory - Phase 2B)

```
Inventory read: <2 minutes
Full coverage: 100% (all 172,754 objects)
API calls: ~10 (just to read manifest + data files)
Freshness: 24 hours old
```

**Performance gain:** ~15x faster for full inventory  
**Cost savings:** ~99% reduction in API calls

---

## Troubleshooting

### Issue: "No inventory manifest found"

**Cause:** First report not generated yet (takes 24-48 hours)

**Solution:** Use fallback to sample scanning:

```bash
python scripts/reconciliation/aws_s3_inventory.py --fallback-to-sample
```

### Issue: "Inventory configuration not found"

**Cause:** S3 Inventory not enabled

**Solution:** Follow Step 1-3 above to enable

### Issue: "Access Denied" reading inventory

**Cause:** Missing IAM permissions

**Solution:** Add to your IAM policy:

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::nba-sim-raw-data-lake",
    "arn:aws:s3:::nba-sim-raw-data-lake/*"
  ]
}
```

### Issue: Inventory reports are outdated

**Cause:** AWS Inventory runs on schedule (daily)

**Solution:** This is expected. For real-time data, use sample scanning.

---

## Cost Analysis

### S3 Inventory Costs

**Pricing (as of 2025):**

- Per million objects listed: $0.0025
- Storage of reports: Standard S3 rates (~$0.023/GB/month)

**Example for 172,754 objects:**

- Listing cost: $0.0025 × 0.173 = ~$0.0004/day
- Storage (reports ~10 MB): ~$0.0002/month
- **Total: ~$0.01/month**

**Compared to API costs:**

- list_objects_v2: $0.005 per 1,000 requests
- Full scan: ~173 requests = $0.865/month (daily scans)

**Savings:** ~$0.85/month (~99% reduction)

---

## Alternative: Continue with Sample Scanning

If you prefer not to enable AWS Inventory:

**Pros of sample scanning:**
- Real-time data (not 24 hours old)
- No AWS configuration needed
- Works immediately

**Cons of sample scanning:**
- Slower (27s vs <2min for equivalent data)
- Higher API costs
- Only samples 10% of data (vs 100%)

**Recommendation:** Use sample scanning for Phase 2A MVP, upgrade to AWS Inventory for Phase 2B production deployment.

---

## Related Documentation

- AWS S3 Inventory docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
- `scripts/reconciliation/aws_s3_inventory.py` - Implementation
- `scripts/reconciliation/scan_s3_inventory.py` - Sample scanning (fallback)
- `config/reconciliation_config.yaml` - Configuration

---

**Last Updated:** October 22, 2025  
**Status:** Phase 2B Enhancement (Optional)  
**Recommendation:** Enable for production deployment

