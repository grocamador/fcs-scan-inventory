#!/usr/bin/env python3
"""
Advanced query for CrowdStrike Cloud Assets - RUNNING instances only.
Supports filtering by cloud provider and export to JSON.
"""

import os
import sys
import json
import argparse
from falconpy import CloudSecurityAssets
from typing import Dict

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

def get_running_count(cs: CloudSecurityAssets, filter_str: str) -> int:
    """Execute filter and return count."""
    result = cs.query_assets(filter=filter_str, limit=1)
    if result.get("status_code") == 200:
        return result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
    else:
        error = result.get("body", {}).get("errors", [{}])[0].get("message", "Unknown error")
        print(f"⚠️  Error: {error}")
        return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query CrowdStrike Cloud Assets for RUNNING instances",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Count all running instances
  %(prog)s

  # Count running AWS EC2 only
  %(prog)s --cloud aws

  # Count running GCP only
  %(prog)s --cloud gcp

  # Export running instances to JSON
  %(prog)s -o running.json

  # Verbose mode
  %(prog)s -v
        """
    )

    parser.add_argument("-c", "--cloud", choices=["aws", "gcp", "azure"],
                       help="Cloud provider to query")
    parser.add_argument("-o", "--output", help="Output file for JSON results")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Show detailed output")

    args = parser.parse_args()

    print("🚀 CrowdStrike Running Instances Query")
    print("-" * 60)

    credentials = get_falcon_credentials()
    if args.verbose:
        print(f"🔑 Using base URL: {credentials['base_url']}\n")

    cs = CloudSecurityAssets(
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        base_url=credentials["base_url"]
    )

    results = {}

    # Define queries for each cloud provider
    queries = {
        'aws': {
            'filter': 'service:"EC2"+instance_state:"running"',
            'label': 'AWS EC2 - Running'
        },
        'gcp': {
            'filter': 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"',
            'label': 'Google Cloud - Running'
        },
        'azure': {
            'filter': 'service:"Virtual Machines"+instance_state:"VM running"',
            'label': 'Azure - Running'
        }
    }

    if args.cloud:
        # Query specific cloud provider
        if args.cloud in queries:
            q = queries[args.cloud]
            print(f"🔍 Querying {q['label']}...")
            count = get_running_count(cs, q['filter'])
            results[args.cloud] = count
            print(f"✅ {q['label']}: {count}")
    else:
        # Query all cloud providers
        for cloud, q in queries.items():
            print(f"🔍 Querying {q['label']}...")
            count = get_running_count(cs, q['filter'])
            results[cloud] = count
            print(f"✅ {q['label']}: {count}")

    print("-" * 60)
    print("📊 Summary - Running Instances:")

    total = 0
    for cloud, count in results.items():
        label = queries[cloud]['label']
        print(f"  {label:.<40} {count:>6}")
        total += count

    print(f"  {'TOTAL':.<40} {total:>6}")
    print("-" * 60)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"📁 Results saved to: {args.output}")

if __name__ == "__main__":
    main()
