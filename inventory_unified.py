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
import csv
from falconpy import CloudSecurityAssets
from typing import Dict, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


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

    def get_ec2():
        ec2_filter = 'service:"EC2"+instance_state:"running"'
        ec2_result = cs.query_assets(filter=ec2_filter, limit=1)
        if ec2_result.get("status_code") == 200:
            return ec2_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
        return 0

    def get_gcp():
        gcp_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"'
        gcp_result = cs.query_assets(filter=gcp_filter, limit=1)
        if gcp_result.get("status_code") == 200:
            return gcp_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
        return 0

    def get_azure():
        azure_filter = 'service:"Virtual Machines"+instance_state:"VM running"'
        azure_result = cs.query_assets(filter=azure_filter, limit=1)
        if azure_result.get("status_code") == 200:
            return azure_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
        return 0

    with ThreadPoolExecutor(max_workers=3) as executor:
        ec2_future = executor.submit(get_ec2)
        gcp_future = executor.submit(get_gcp)
        azure_future = executor.submit(get_azure)

        instances["ec2"] = ec2_future.result()
        instances["gcp"] = gcp_future.result()
        instances["azure"] = azure_future.result()

    print(f"  ✓ EC2 running: {instances['ec2']}")
    print(f"  ✓ GCP instances running: {instances['gcp']}")
    print(f"  ✓ Azure VMs running: {instances['azure']}")

    instances["total"] = instances["ec2"] + instances["gcp"] + instances["azure"]
    return instances


def query_k8s_nodes(cs: CloudSecurityAssets) -> Dict:
    """Query for Kubernetes managed nodes."""
    print("🔍 Querying Kubernetes managed nodes...")

    results = {
        "eks": 0,
        "gke": 0,
        "total": 0
    }

    def get_eks():
        eks_filter = 'service:"EC2"+instance_state:"running"+tag_key:"aws:eks:cluster-name"'
        eks_result = cs.query_assets(filter=eks_filter, limit=1)
        if eks_result.get("status_code") == 200:
            return eks_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
        return 0

    def get_gke():
        gke_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"+tag_key:"goog-k8s-cluster-name"'
        gke_result = cs.query_assets(filter=gke_filter, limit=1)
        if gke_result.get("status_code") == 200:
            return gke_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
        return 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        eks_future = executor.submit(get_eks)
        gke_future = executor.submit(get_gke)

        results["eks"] = eks_future.result()
        results["gke"] = gke_future.result()

    print(f"  ✓ EKS nodes found: {results['eks']}")
    print(f"  ✓ GKE nodes found: {results['gke']}")

    results["total"] = results["eks"] + results["gke"]
    return results


