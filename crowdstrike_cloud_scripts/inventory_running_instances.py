#!/usr/bin/env python3
"""
Query CrowdStrike Cloud Assets API to count RUNNING cloud instances.
Uses FalconPy SDK with proper status filtering for each cloud provider.
"""

import os
import sys
from falconpy import CloudSecurityAssets
from typing import Dict, Tuple

def get_falcon_credentials() -> Dict[str, str]:
    """Retrieve CrowdStrike API credentials from environment variables."""
    client_id = os.getenv("FALCON_CLIENT_ID")
    client_secret = os.getenv("FALCON_CLIENT_SECRET")
    base_url = os.getenv("FALCON_BASE_URL", "https://api.eu-1.crowdstrike.com")

    if not client_id or not client_secret:
        print("❌ Error: FALCON_CLIENT_ID or FALCON_CLIENT_SECRET not set")
        sys.exit(1)

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "base_url": base_url
    }

def query_running_instances(credentials: Dict[str, str]) -> Tuple[int, int, int]:
    """
    Query CrowdStrike Cloud Assets API for RUNNING instances only.

    Note: Different cloud providers use different status fields:
    - AWS EC2: Uses instance_state:"running"
    - GCP: Uses resource_type_name:"Compute Instance"+instance_state:"RUNNING"
    - Azure: Uses instance_state:"VM running"

    Returns:
        Tuple of (ec2_running, gcp_running, azure_running)
    """
    try:
        service_class = CloudSecurityAssets(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            base_url=credentials["base_url"]
        )

        ec2_running = 0
        gcp_running = 0
        azure_running = 0

        # Query for running EC2 instances
        print("🔍 Querying running EC2 instances...")
        ec2_filter = 'service:"EC2"+instance_state:"running"'
        ec2_result = service_class.query_assets(filter=ec2_filter, limit=1)

        if ec2_result.get("status_code") == 200:
            ec2_running = ec2_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"✅ Running EC2 instances: {ec2_running}")
        else:
            error = ec2_result.get("body", {}).get("errors", [{}])[0].get("message", "Unknown error")
            print(f"⚠️  Error querying EC2: {error}")

        # Query for running GCP instances (using resource_type_name:"Compute Instance"+instance_state:"RUNNING")
        print("🔍 Querying running GCP instances...")
        gcp_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"'
        gcp_result = service_class.query_assets(filter=gcp_filter, limit=1)

        if gcp_result.get("status_code") == 200:
            gcp_running = gcp_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"✅ Running GCP instances: {gcp_running}")
        else:
            error = gcp_result.get("body", {}).get("errors", [{}])[0].get("message", "Unknown error")
            print(f"⚠️  Error querying GCP: {error}")

        # Query for running Azure instances (using instance_state:"VM running")
        print("🔍 Querying running Azure instances...")
        azure_filter = 'service:"Virtual Machines"+instance_state:"VM running"'
        azure_result = service_class.query_assets(filter=azure_filter, limit=1)

        if azure_result.get("status_code") == 200:
            azure_running = azure_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"✅ Running Azure instances: {azure_running}")
        else:
            error = azure_result.get("body", {}).get("errors", [{}])[0].get("message", "Unknown error")
            print(f"⚠️  Error querying Azure: {error}")

        return ec2_running, gcp_running, azure_running

    except Exception as e:
        print(f"❌ Error during API query: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    print("🚀 CrowdStrike Running Instances Query Tool")
    print("-" * 50)

    credentials = get_falcon_credentials()
    print(f"🔑 Using base URL: {credentials['base_url']}\n")

    ec2_running, gcp_running, azure_running = query_running_instances(credentials)

    print("-" * 50)
    print(f"📊 Running Instances Summary:")
    print(f"   EC2 instances:  {ec2_running}")
    print(f"   GCP instances:  {gcp_running}")
    print(f"   Azure VMs:      {azure_running}")
    print(f"   Total Running:  {ec2_running + gcp_running + azure_running}")
    print("-" * 50)

if __name__ == "__main__":
    main()
