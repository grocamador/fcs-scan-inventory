# 🚀 K8s Managed Nodes Detector

Query CrowdStrike Cloud Assets to identify and count Kubernetes managed nodes (EKS and GKE) by detecting cloud-provider specific tags.

## Overview

Detects running cloud instances that are part of managed Kubernetes clusters by identifying:
- **AWS EKS**: Nodes with `eks:cluster-name` tag
- **GCP GKE**: Nodes with `goog-k8s-cluster-name` tag

## Results

| Metric | Count |
|--------|------:|
| Total Running Instances (AWS EC2 + GCP) | 1,569 |
| EKS Nodes (AWS) | 15 |
| GKE Nodes (GCP) | 0 |
| K8s Managed Nodes | 15 (1.0%) |
| Unmanaged Instances | 1,554 (99.0%) |

## Usage

### Basic Usage (Using Environment Variables)
```bash
python3 k8s_nodes_detector.py
```

Uses:
- `FALCON_CLIENT_ID` environment variable
- `FALCON_CLIENT_SECRET` environment variable  
- `FALCON_BASE_URL` environment variable (or defaults to eu-1)

### With Explicit Credentials
```bash
python3 k8s_nodes_detector.py \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

### Specify Region
```bash
# US region
python3 k8s_nodes_detector.py --region us-1

# EU region
python3 k8s_nodes_detector.py --region eu-1
```

### Export to JSON
```bash
python3 k8s_nodes_detector.py -o k8s_nodes.json
```

### Verbose Mode
```bash
python3 k8s_nodes_detector.py -v
```

## Options

```
--client-id TEXT          CrowdStrike API Client ID (env: FALCON_CLIENT_ID)
--client-secret TEXT      CrowdStrike API Client Secret (env: FALCON_CLIENT_SECRET)
--region REGION           API Region (e.g., us-1, eu-1)
-o, --output FILE         Export results to JSON file
-v, --verbose             Show detailed output
-h, --help                Show help message
```

## Tag Detection Reference

### AWS EKS Nodes
The script detects nodes using this tag:
```
eks:cluster-name = <cluster-name>
```

Other EKS tags (for reference):
```
kubernetes.io/cluster/<cluster-name> = owned|shared
k8s.io/cluster-autoscaler/<cluster-name> = owned
k8s.io/cluster-autoscaler/enabled = true
eks:nodegroup-name = <nodegroup-name>
```

### GCP GKE Nodes
The script detects nodes using this tag:
```
goog-k8s-cluster-name = <cluster-name>
```

Other GKE tags (for reference):
```
goog-gke-node = ""
goog-k8s-cluster-location = <zone/region>
```

## Query Filters

### AWS EKS
```
Filter: service:"EC2"+instance_state:"running"+tag_key:"eks:cluster-name"
Count: 15 nodes
```

### GCP GKE
```
Filter: resource_type_name:"Compute Instance"+instance_state:"RUNNING"+tag_key:"goog-k8s-cluster-name"
Count: 0 nodes
```

## JSON Output Format

```json
{
  "eks": {
    "total": 15,
    "clusters": {}
  },
  "gke": {
    "total": 0,
    "clusters": {}
  },
  "total_running": 1569
}
```

## Example Commands

```bash
# Quick check (using environment variables)
python3 k8s_nodes_detector.py

# Detailed output with explicit credentials
python3 k8s_nodes_detector.py \
  --client-id abc123... \
  --client-secret xyz789... \
  --region eu-1 \
  -v

# Export for reporting
python3 k8s_nodes_detector.py \
  --region eu-1 \
  -o k8s_nodes_report.json

# Different region
python3 k8s_nodes_detector.py --region us-1
```

## Insights

- **1.0%** of running instances are part of EKS clusters
- **15 EKS nodes** detected with `eks:cluster-name` tag
- **0 GKE nodes** detected (no GCP Kubernetes instances running)
- **99.0%** of instances are unmanaged/non-Kubernetes

## Notes

- Region can be left empty to use `FALCON_BASE_URL` environment variable
- Client credentials can come from environment or command-line arguments
- JSON export useful for integration with other tools
- Tag-based detection is highly reliable for cloud-managed Kubernetes

## Files

- `k8s_nodes_detector.py` - Main detection script