def query_sensor_installation(cs: CloudSecurityAssets) -> Dict:
    """Query for Sensor Crowdstrike installation status across cloud providers, differentiating VMs and K8s nodes."""
    print("🔍 Querying Sensor Crowdstrike installation status...")

    results = {
        "ec2_vms": {"installed": 0, "not_installed": 0},
        "ec2_eks": {"installed": 0, "not_installed": 0},
        "gcp_vms": {"installed": 0, "not_installed": 0},
        "gcp_gke": {"installed": 0, "not_installed": 0},
        "azure_vms": {"installed": 0, "not_installed": 0},
        "azure_aks": {"installed": 0, "not_installed": 0},
    }

    def query_with_pagination(filter_str, resource_key):
        """Helper to query with pagination and count sensor installation."""
        counts = {"installed": 0, "not_installed": 0}
        offset = 0
        while True:
            result = cs.query_assets(filter=filter_str, limit=100, offset=offset)
            if result.get("status_code") != 200:
                break
            resource_ids = result.get("body", {}).get("resources", [])
            if not resource_ids:
                break

            details = cs.cloud_security_assets_entities_get(ids=resource_ids)
            if details.get("status_code") == 200:
                assets = details.get("body", {}).get("resources", [])
                for asset in assets:
                    managed_by = asset.get('cloud_context', {}).get('host', {}).get('managed_by', 'Unmanaged')
                    if managed_by == "Sensor":
                        counts["installed"] += 1
                    else:
                        counts["not_installed"] += 1

            total = result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            offset += 100
            if offset >= total:
                break

        return counts

    def query_eks_nodes():
        eks_filter = 'service:"EC2"+instance_state:"running"+tag_key:"aws:eks:cluster-name"'
        return query_with_pagination(eks_filter, "ec2_eks")

    def query_ec2_vms():
        ec2_filter = 'service:"EC2"+instance_state:"running"'
        ec2_counts = {"installed": 0, "not_installed": 0}
        offset = 0
        while True:
            ec2_result = cs.query_assets(filter=ec2_filter, limit=100, offset=offset)
            if ec2_result.get("status_code") != 200:
                break
            resource_ids = ec2_result.get("body", {}).get("resources", [])
            if not resource_ids:
                break

            details = cs.cloud_security_assets_entities_get(ids=resource_ids)
            if details.get("status_code") == 200:
                assets = details.get("body", {}).get("resources", [])
                for asset in assets:
                    managed_by = asset.get('cloud_context', {}).get('host', {}).get('managed_by', 'Unmanaged')
                    is_eks = 'aws:eks:cluster-name' in asset.get('cloud_context', {}).get('tags', {})
                    if not is_eks:
                        if managed_by == "Sensor":
                            ec2_counts["installed"] += 1
                        else:
                            ec2_counts["not_installed"] += 1

            total = ec2_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            offset += 100
            if offset >= total:
                break
        return ec2_counts

    def query_gke_nodes():
        gke_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"+tag_key:"goog-k8s-cluster-name"'
        return query_with_pagination(gke_filter, "gcp_gke")

    def query_gcp_vms():
        gcp_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"'
        gcp_counts = {"installed": 0, "not_installed": 0}
        offset = 0
        while True:
            gcp_result = cs.query_assets(filter=gcp_filter, limit=100, offset=offset)
            if gcp_result.get("status_code") != 200:
                break
            resource_ids = gcp_result.get("body", {}).get("resources", [])
            if not resource_ids:
                break

            details = cs.cloud_security_assets_entities_get(ids=resource_ids)
            if details.get("status_code") == 200:
                assets = details.get("body", {}).get("resources", [])
                for asset in assets:
                    managed_by = asset.get('cloud_context', {}).get('host', {}).get('managed_by', 'Unmanaged')
                    is_gke = 'goog-k8s-cluster-name' in asset.get('cloud_context', {}).get('tags', {})
                    if not is_gke:
                        if managed_by == "Sensor":
                            gcp_counts["installed"] += 1
                        else:
                            gcp_counts["not_installed"] += 1

            total = gcp_result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            offset += 100
            if offset >= total:
                break
        return gcp_counts

    def query_azure_aks():
        aks_filter = 'resource_type_name:"Virtual Machine Scale Sets Virtual Machines"+tag_key:"aks-managed-orchestrator"'
        return query_with_pagination(aks_filter, "azure_aks")

    def query_azure_vms():
        azure_filter = 'service:"Virtual Machines"+instance_state:"VM running"'
        return query_with_pagination(azure_filter, "azure_vms")

    try:
        with ThreadPoolExecutor(max_workers=6) as executor:
            eks_future = executor.submit(query_eks_nodes)
            ec2_future = executor.submit(query_ec2_vms)
            gke_future = executor.submit(query_gke_nodes)
            gcp_future = executor.submit(query_gcp_vms)
            aks_future = executor.submit(query_azure_aks)
            azure_future = executor.submit(query_azure_vms)

            results["ec2_eks"] = eks_future.result()
            results["ec2_vms"] = ec2_future.result()
            results["gcp_gke"] = gke_future.result()
            results["gcp_vms"] = gcp_future.result()
            results["azure_aks"] = aks_future.result()
            results["azure_vms"] = azure_future.result()

        return results

    except Exception as e:
        print(f"❌ Error querying Sensor installation status: {e}")
        sys.exit(1)


def query_aks_nodes(cs: CloudSecurityAssets) -> Dict:
    """Query for AKS managed nodes in Azure VMSS."""
    print("🔍 Querying Azure AKS nodes...")

    results = {
        "aks_nodes": 0
    }

    try:
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

    # Calculate sensor totals
    total_vms_installed = sensor["ec2_vms"]["installed"] + sensor["gcp_vms"]["installed"] + sensor["azure_vms"]["installed"]
    total_vms_not_installed = sensor["ec2_vms"]["not_installed"] + sensor["gcp_vms"]["not_installed"] + sensor["azure_vms"]["not_installed"]
    total_nodes_installed = sensor["ec2_eks"]["installed"] + sensor["gcp_gke"]["installed"] + sensor["azure_aks"]["installed"]
    total_nodes_not_installed = sensor["ec2_eks"]["not_installed"] + sensor["gcp_gke"]["not_installed"] + sensor["azure_aks"]["not_installed"]
    total_all_installed = total_vms_installed + total_nodes_installed
    total_all_not_installed = total_vms_not_installed + total_nodes_not_installed

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

