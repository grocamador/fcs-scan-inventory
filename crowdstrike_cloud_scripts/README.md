# CrowdStrike Cloud Scripts

Collection of Python scripts for querying and analyzing cloud assets via CrowdStrike Cloud Security Platform (CSPM).

## 📁 Directory Structure

```
crowdstrike_cloud_scripts/
├── README.md                              (this file)
│
├── INVENTORY SCRIPTS
├── inventory_query.py                     (simple EC2/GCP count)
├── inventory_query_advanced.py            (advanced with filters)
├── INVENTORY_QUERY_README.md
├── INVENTORY_RESULTS.md
│
├── RUNNING INSTANCES SCRIPTS
├── inventory_running_instances.py         (simple running instances)
├── inventory_running_advanced.py          (advanced with filtering)
├── inventory_running_verified.py          (verified filters)
├── RUNNING_INSTANCES_FINAL.md
├── RUNNING_INSTANCES_REPORT.md
├── RUNNING_INSTANCES_VERIFIED.md
│
├── K8S NODES DETECTOR
├── k8s_nodes_detector.py                  (EKS/GKE node detection)
└── K8S_NODES_DETECTOR.md
```

## 🚀 Quick Start

### 1. Set Environment Variables
```bash
export FALCON_CLIENT_ID="your_client_id"
export FALCON_CLIENT_SECRET="your_client_secret"
export FALCON_BASE_URL="https://api.eu-1.crowdstrike.com"  # or us-1
```

### 2. Run Scripts

**Count all instances (inventory):**
```bash
python3 inventory_query.py
```

**Count running instances only:**
```bash
python3 inventory_running_instances.py
```

**Detect Kubernetes managed nodes:**
```bash
python3 k8s_nodes_detector.py
```

## 📊 Scripts Overview

### Inventory Scripts
- `inventory_query.py` - Simple query for EC2 and GCP counts
- `inventory_query_advanced.py` - Advanced with cloud filtering, export to JSON

**Results:** Total 204,916 instances
- AWS EC2: 202,166
- GCP: 103
- Azure: 2,647

### Running Instances Scripts
- `inventory_running_instances.py` - Running instances only (simple)
- `inventory_running_advanced.py` - Running instances with filtering
- `inventory_running_verified.py` - Verified filters per cloud

**Results:** Total 1,669 running instances
- AWS EC2: 1,567
- GCP: 0
- Azure: 102

### K8s Nodes Detector
- `k8s_nodes_detector.py` - Identifies Kubernetes managed nodes (EKS/GKE)

**Results:**
- EKS Nodes: 15 (1.0% of running instances)
- GKE Nodes: 0
- Unmanaged: 1,554 (99.0%)

## 🔑 Authentication

### Option 1: Environment Variables
```bash
export FALCON_CLIENT_ID="your_id"
export FALCON_CLIENT_SECRET="your_secret"
export FALCON_BASE_URL="https://api.eu-1.crowdstrike.com"
```

### Option 2: Command Line Arguments
```bash
python3 script.py --client-id YOUR_ID --client-secret YOUR_SECRET --region eu-1
```

### Option 3: Mix (CLI overrides env)
```bash
python3 k8s_nodes_detector.py --region us-1
```

## 📋 Supported Filters

### AWS EC2
- **Running:** `service:"EC2"+instance_state:"running"`
- **EKS Nodes:** `service:"EC2"+instance_state:"running"+tag_key:"eks:cluster-name"`

### GCP
- **Running:** `resource_type_name:"Compute Instance"+instance_state:"RUNNING"`
- **GKE Nodes:** `resource_type_name:"Compute Instance"+instance_state:"RUNNING"+tag_key:"goog-k8s-cluster-name"`

### Azure
- **Running:** `service:"Virtual Machines"+instance_state:"VM running"`

## 💡 Usage Examples

```bash
# Simple inventory check
python3 inventory_query.py

# Count running instances with details
python3 inventory_running_instances.py -v

# Check Kubernetes nodes
python3 k8s_nodes_detector.py

# Export to JSON
python3 k8s_nodes_detector.py -o results.json

# Specific region
python3 inventory_running_advanced.py --cloud aws --region us-1

# With explicit credentials
python3 k8s_nodes_detector.py \
  --client-id abc123 \
  --client-secret xyz789 \
  --region eu-1
```

## 📚 Documentation

- `INVENTORY_QUERY_README.md` - Detailed inventory script guide
- `RUNNING_INSTANCES_FINAL.md` - Running instances query details
- `K8S_NODES_DETECTOR.md` - Kubernetes node detection guide

## 🔧 Requirements

- Python 3.9+
- FalconPy SDK: `pip install crowdstrike-falconpy`
- CrowdStrike API credentials

## 📊 Current Inventory Status

| Metric | Count |
|--------|------:|
| Total Cloud Instances | 204,916 |
| Running Instances | 1,669 |
| K8s Managed Nodes | 15 |
| Utilization Rate | 0.8% |

---

**Last Updated:** May 8, 2026
**Region:** EU-1 (default)
