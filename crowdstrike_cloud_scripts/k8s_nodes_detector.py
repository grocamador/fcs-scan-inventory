#!/usr/bin/env python3
"""
CrowdStrike Cloud Assets - K8s Managed Nodes Detection
Query running instances and identify which are Kubernetes managed nodes (EKS, GKE)
"""

import os
import sys
import argparse
import json
from falconpy import CloudSecurityAssets
from typing import Dict, Tuple

def get_credentials(client_id: str = None, client_secret: str = None, base_url: str = None) -> Dict[str, str]:
    """Get CrowdStrike API credentials from args or environment."""
    # Use args if provided, otherwise fall back to environment
    cid = client_id or os.getenv("FALCON_CLIENT_ID")
    csec = client_secret or os.getenv("FALCON_CLIENT_SECRET")
    burl = base_url or os.getenv("FALCON_BASE_URL", "https://api.eu-1.crowdstrike.com")

    if not cid or not csec:
        print("❌ Error: API credentials not provided")
        print("   Use: --client-id and --client-secret, or set FALCON_CLIENT_ID/FALCON_CLIENT_SECRET")
        sys.exit(1)

    return {
        "client_id": cid,
        "client_secret": csec,
        "base_url": burl
    }

def query_k8s_nodes(cs: CloudSecurityAssets) -> Tuple[Dict, Dict]:
    """Query for K8s managed nodes (EKS and GKE)."""

    results = {
        "eks": {"total": 0, "clusters": {}},
        "gke": {"total": 0, "clusters": {}},
        "total_running": 0
    }

    # Get total running instances
    print("🔍 Querying total running instances...")
    ec2_result = cs.query_assets(filter='service:"EC2"+instance_state:"running"', limit=1)
    ec2_total = ec2_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)

    gcp_result = cs.query_assets(filter='resource_type_name:"Compute Instance"+instance_state:"RUNNING"', limit=1)
    gcp_total = gcp_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)

    results["total_running"] = ec2_total + gcp_total
    print(f"  AWS EC2 running: {ec2_total}")
    print(f"  GCP instances running: {gcp_total}")

    # Query EKS nodes - use tags
    print("\n🔍 Querying AWS EKS managed nodes...")
    eks_filter = 'service:"EC2"+instance_state:"running"+tag_key:"eks:cluster-name"'
    eks_result = cs.query_assets(filter=eks_filter, limit=1)
    eks_count = eks_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
    results["eks"]["total"] = eks_count
    print(f"  EKS nodes found: {eks_count}")

    # Query GKE nodes - use tags
    print("\n🔍 Querying GCP GKE managed nodes...")
    gke_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"+tag_key:"goog-k8s-cluster-name"'
    gke_result = cs.query_assets(filter=gke_filter, limit=1)
    gke_count = gke_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
    results["gke"]["total"] = gke_count
    print(f"  GKE nodes found: {gke_count}")

    return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Identify Kubernetes managed nodes in cloud assets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variables (FALCON_CLIENT_ID, FALCON_CLIENT_SECRET, FALCON_BASE_URL)
  %(prog)s

  # With explicit credentials
  %(prog)s --client-id YOUR_CLIENT_ID --client-secret YOUR_SECRET

  # Different region
  %(prog)s --client-id YOUR_ID --client-secret YOUR_SECRET --region us-1

  # Export results
  %(prog)s -o k8s_nodes.json
        """
    )

    parser.add_argument("--client-id", help="CrowdStrike API Client ID (env: FALCON_CLIENT_ID)")
    parser.add_argument("--client-secret", help="CrowdStrike API Client Secret (env: FALCON_CLIENT_SECRET)")
    parser.add_argument("--region", default="",
                       help="API Region (e.g., us-1, eu-1)")
    parser.add_argument("-o", "--output", help="Export results to JSON file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print("🚀 CrowdStrike K8s Managed Nodes Detection")
    print("=" * 60)

    # Build base URL
    if args.region:
        base_url = f"https://api.{args.region}.crowdstrike.com"
    else:
        # Use environment variable or empty (will use default from get_credentials)
        base_url = os.getenv("FALCON_BASE_URL", "")

    credentials = get_credentials(args.client_id, args.client_secret, base_url)

    if args.verbose:
        print(f"🔑 Using: {base_url}")
        print(f"🔑 Client ID: {credentials['client_id'][:10]}...")

    try:
        cs = CloudSecurityAssets(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            base_url=credentials["base_url"]
        )
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)

    results = query_k8s_nodes(cs)

    print("\n" + "=" * 60)
    print("📊 K8s Managed Nodes Summary")
    print("=" * 60)

    total_k8s = results["eks"]["total"] + results["gke"]["total"]
    total_running = results["total_running"]
    k8s_percentage = (total_k8s / total_running * 100) if total_running > 0 else 0

    print(f"\nTotal Running Instances:  {total_running}")
    print(f"  AWS EC2:                {results['total_running']} (queried)")
    print(f"  GCP Compute:            (queried)")

    print(f"\nK8s Managed Nodes:        {total_k8s} ({k8s_percentage:.1f}%)")
    print(f"  EKS Nodes (AWS):        {results['eks']['total']}")
    print(f"  GKE Nodes (GCP):        {results['gke']['total']}")
    print(f"  Unmanaged Instances:    {total_running - total_k8s} ({100 - k8s_percentage:.1f}%)")

    print("\n" + "=" * 60)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"📁 Results saved to: {args.output}")

if __name__ == "__main__":
    main()