Summary:
  • Total of {total_running} instances
  • {total_k8s} running as Kubernetes nodes
  • {total_standalone} running standalone
  • Breakdown: EKS {k8s_nodes['eks']} | GKE {k8s_nodes['gke']} | AKS {aks['aks_nodes']}

┌─ SENSOR CROWDSTRIKE INSTALLED ──────────────────────────────────────┐
│                                                                      │
│  Type          Installed  Not Installed                             │
│  ──────────────────────────────────────                             │
│  VMs:          {total_vms_installed:>9} {total_vms_not_installed:>13}
│  Nodes:        {total_nodes_installed:>9} {total_nodes_not_installed:>13}
│  ──────────────────────────────────────                             │
│  Total:        {total_all_installed:>9} {total_all_not_installed:>13}
│                                                                      │
│  Breakdown by Cloud:                                                │
│  • AWS EC2 VMs:       {sensor['ec2_vms']['installed']:>6} installed, {sensor['ec2_vms']['not_installed']:>6} not installed
│  • AWS EKS Nodes:     {sensor['ec2_eks']['installed']:>6} installed, {sensor['ec2_eks']['not_installed']:>6} not installed
│  • GCP VMs:           {sensor['gcp_vms']['installed']:>6} installed, {sensor['gcp_vms']['not_installed']:>6} not installed
│  • GCP GKE Nodes:     {sensor['gcp_gke']['installed']:>6} installed, {sensor['gcp_gke']['not_installed']:>6} not installed
│  • Azure VMs:         {sensor['azure_vms']['installed']:>6} installed, {sensor['azure_vms']['not_installed']:>6} not installed
│  • Azure AKS Nodes:   {sensor['azure_aks']['installed']:>6} installed, {sensor['azure_aks']['not_installed']:>6} not installed
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
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
                "vms_with_sensor": total_vms_installed,
                "vms_without_sensor": total_vms_not_installed,
                "nodes_with_sensor": total_nodes_installed,
                "nodes_without_sensor": total_nodes_not_installed,
                "total_with_sensor": total_all_installed,
                "total_without_sensor": total_all_not_installed
            }
        }
        json_file = output_file.replace(".txt", ".json")
        with open(json_file, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"\n📁 Report saved:")
        print(f"   • {output_file}")
        print(f"   • {json_file}")

    return report


