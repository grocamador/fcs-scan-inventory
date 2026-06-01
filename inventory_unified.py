#!/usr/bin/env python3
"""
CrowdStrike Cloud Inventory - Unified Report
Combines running instances and Kubernetes managed nodes detection in a single report
"""

import os
import sys
import warnings

os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"
warnings.filterwarnings("ignore")

import argparse
import json
from falconpy import CloudSecurityAssets
from typing import Dict, Tuple
from datetime import datetime


def get_credentials(client_id: str = None, client_secret: str = None, base_url: str = None) -> Dict[str, str]:
    """Get CrowdStrike API credentials from args or environment."""
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


def query_running_instances(cs: CloudSecurityAssets) -> Dict[str, int]:
    """Query for running instances across all clouds."""
    print("🔍 Querying running instances...")

    instances = {
        "ec2": 0,
        "gcp": 0,
        "azure": 0,
        "total": 0
    }

    try:
        # EC2 instances
        ec2_filter = 'service:"EC2"+instance_state:"running"'
        ec2_result = cs.query_assets(filter=ec2_filter, limit=1)
        if ec2_result.get("status_code") == 200:
            instances["ec2"] = ec2_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"  ✓ EC2 running: {instances['ec2']}")

        # GCP instances
        gcp_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"'
        gcp_result = cs.query_assets(filter=gcp_filter, limit=1)
        if gcp_result.get("status_code") == 200:
            instances["gcp"] = gcp_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"  ✓ GCP instances running: {instances['gcp']}")

        # Azure instances (regular VMs only)
        azure_filter = 'service:"Virtual Machines"+instance_state:"VM running"'
        azure_result = cs.query_assets(filter=azure_filter, limit=1)
        if azure_result.get("status_code") == 200:
            instances["azure"] = azure_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"  ✓ Azure VMs running: {instances['azure']}")

        instances["total"] = instances["ec2"] + instances["gcp"] + instances["azure"]
        return instances

    except Exception as e:
        print(f"❌ Error querying instances: {e}")
        sys.exit(1)


def query_k8s_nodes(cs: CloudSecurityAssets) -> Dict:
    """Query for Kubernetes managed nodes."""
    print("🔍 Querying Kubernetes managed nodes...")

    results = {
        "eks": 0,
        "gke": 0,
        "total": 0
    }

    try:
        # EKS nodes
        eks_filter = 'service:"EC2"+instance_state:"running"+tag_key:"eks:cluster-name"'
        eks_result = cs.query_assets(filter=eks_filter, limit=1)
        if eks_result.get("status_code") == 200:
            results["eks"] = eks_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"  ✓ EKS nodes found: {results['eks']}")

        # GKE nodes
        gke_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"+tag_key:"goog-k8s-cluster-name"'
        gke_result = cs.query_assets(filter=gke_filter, limit=1)
        if gke_result.get("status_code") == 200:
            results["gke"] = gke_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"  ✓ GKE nodes found: {results['gke']}")

        results["total"] = results["eks"] + results["gke"]
        return results

    except Exception as e:
        print(f"❌ Error querying K8s nodes: {e}")
        sys.exit(1)


