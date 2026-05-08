#!/usr/bin/env python3
"""
Query CrowdStrike Cloud Assets API to count EC2 and GCP instances.
Uses FalconPy SDK for API interaction.
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

def query_inventory(credentials: Dict[str, str]) -> Tuple[int, int]:
    """
    Query CrowdStrike Cloud Assets API for EC2 and GCP instances.

    Returns:
        Tuple of (ec2_count, gcp_count)
    """
    try:
        service_class = CloudSecurityAssets(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            base_url=credentials["base_url"]
        )

        ec2_count = 0
        gcp_count = 0

        # Query for EC2 instances
        print("🔍 Querying EC2 instances...")
        ec2_filter = 'service:"EC2"'
        ec2_result = service_class.query_assets(filter=ec2_filter, limit=1)

        if ec2_result.get("status_code") == 200:
            ec2_count = ec2_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"✅ EC2 instances found: {ec2_count}")
        else:
            print(f"⚠️  Error querying EC2: {ec2_result}")

        # Query for GCP instances
        print("🔍 Querying GCP instances...")
        gcp_filter = 'service:"Compute Engine"'
        gcp_result = service_class.query_assets(filter=gcp_filter, limit=1)

        if gcp_result.get("status_code") == 200:
            gcp_count = gcp_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"✅ GCP instances found: {gcp_count}")
        else:
            print(f"⚠️  Error querying GCP: {gcp_result}")

        return ec2_count, gcp_count

    except Exception as e:
        print(f"❌ Error during API query: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    print("🚀 CrowdStrike Inventory Query Tool")
    print("-" * 50)

    credentials = get_falcon_credentials()
    print(f"🔑 Using base URL: {credentials['base_url']}")

    ec2_count, gcp_count = query_inventory(credentials)

    print("-" * 50)
    print(f"📊 Inventory Summary:")
    print(f"   EC2 instances:  {ec2_count}")
    print(f"   GCP instances:  {gcp_count}")
    print(f"   Total:          {ec2_count + gcp_count}")
    print("-" * 50)

if __name__ == "__main__":
    main()