def export_assets_csv(cs: CloudSecurityAssets, output_file: str, unmanaged_only: bool = False) -> None:
    """Export all cloud assets to CSV with sensor and K8s node information."""
    filter_label = "unmanaged " if unmanaged_only else ""
    print(f"📊 Exporting {filter_label}assets to CSV: {output_file}")

    csv_file = output_file.replace(".txt", ".csv") if output_file.endswith(".txt") else output_file + ".csv"

    def process_assets_batch(assets, cloud_type, is_k8s=False, k8s_type=None):
        """Process a batch of assets and return list of rows."""
        rows = []
        for asset in assets:
            managed_by = asset.get('cloud_context', {}).get('host', {}).get('managed_by', 'Unmanaged')

            if unmanaged_only and managed_by == "Sensor":
                continue

            name = asset.get('resource_name', 'N/A')
            asset_id = asset.get('resource_id', 'N/A')
            region = asset.get('region', 'N/A')

            if is_k8s:
                is_node = "Yes"
            else:
                is_node = "No"

            rows.append({
                'asset_name': name,
                'asset_id': asset_id,
                'asset_type': cloud_type,
                'region': region,
                'managed_by': managed_by,
                'is_kubernetes_node': is_node
            })
        return rows

    def query_cloud_type(filter_str, cloud_type, is_k8s=False, k8s_type=None):
        """Query and process a cloud type with pagination."""
        all_rows = []
        offset = 0
        while True:
            result = cs.query_assets(filter=filter_str, limit=100, offset=offset)
            if result.get("status_code") != 200:
                break
            resource_ids = result.get("body", {}).get("resources", [])
            if not resource_ids:
                break

            details = cs.cloud_security_assets_entities_get(ids=resource_ids)
            if details.get("status_code") == 200:
                assets = details.get("body", {}).get("resources", [])
                rows = process_assets_batch(assets, cloud_type, is_k8s, k8s_type)
                all_rows.extend(rows)

            total = result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            offset += 100
            if offset >= total:
                break

        return all_rows

    def query_ec2_vms_and_eks():
        """Query EC2 and separate VMs from EKS."""
        all_rows = []
        ec2_filter = 'service:"EC2"+instance_state:"running"'
        offset = 0
        while True:
            result = cs.query_assets(filter=ec2_filter, limit=100, offset=offset)
            if result.get("status_code") != 200:
                break
            resource_ids = result.get("body", {}).get("resources", [])
            if not resource_ids:
                break

            details = cs.cloud_security_assets_entities_get(ids=resource_ids)
            if details.get("status_code") == 200:
                assets = details.get("body", {}).get("resources", [])
                for asset in assets:
                    managed_by = asset.get('cloud_context', {}).get('host', {}).get('managed_by', 'Unmanaged')

                    if unmanaged_only and managed_by == "Sensor":
                        continue

                    name = asset.get('resource_name', 'N/A')
                    asset_id = asset.get('resource_id', 'N/A')
                    region = asset.get('region', 'N/A')

                    is_eks = 'aws:eks:cluster-name' in asset.get('cloud_context', {}).get('tags', {})
                    is_node = "Yes" if is_eks else "No"

                    all_rows.append({
                        'asset_name': name,
                        'asset_id': asset_id,
                        'asset_type': 'AWS EC2',
                        'region': region,
                        'managed_by': managed_by,
                        'is_kubernetes_node': is_node
                    })

            total = result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            offset += 100
            if offset >= total:
                break

        return all_rows

    def query_gcp_vms_and_gke():
        """Query GCP and separate VMs from GKE."""
        all_rows = []
        gcp_filter = 'resource_type_name:"Compute Instance"+instance_state:"RUNNING"'
        offset = 0
        while True:
            result = cs.query_assets(filter=gcp_filter, limit=100, offset=offset)
            if result.get("status_code") != 200:
                break
            resource_ids = result.get("body", {}).get("resources", [])
            if not resource_ids:
                break

            details = cs.cloud_security_assets_entities_get(ids=resource_ids)
            if details.get("status_code") == 200:
                assets = details.get("body", {}).get("resources", [])
                for asset in assets:
                    managed_by = asset.get('cloud_context', {}).get('host', {}).get('managed_by', 'Unmanaged')

                    if unmanaged_only and managed_by == "Sensor":
                        continue

                    name = asset.get('resource_name', 'N/A')
                    asset_id = asset.get('resource_id', 'N/A')
                    region = asset.get('region', 'N/A')

                    is_gke = 'goog-k8s-cluster-name' in asset.get('cloud_context', {}).get('tags', {})
                    is_node = "Yes" if is_gke else "No"

                    all_rows.append({
                        'asset_name': name,
                        'asset_id': asset_id,
                        'asset_type': 'GCP Compute',
                        'region': region,
                        'managed_by': managed_by,
                        'is_kubernetes_node': is_node
                    })

            total = result.get("body", {}).get("meta", {}).get("pagination", {}).get("total", 0)
            offset += 100
            if offset >= total:
                break

        return all_rows

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            ec2_future = executor.submit(query_ec2_vms_and_eks)
            gcp_future = executor.submit(query_gcp_vms_and_gke)
            azure_future = executor.submit(query_cloud_type, 'service:"Virtual Machines"+instance_state:"VM running"', 'Azure VM', False)

            all_rows = []
            all_rows.extend(ec2_future.result())
            all_rows.extend(gcp_future.result())
            all_rows.extend(azure_future.result())

            # Query AKS nodes
            aks_rows = query_cloud_type(
                'resource_type_name:"Virtual Machine Scale Sets Virtual Machines"+tag_key:"aks-managed-orchestrator"',
                'Azure AKS Node',
                is_k8s=True,
                k8s_type='AKS'
            )
            all_rows.extend(aks_rows)

        # Write to CSV
        if all_rows:
            with open(csv_file, 'w', newline='') as f:
                fieldnames = ['asset_name', 'asset_id', 'asset_type', 'region', 'managed_by', 'is_kubernetes_node']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
            print(f"✓ CSV saved: {csv_file} ({len(all_rows)} assets)")
        else:
            print("⚠ No assets found to export")

    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        sys.exit(1)


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
    parser.add_argument("-e", "--export-csv", action="store_true", help="Export all assets to CSV")
    parser.add_argument("--unmanaged-only", action="store_true", help="Export only unmanaged assets (with -e)")
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

    if args.export_csv:
        export_assets_csv(cs, args.output or "assets_export.txt", args.unmanaged_only)


if __name__ == "__main__":
    main()
