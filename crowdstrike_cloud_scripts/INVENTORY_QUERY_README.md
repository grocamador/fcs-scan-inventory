# CrowdStrike Inventory Query Tools

Query CrowdStrike Cloud Assets API to count and export cloud instances (EC2, GCP, Azure, OCI) using FalconPy SDK.

## Prerequisites

- Python 3.9+
- FalconPy SDK (`crowdstrike-falconpy`)
- CrowdStrike API credentials (Client ID and Secret)

## Installation

```bash
# Install FalconPy
python3 -m pip install crowdstrike-falconpy

# Set environment variables (from your .zshrc or manually)
export FALCON_CLIENT_ID="your_client_id"
export FALCON_CLIENT_SECRET="your_client_secret"
export FALCON_BASE_URL="https://api.eu-1.crowdstrike.com"  # or your region
```

## Scripts

### 1. Simple Script: `inventory_query.py`

Basic query for EC2 and GCP instances.

```bash
python3 /Users/grocamador/inventory_query.py
```

**Output:**
```
🚀 CrowdStrike Inventory Query Tool
--------------------------------------------------
🔑 Using base URL: https://api.eu-1.crowdstrike.com
🔍 Querying EC2 instances...
✅ EC2 instances found: 42
🔍 Querying GCP instances...
✅ GCP instances found: 15
--------------------------------------------------
📊 Inventory Summary:
   EC2 instances:  42
   GCP instances:  15
   Total:          57
--------------------------------------------------
```

### 2. Advanced Script: `inventory_query_advanced.py`

Full-featured query tool with filtering, export, and detailed options.

```bash
# Default: Query EC2, GCP, and Azure
python3 /Users/grocamador/inventory_query_advanced.py

# Query specific cloud provider
python3 /Users/grocamador/inventory_query_advanced.py --cloud aws --type ec2

# Export results to JSON
python3 /Users/grocamador/inventory_query_advanced.py -o inventory.json

# Verbose output
python3 /Users/grocamador/inventory_query_advanced.py -v

# Show help
python3 /Users/grocamador/inventory_query_advanced.py --help
```

#### Advanced Script Options

```
Options:
  -c, --cloud {aws,gcp,azure,oci}    Cloud provider to query
  -t, --type RESOURCE_TYPE           Resource type (e.g., ec2, gcp, vm)
  -o, --output FILE                  Export results to JSON file
  -v, --verbose                      Show detailed output
```

#### Examples

```bash
# Count all AWS EC2 instances
python3 /Users/grocamador/inventory_query_advanced.py --cloud aws --type ec2

# Count all GCP instances
python3 /Users/grocamador/inventory_query_advanced.py --cloud gcp

# Count Azure VMs
python3 /Users/grocamador/inventory_query_advanced.py --cloud azure --type vm

# Export to JSON with verbose output
python3 /Users/grocamador/inventory_query_advanced.py -o /tmp/inventory.json -v
```

## API Credentials

The scripts look for these environment variables (configured in your `.zshrc`):

- `FALCON_CLIENT_ID` - Your CrowdStrike API client ID
- `FALCON_CLIENT_SECRET` - Your CrowdStrike API client secret
- `FALCON_BASE_URL` - API endpoint URL (defaults to EU-1)

These are already set in your `.zshrc`:
```bash
export FALCON_CLIENT_ID=540d434c252642a0a92a4cbb75da26f2
export FALCON_CLIENT_SECRET=ySxUEKjIub3ho4C2lLqmP5819YOQTv7XZ6N0kaVg
export FALCON_BASE_URL=https://api.eu-1.crowdstrike.com
```

## Supported Filters

The CloudSecurityAssets API supports filtering by:

- `cloud_provider`: aws, gcp, azure, oci
- `resource_type`: ec2, gcp, vm, etc.
- `region`: AWS regions
- `cloud_label`: Custom labels
- `status`: active, inactive, etc.

And many other fields as listed in the API documentation.

## Troubleshooting

### SSL Warning
Ignore the urllib3/LibreSSL warning - it's a known macOS issue and doesn't affect functionality.

### API Errors
- **400 Bad Request**: Check your filter syntax. Filters use FQL (Falcon Query Language).
- **401 Unauthorized**: Verify your API credentials are correct.
- **403 Forbidden**: Check your API client permissions.

### No Assets Found
- Ensure cloud accounts are registered with CrowdStrike CSPM
- Check that assets exist in your cloud provider

## API Reference

Query Function Signature:
```python
query_assets(filter: str = "", limit: int = 1) -> Dict
```

Filter syntax examples:
```python
# Single filter
'cloud_provider:"aws"'

# Multiple filters (AND)
'cloud_provider:"aws"+resource_type:"ec2"'

# Check /falcon-docs for complete filter field list
```

## Files

- `inventory_query.py` - Simple, focused EC2/GCP counter
- `inventory_query_advanced.py` - Full-featured query tool with CLI options
