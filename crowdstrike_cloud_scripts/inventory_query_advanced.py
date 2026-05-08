#!/usr/bin/env python3
"""
Query CrowdStrike Cloud Assets API to count various cloud instances.
Uses FalconPy SDK for API interaction with optional filtering and export.
"""

import os
import sys
import json
import argparse
from falconpy import CloudSecurityAssets
from typing import Dict, List, Tuple

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

def query_inventory(credentials: Dict[str, str], cloud_provider: str = None,
                   resource_type: str = None) -> Tuple[int, List[Dict]]:
    """
    Query CrowdStrike Cloud Assets API.

    Args:
        credentials: API credentials dict
        cloud_provider: Filter by cloud provider (aws, gcp, azure, oci)
        resource_type: Filter by resource type (ec2, gcp, etc)

    Returns:
        Tuple of (total_count, resources)
    """
    try:
        service_class = CloudSecurityAssets(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            base_url=credentials["base_url"]
        )

        filter_parts = []
        if cloud_provider:
            filter_parts.append(f'cloud_provider:"{cloud_provider}"')
        if resource_type:
            filter_parts.append(f'resource_type:"{resource_type}"')

        query_filter = "+".join(filter_parts) if filter_parts else ""

        result = service_class.query_assets(filter=query_filter, limit=1)

        if result.get("status_code") == 200:
            total = result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            resources = result.get("body", {}).get("resources", [])
            return total, resources
        else:
            error_msg = result.get("body", {}).get("errors", [{}])[0].get("message", "Unknown error")
            print(f"❌ API Error: {error_msg}")
            return 0, []

    except Exception as e:
        print(f"❌ Error during API query: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query CrowdStrike Cloud Assets inventory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Count all EC2 and GCP instances
  %(prog)s

  # Count only AWS EC2 instances
  %(prog)s --cloud aws --type ec2

  # Count all GCP resources
  %(prog)s --cloud gcp

  # Export results to JSON
  %(prog)s -o inventory.json
        """
    )

    parser.add_argument("-c", "--cloud", choices=["aws", "gcp", "azure", "oci"],
                       help="Cloud provider to query")
    parser.add_argument("-t", "--type", dest="resource_type",
                       help="Resource type to query (e.g., ec2, gcp, vm)")
    parser.add_argument("-o", "--output", help="Output file for JSON results")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Show detailed output")

    args = parser.parse_args()

    print("🚀 CrowdStrike Inventory Query Tool")
    print("-" * 60)

    credentials = get_falcon_credentials()
    if args.verbose:
        print(f"🔑 Using base URL: {credentials['base_url']}")

    service_class = CloudSecurityAssets(
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        base_url=credentials["base_url"]
    )

    results = {}

    # If specific filters provided
    if args.cloud or args.resource_type:
        provider = args.cloud or "all"
        rtype = args.resource_type or "all"
        print(f"🔍 Querying {provider}/{rtype}...")

        count, resources = query_inventory(
            credentials,
            cloud_provider=args.cloud,
            resource_type=args.resource_type
        )

        key = f"{provider}_{rtype}"
        results[key] = {"count": count, "resources": resources}
        print(f"✅ Found {count} assets")
    else:
        # Default: query EC2 and GCP
        queries = [
            ("EC2", 'service:"EC2"', "EC2 Instances"),
            ("GCP Compute Engine", 'service:"Compute Engine"', "GCP Instances"),
            ("Azure VM", 'service:"Virtual Machines"', "Azure VMs"),
        ]

        for label, flt, display_label in queries:
            print(f"🔍 Querying {display_label}...")
            result = service_class.query_assets(filter=flt, limit=1)
            if result.get("status_code") == 200:
                count = result.get('body', {}).get('meta', {}).get('pagination', {}).get('total', 0)
                results[display_label] = count
                print(f"   ✅ {display_label}: {count}")
            else:
                results[display_label] = 0
                print(f"   ❌ Error querying {display_label}")

    print("-" * 60)
    print(f"📊 Inventory Summary:")

    if isinstance(results.get(list(results.keys())[0]), dict):
        # Detailed results
        for key, data in results.items():
            print(f"   {key}: {data['count']}")
    else:
        # Summary results
        total = sum(results.values())
        for label, count in results.items():
            print(f"   {label}: {count}")
        print(f"   Total: {total}")

    print("-" * 60)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"📁 Results saved to: {args.output}")

if __name__ == "__main__":
    main()
