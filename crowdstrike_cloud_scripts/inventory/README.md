# Cloud Inventory

Unified tool to query and report on cloud infrastructure inventory, including running instances and Kubernetes managed nodes detection across AWS, GCP, and Azure.

## Features

- Query running instances across all cloud providers:
  - AWS EC2
  - GCP Compute Instances
  - Azure Virtual Machines
- Detect Kubernetes managed nodes:
  - AWS EKS (Elastic Kubernetes Service)
  - GCP GKE (Google Kubernetes Engine)
- Generate unified inventory reports (text and JSON)
- Optional file export

## Prerequisites

- Python 3.8+
- `falconpy` SDK installed
- Valid CrowdStrike API credentials

## Installation

```bash
pip install falconpy
```

## Usage

### Using environment variables

```bash
export FALCON_CLIENT_ID="your_client_id"
export FALCON_CLIENT_SECRET="your_client_secret"
export FALCON_BASE_URL="https://api.eu-1.crowdstrike.com"

python inventory_unified.py
```

### With command-line arguments

```bash
python inventory_unified.py \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET
```

### Save report to file

```bash
python inventory_unified.py -o inventory_report.txt
```

This generates two files:
- `inventory_report.txt` - Formatted text report
- `inventory_report.json` - Machine-readable JSON data

### Different API region

```bash
python inventory_unified.py --region us-1 -o report.txt
```

### Verbose output

```bash
python inventory_unified.py -v
```

## Output

The report includes:
- **Running Instances**: Count by cloud provider (EC2, GCP, Azure)
- **Kubernetes Managed Nodes**: Count by platform (EKS, GKE)
- **Summary**: Total managed vs unmanaged instances with percentages

### Example Output

```
╔══════════════════════════════════════════════════════════════════════╗
║          CrowdStrike Cloud Inventory Report - Unified                ║
╚══════════════════════════════════════════════════════════════════════╝

Generated: 2026-05-08 10:30:45

┌─ RUNNING INSTANCES ─────────────────────────────────────────────────┐
│                                                                      │
│  AWS EC2:              156 instances
│  GCP Compute:           42 instances
│  Azure VMs:             28 instances
│  ───────────────────────────────────
│  Total Running:        226 instances
...
```

## API Credentials

Ensure your CrowdStrike API credentials have the following permissions:
- `cloud-security-assets:read`

For production use, store credentials securely using environment variables or secrets management tools.

## Troubleshooting

### Authentication Error

Verify your credentials are correct:
```bash
echo $FALCON_CLIENT_ID
echo $FALCON_CLIENT_SECRET
```

### No Results

- Check that your cloud accounts are connected to CrowdStrike CNAPP
- Verify the API region matches your account location
- Ensure you have running instances in your cloud accounts

### Rate Limiting

If you encounter rate limits, the script uses batch queries optimized to minimize API calls.

## License

CrowdStrike API Tool