def query_sensor_installation(cs: CloudSecurityAssets) -> Dict[str, Dict[str, int]]:
    """Query for sensor installation status across cloud providers."""
    print("🔍 Querying sensor installation status...")

    results = {
        "ec2": {"installed": 0, "not_installed": 0},
        "gcp": {"installed": 0, "not_installed": 0},
        "azure": {"installed": 0, "not_installed": 0},
    }

    try:
        # EC2 instances with sensor status
        ec2_filter = 'service:"EC2"+instance_state:"running"'
        ec2_result = cs.query_assets(filter=ec2_filter, limit=100)
        if ec2_result.get("status_code") == 200:
            resource_ids = ec2_result.get("body", {}).get("resources", [])
            if resource_ids:
                details = cs.cloud_security_assets_entities_get(ids=resource_ids)
                if details.get("status_code") == 200:
                    assets = details.get("body", {}).get("resources", [])
                    for asset in assets:
                        has_sensor = asset.get('cloud_context', {}).get('insights', {}).get('details', {}).get('enabledLoggingSources', {}).get('context', {}).get('hasSensor', False)
                        if has_sensor:
                            results["ec2"]["installed"] += 1
                        else:
                            results["ec2"]["not_installed"] += 1
                    print(f"  ✓ EC2: {results['ec2']['installed']} with sensor, {results['ec2']['not_installed']} without")

        # GCP instances with sensor status
        gcp_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"'
        gcp_result = cs.query_assets(filter=gcp_filter, limit=100)
        if gcp_result.get("status_code") == 200:
            resource_ids = gcp_result.get("body", {}).get("resources", [])
            if resource_ids:
                details = cs.cloud_security_assets_entities_get(ids=resource_ids)
                if details.get("status_code") == 200:
                    assets = details.get("body", {}).get("resources", [])
                    for asset in assets:
                        has_sensor = asset.get('cloud_context', {}).get('insights', {}).get('details', {}).get('enabledLoggingSources', {}).get('context', {}).get('hasSensor', False)
                        if has_sensor:
                            results["gcp"]["installed"] += 1
                        else:
                            results["gcp"]["not_installed"] += 1
                    print(f"  ✓ GCP: {results['gcp']['installed']} with sensor, {results['gcp']['not_installed']} without")

        # Azure instances with sensor status
        azure_filter = 'service:"Virtual Machines"+instance_state:"VM running"'
        azure_result = cs.query_assets(filter=azure_filter, limit=100)
        if azure_result.get("status_code") == 200:
            resource_ids = azure_result.get("body", {}).get("resources", [])
            if resource_ids:
                details = cs.cloud_security_assets_entities_get(ids=resource_ids)
                if details.get("status_code") == 200:
                    assets = details.get("body", {}).get("resources", [])
                    for asset in assets:
                        has_sensor = asset.get('cloud_context', {}).get('insights', {}).get('details', {}).get('enabledLoggingSources', {}).get('context', {}).get('hasSensor', False)
                        if has_sensor:
                            results["azure"]["installed"] += 1
                        else:
                            results["azure"]["not_installed"] += 1
                    print(f"  ✓ Azure: {results['azure']['installed']} with sensor, {results['azure']['not_installed']} without")

        return results

    except Exception as e:
        print(f"❌ Error querying sensor installation: {e}")
        sys.exit(1)


def query_aks_nodes(cs: CloudSecurityAssets) -> Dict:
    """Query for AKS managed nodes in Azure VMSS."""
    print("🔍 Querying Azure AKS nodes...")

    results = {
        "aks_nodes": 0
    }

    try:
        # AKS nodes have aks-managed-orchestrator tag
        aks_filter = 'resource_type_name:"Virtual Machine Scale Sets Virtual Machines"+tag_key:"aks-managed-orchestrator"'
        aks_result = cs.query_assets(filter=aks_filter, limit=1)
        if aks_result.get("status_code") == 200:
            results["aks_nodes"] = aks_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            print(f"  ✓ AKS nodes found: {results['aks_nodes']}")

        return results

    except Exception as e:
        print(f"❌ Error querying AKS nodes: {e}")
        sys.exit(1)



