# 🚀 CrowdStrike Running Instances Report

## Executive Summary

Successfully queried CrowdStrike Cloud Assets API to retrieve **RUNNING instances only** across multiple cloud providers, using provider-specific status fields.

### 📊 Results - RUNNING INSTANCES ONLY

| Cloud Provider | Instance Type | Running Count |
|---|---|---:|
| **AWS** | EC2 Running | **1,569** |
| **Google Cloud** | Compute Running | **102** |
| **Microsoft Azure** | VMs Running | **497** |
| | **TOTAL RUNNING** | **2,168** |

**Note:** This counts ONLY instances in running/active state, excluding stopped, terminated, or deallocated instances.

---

## Key Findings

| Metric | AWS EC2 | GCP | Azure |
|--------|---------|-----|-------|
| Total Instances | 202,166 | 103 | 2,647 |
| Running | 1,569 | 102 | 497 |
| Stopped/Inactive | 273+ | 1 | 2,150 |
| **% Running** | **0.8%** | **99%** | **18.8%** |

---

## Query Methodology

⚠️ **Important:** Different cloud providers use different status fields:

### AWS EC2
- **Filter:** `service:"EC2"+instance_state:"running"`
- **Status Field:** `instance_state`
- **Values:** "running", "stopped", "terminated", etc.

### Google Cloud Platform
- **Filter:** `service:"Compute Engine"+active:true`
- **Status Field:** `active` (boolean)
- **Note:** `instance_state` is not reliably populated for GCP in CrowdStrike API

### Microsoft Azure
- **Filter:** `service:"Virtual Machines"+active:true`
- **Status Field:** `active` (boolean)
- **Note:** `instance_state` is not reliably populated for Azure in CrowdStrike API

---

## Usage

### Simple Script - Running Instances Only
```bash
python3 /Users/grocamador/inventory_running_instances.py
```

**Output:**
```
📊 Running Instances Summary:
   EC2 instances:  1569
   GCP instances:  102
   Azure VMs:      497
   Total Running:  2168
```

### Advanced Script - With Options

```bash
# All running instances
python3 /Users/grocamador/inventory_running_advanced.py

# Specific cloud provider
python3 /Users/grocamador/inventory_running_advanced.py --cloud aws
python3 /Users/grocamador/inventory_running_advanced.py --cloud gcp
python3 /Users/grocamador/inventory_running_advanced.py --cloud azure

# Export to JSON
python3 /Users/grocamador/inventory_running_advanced.py -o running.json

# Verbose output
python3 /Users/grocamador/inventory_running_advanced.py -v
```

---

## Important Notes

### Filter Syntax Issues Discovered
- **Quote Values:** All filter values MUST be quoted: `instance_state:"running"` (NOT `instance_state:running`)
- **Combine with +:** Use `+` to combine filters: `service:"EC2"+instance_state:"running"`
- **Cloud-Specific:** Each cloud provider uses different status mechanisms

### API Response Differences
- **AWS:** Reliably populates `instance_state` field
- **GCP:** Does NOT populate `instance_state`; use `active:true/false` instead
- **Azure:** Does NOT populate `instance_state`; use `active:true/false` instead

### Stopped/Stopped Instances
- **EC2 Stopped Count:** 273 (queryable with `instance_state:"stopped"`)
- **Azure Deallocated:** 2,150 (large portion of inactive VMs)
- **GCP Inactive:** 1 (minimal deallocated instances)

---

## Files

- `inventory_running_instances.py` - Simple script (running instances only)
- `inventory_running_advanced.py` - Advanced script with filtering & export
- `RUNNING_INSTANCES_REPORT.md` - This report

## API Credentials

Uses environment variables set in `.zshrc`:
- `FALCON_CLIENT_ID`
- `FALCON_CLIENT_SECRET`
- `FALCON_BASE_URL`

---

## Verification

✅ **Both scripts tested and verified:**
- Correct status filtering for each cloud provider
- Accurate running instance counts
- JSON export working
- Cloud provider filtering working
- Verbose mode operational
