# Cloud Inventory

Unified tool to query and report on cloud infrastructure inventory across AWS, GCP, and Azure, with comprehensive Kubernetes cluster node detection.

## Features

- Query running instances across all cloud providers:
  - AWS EC2 instances
  - GCP Compute instances
  - Azure Virtual Machines (including VMSS VMs)
- Detect Kubernetes managed nodes:
  - AWS EKS (Elastic Kubernetes Service) nodes
  - GCP GKE (Google Kubernetes Engine) nodes
  - Azure AKS (Azure Kubernetes Service) nodes
- Generate unified inventory reports (text and JSON formats)
- Optional file export for reports
- Clean summary showing standalone vs Kubernetes-managed instances

## Prerequisites

- Python 3.8+
- `falconpy` SDK installed
- Valid CrowdStrike API credentials with `cloud-security-assets:read` scope

## Installation

```bash
python3 -m pip install crowdstrike-falconpy
```

## API Credentials Setup

### Creating an API Key

1. Log in to your CrowdStrike Falcon console
2. Navigate to **Support and resources** → **API Clients and Keys**
3. Click **Add API Client**
4. Fill in the following details:
   - **Client Name**: (e.g., "Cloud Inventory Tool")
   - **Client Type**: Select your preferred type
5. Under **API Scopes**, add the required scope:
   - `cloud-security-assets:read`
6. Click **Add** to create the API client
7. Save your **Client ID** and **Client Secret** securely

### API Credentials Requirements

Ensure your CrowdStrike API credentials have the following permissions:
- `cloud-security-assets:read` - Required to query cloud assets inventory

For production use, store credentials securely using environment variables or secrets management tools.

## Usage

### Using environment variables

```bash
export FALCON_CLIENT_ID="your_client_id"
export FALCON_CLIENT_SECRET="your_client_secret"
export FALCON_BASE_URL="https://api.eu-1.crowdstrike.com"

python3 inventory_unified.py
```

### With command-line arguments

```bash
python3 inventory_unified.py \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

### Save report to file

```bash
python3 inventory_unified.py -o inventory_report.txt
```

This generates two files:
- `inventory_report.txt` - Formatted text report
- `inventory_report.json` - Machine-readable JSON data

### Different API region

```bash
python3 inventory_unified.py --region us-1 -o report.txt
```

### Verbose output

```bash
python3 inventory_unified.py -v
```

## Output

The report provides a comprehensive overview of your cloud infrastructure:
- **Running Instances**: Total count by cloud provider (EC2, GCP, Azure)
- **Kubernetes Managed Nodes**: Breakdown by platform (EKS, GKE, AKS)
- **Summary**: Clear recap showing total instances and standalone vs managed nodes

### Example Output

```
🚀 CrowdStrike Cloud Inventory Report (Unified)
======================================================================
🔍 Querying running instances...
  ✓ EC2 running: 40
  ✓ GCP instances running: 3
  ✓ Azure VMs running: 108
🔍 Querying Kubernetes managed nodes...
  ✓ EKS nodes found: 13
  ✓ GKE nodes found: 3
🔍 Querying Azure AKS nodes...
  ✓ AKS nodes found: 125

╔══════════════════════════════════════════════════════════════════════╗
║          CrowdStrike Cloud Inventory Report - Unified                ║
╚══════════════════════════════════════════════════════════════════════╝

Generated: 2026-05-13 11:19:01

┌─ RUNNING INSTANCES (Standalone + Kubernetes nodes) ─────────────────┐
│                                                                      │
│  AWS EC2:                  40 instances
│  GCP Compute:               3 instances
│  Azure VMs:               233 instances
│  ───────────────────────────────────                               │
│  Total Running:           276 instances
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─ RUNNING KUBERNETES MANAGED NODES ──────────────────────────────────┐
│                                                                      │
│  EKS Nodes (AWS):          13 nodes
│  GKE Nodes (GCP):           3 nodes
│  AKS Nodes (Azure):       125 nodes
│  ───────────────────────────────────                               │
│  Total K8s Managed:       141 nodes
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

Summary:
  • Total of 276 instances
  • 141 running as Kubernetes nodes
  • 135 running standalone
  • Breakdown: EKS 13 | GKE 3 | AKS 125
```

### JSON Output

When saving to file with `-o report.txt`, an additional JSON file (`report.json`) is generated with machine-readable data:

```json
{
  "timestamp": "2026-05-13T11:19:01.123456",
  "instances": {
    "ec2": 40,
    "gcp": 3,
    "azure": 108,
    "total": 151
  },
  "azure_total": 233,
  "k8s_nodes": {
    "eks": 13,
    "gke": 3,
    "total": 16
  },
  "aks_nodes": {
    "aks_nodes": 125
  },
  "summary": {
    "total_running": 276,
    "total_k8s_managed": 141,
    "total_standalone": 135,
    "eks_nodes": 13,
    "gke_nodes": 3,
    "aks_nodes": 125
  }
}
```

## Troubleshooting

### Authentication Error

Verify your credentials are correct:
```bash
echo $FALCON_CLIENT_ID
echo $FALCON_CLIENT_SECRET
```

Ensure your API client has the `cloud-security-assets:read` scope. Check the [API Credentials Setup](#api-credentials-setup) section above.

### No Results

- Verify your cloud accounts are connected to CrowdStrike Falcon Cloud Security Platform
- Confirm the API region matches your account location (e.g., `eu-1` for Europe, `us-1` for US)
- Ensure you have running instances in your cloud accounts
- Check that the API client has proper permissions

### Empty Instance Counts

If one cloud provider shows 0 instances:
- Verify the account is properly configured in CrowdStrike
- Check that resources in that cloud are actively running (not stopped/deallocated)
- Ensure the API region is correct for where your resources are deployed

### Performance

- The script makes 4 API calls per execution (1 per cloud provider + 2 for K8s nodes)
- Each query is optimized to request only count metadata, not full asset details
- Typical execution time: 15-25 seconds depending on network latency

## Advanced Usage

### Scheduling Reports

Generate reports on a regular schedule using cron:

```bash
# Daily report at 9 AM
0 9 * * * cd /path/to/fcs-scan-inventory && python3 inventory_unified.py -o reports/daily_$(date +\%Y\%m\%d).txt
```

### Integration with Monitoring

Use the JSON output for integration with monitoring systems:

```bash
python3 inventory_unified.py -o inventory_report.txt
# Read the JSON file for programmatic access
jq '.summary' inventory_report.json
```

## License

CrowdStrike API Tool