def generate_report(instances: Dict, k8s_nodes: Dict, aks: Dict, sensor: Dict, output_file: str = None) -> str:
    """Generate unified inventory report."""
    # Azure total includes regular VMs + AKS nodes
    azure_total = instances["azure"] + aks["aks_nodes"]
    total_running = instances["ec2"] + instances["gcp"] + azure_total
    total_k8s = k8s_nodes["total"] + aks["aks_nodes"]
    total_standalone = total_running - total_k8s

    report = f"""
╔══════════════════════════════════════════════════════════════════════╗
║          CrowdStrike Cloud Inventory Report - Unified                ║
╚══════════════════════════════════════════════════════════════════════╝

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

┌─ RUNNING INSTANCES (Standalone + Kubernetes nodes) ─────────────────┐
│                                                                      │
│  AWS EC2:              {instances['ec2']:>6} instances
│  GCP Compute:          {instances['gcp']:>6} instances
│  Azure VMs:            {azure_total:>6} instances
│  ───────────────────────────────────                               │
│  Total Running:        {total_running:>6} instances
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─ RUNNING KUBERNETES MANAGED NODES ──────────────────────────────────┐
│                                                                      │
│  EKS Nodes (AWS):      {k8s_nodes['eks']:>6} nodes
│  GKE Nodes (GCP):      {k8s_nodes['gke']:>6} nodes
│  AKS Nodes (Azure):    {aks['aks_nodes']:>6} nodes
│  ───────────────────────────────────                               │
│  Total K8s Managed:    {total_k8s:>6} nodes
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─ FALCON SENSOR INSTALLATION STATUS ─────────────────────────────────┐
│                                                                      │
│  AWS EC2:              {sensor['ec2']['installed']:>6} installed, {sensor['ec2']['not_installed']:>6} not installed
│  GCP Compute:          {sensor['gcp']['installed']:>6} installed, {sensor['gcp']['not_installed']:>6} not installed
│  Azure VMs:            {sensor['azure']['installed']:>6} installed, {sensor['azure']['not_installed']:>6} not installed
│  ───────────────────────────────────                               │
│  Total:                {sensor['ec2']['installed'] + sensor['gcp']['installed'] + sensor['azure']['installed']:>6} installed, {sensor['ec2']['not_installed'] + sensor['gcp']['not_installed'] + sensor['azure']['not_installed']:>6} not installed
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

Summary:
  • Total of {total_running} instances
  • {total_k8s} running as Kubernetes nodes
  • {total_standalone} running standalone
  • Breakdown: EKS {k8s_nodes['eks']} | GKE {k8s_nodes['gke']} | AKS {aks['aks_nodes']}
  • Sensor Coverage: {sensor['ec2']['installed'] + sensor['gcp']['installed'] + sensor['azure']['installed']} protected, {sensor['ec2']['not_installed'] + sensor['gcp']['not_installed'] + sensor['azure']['not_installed']} unprotected
"""

    if output_file:
        with open(output_file, "w") as f:
            f.write(report)

        json_data = {
            "timestamp": datetime.now().isoformat(),
            "instances": instances,
            "azure_total": azure_total,
            "k8s_nodes": k8s_nodes,
            "aks_nodes": aks,
            "sensor": sensor,
            "summary": {
                "total_running": total_running,
                "total_k8s_managed": total_k8s,
                "total_standalone": total_standalone,
                "eks_nodes": k8s_nodes['eks'],
                "gke_nodes": k8s_nodes['gke'],
                "aks_nodes": aks['aks_nodes'],
                "sensor_installed": sensor['ec2']['installed'] + sensor['gcp']['installed'] + sensor['azure']['installed'],
                "sensor_not_installed": sensor['ec2']['not_installed'] + sensor['gcp']['not_installed'] + sensor['azure']['not_installed']
            }
        }
        json_file = output_file.replace(".txt", ".json")
        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"\n📁 Report saved:")
        print(f"   • {output_file}")
        print(f"   • {json_file}")

    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CrowdStrike Cloud Inventory - Unified Report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variables
  %(prog)s

  # With explicit credentials
  %(prog)s --client-id YOUR_ID --client-secret YOUR_SECRET

  # Save report to file
  %(prog)s -o inventory_report.txt

  # Different region
  %(prog)s --region us-1 -o report.txt
        """
    )

    parser.add_argument("--client-id", help="CrowdStrike API Client ID")
    parser.add_argument("--client-secret", help="CrowdStrike API Client Secret")
    parser.add_argument("--region", default="", help="API Region (e.g., us-1, eu-1)")
    parser.add_argument("-o", "--output", help="Save report to file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print("🚀 CrowdStrike Cloud Inventory Report (Unified)")
    print("=" * 70)

    if args.region:
        base_url = f"https://api.{args.region}.crowdstrike.com"
    else:
        base_url = None

    credentials = get_credentials(args.client_id, args.client_secret, base_url)

    if args.verbose:
        print(f"🔑 Using base URL: {credentials['base_url']}\n")

    try:
        cs = CloudSecurityAssets(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            base_url=credentials["base_url"]
        )
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)

    instances = query_running_instances(cs)
    k8s_nodes = query_k8s_nodes(cs)
    aks = query_aks_nodes(cs)
    sensor = query_sensor_installation(cs)

    report = generate_report(instances, k8s_nodes, aks, sensor, args.output)
    print(report)


if __name__ == "__main__":
    main()
