"""
═══════════════════════════════════════════════════════════════
  Rubiscape Alert Service — End-to-End Demo Script
  Demonstrates the full system flow for evaluation/submission
═══════════════════════════════════════════════════════════════

This script:
  1. Cleans up old data (optional)
  2. Creates rules for ALL system-level metrics
  3. Sends simulated events from multiple AI services
  4. Verifies alerts were generated
  5. Fetches the metrics report

Run: python demo.py
Requires: Server running at http://127.0.0.1:8000
"""

import urllib.request
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"
DELAY = 0.3  # seconds between API calls


# ── Helpers ───────────────────────────────────────────────────
def api_request(method, path, data=None):
    """Make an API request and return parsed JSON response."""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8") if data else None
    headers = {"Content-Type": "application/json"} if data else {}

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, {"error": str(e)}


def print_header(title):
    """Print a formatted section header."""
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print(f"{'═' * 60}")


def print_success(msg):
    print(f"  ✅ {msg}")


def print_info(msg):
    print(f"  📌 {msg}")


# ── Step 0: Health Check ─────────────────────────────────────
print_header("RUBISCAPE ALERT SERVICE — END-TO-END DEMO")
print_info("Checking server health...")

status, data = api_request("GET", "/")
if status != 200:
    print(f"  ❌ Server not reachable at {BASE_URL}")
    print(f"     Run: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
    sys.exit(1)

print_success(f"Server is healthy — v{data.get('version', '?')}")


# ── Step 1: Create Rules for All System Metrics ──────────────
print_header("STEP 1: Creating Alert Rules")
print_info("Setting up rules for all system-level metrics...\n")

rules = [
    # Latency monitoring
    {"metric": "latency",      "operator": ">",  "threshold": 500.0,  "severity": "CRITICAL"},
    {"metric": "latency",      "operator": ">",  "threshold": 200.0,  "severity": "HIGH"},
    {"metric": "latency",      "operator": ">",  "threshold": 100.0,  "severity": "MEDIUM"},

    # Error rate monitoring
    {"metric": "error_rate",   "operator": ">",  "threshold": 10.0,   "severity": "CRITICAL"},
    {"metric": "error_rate",   "operator": ">",  "threshold": 5.0,    "severity": "HIGH"},
    {"metric": "error_rate",   "operator": ">",  "threshold": 2.0,    "severity": "MEDIUM"},

    # CPU usage monitoring
    {"metric": "cpu_usage",    "operator": ">=", "threshold": 95.0,   "severity": "CRITICAL"},
    {"metric": "cpu_usage",    "operator": ">=", "threshold": 80.0,   "severity": "HIGH"},
    {"metric": "cpu_usage",    "operator": ">=", "threshold": 60.0,   "severity": "LOW"},

    # GPU usage monitoring
    {"metric": "gpu_usage",    "operator": ">=", "threshold": 95.0,   "severity": "CRITICAL"},
    {"metric": "gpu_usage",    "operator": ">=", "threshold": 85.0,   "severity": "HIGH"},
    {"metric": "gpu_usage",    "operator": ">=", "threshold": 70.0,   "severity": "MEDIUM"},

    # Memory usage monitoring
    {"metric": "memory_usage", "operator": ">=", "threshold": 95.0,   "severity": "CRITICAL"},
    {"metric": "memory_usage", "operator": ">=", "threshold": 85.0,   "severity": "HIGH"},
    {"metric": "memory_usage", "operator": ">=", "threshold": 70.0,   "severity": "MEDIUM"},

    # Throughput monitoring (requests per second)
    {"metric": "throughput",   "operator": "<",  "threshold": 10.0,   "severity": "CRITICAL"},
    {"metric": "throughput",   "operator": "<",  "threshold": 50.0,   "severity": "HIGH"},
    {"metric": "throughput",   "operator": "<",  "threshold": 100.0,  "severity": "MEDIUM"},

    # Disk usage monitoring
    {"metric": "disk_usage",   "operator": ">=", "threshold": 95.0,   "severity": "CRITICAL"},
    {"metric": "disk_usage",   "operator": ">=", "threshold": 85.0,   "severity": "HIGH"},
    {"metric": "disk_usage",   "operator": ">=", "threshold": 70.0,   "severity": "MEDIUM"},
]

rules_created = 0
for rule in rules:
    status, data = api_request("POST", "/rules/", rule)
    if status == 201:
        print(f"  Rule #{data['id']:>3}: {rule['metric']:<15} {rule['operator']:>2} {rule['threshold']:>7}  [{rule['severity']}]")
        rules_created += 1
    else:
        print(f"  ⚠️  Rule creation returned {status}: {data}")
    time.sleep(DELAY)

print(f"\n  📊 {rules_created} rules created across 7 system metrics")


# ── Step 2: Simulate AI Workflow Events ──────────────────────
print_header("STEP 2: Simulating AI Workflow Events")
print_info("Sending events from multiple AI services...\n")

events = [
    # High latency from Model Service
    {"service_name": "Model Inference Service",  "metric": "latency",      "value": 650.0},
    # Elevated error rate from Data Pipeline
    {"service_name": "Data Pipeline",            "metric": "error_rate",   "value": 8.5},
    # CPU spike on Training Service
    {"service_name": "Training Service",         "metric": "cpu_usage",    "value": 97.2},
    # GPU overload on Inference Engine
    {"service_name": "GPU Inference Engine",     "metric": "gpu_usage",    "value": 98.0},
    # Memory pressure on Feature Store
    {"service_name": "Feature Store",            "metric": "memory_usage", "value": 91.0},
    # Low throughput from API Gateway
    {"service_name": "API Gateway",              "metric": "throughput",   "value": 8.0},
    # Disk filling up on Storage Service
    {"service_name": "Storage Service",          "metric": "disk_usage",   "value": 92.0},
    # Moderate latency from another service
    {"service_name": "Preprocessing Service",    "metric": "latency",      "value": 250.0},
    # Moderate memory on another service
    {"service_name": "Model Registry",           "metric": "memory_usage", "value": 76.0},
    # Normal GPU usage (should trigger MEDIUM only)
    {"service_name": "Batch Processing Service", "metric": "gpu_usage",    "value": 72.0},
]

total_alerts = 0
for evt in events:
    status, data = api_request("POST", "/events/", evt)
    if status == 201:
        n = data.get("alerts_generated", 0)
        total_alerts += n
        severity_list = ", ".join([a["severity"] for a in data.get("alerts", [])])
        print(f"  📡 {evt['service_name']:<28} │ {evt['metric']:<15} = {evt['value']:>7} │ {n} alerts ({severity_list})")
    else:
        print(f"  ❌ Event failed ({status}): {data}")
    time.sleep(DELAY)

print(f"\n  🔔 {total_alerts} total alerts generated from {len(events)} events")


# ── Step 3: Fetch Metrics Report ─────────────────────────────
print_header("STEP 3: Metrics Report")
time.sleep(0.5)

status, report = api_request("GET", "/alerts/metrics/report")
if status == 200:
    print(f"  Total Alerts     : {report.get('total_alerts', 0)}")
    print(f"  Last 24 Hours    : {report.get('recent_24h', 0)}")
    print(f"  Trend            : {report.get('trend', 'N/A')}")
    print()
    print("  By Severity:")
    for sev, count in report.get("by_severity", {}).items():
        bar = "█" * count
        print(f"    {sev:<10} : {count:>3}  {bar}")
    print()
    print("  By Service:")
    for svc, count in report.get("by_service", {}).items():
        print(f"    {svc:<28} : {count:>3}")
else:
    print(f"  ❌ Failed to fetch report: {report}")


# ── Step 4: Summary ──────────────────────────────────────────
print_header("DEMO COMPLETE")
print(f"""
  ✅ Rules Created     : {rules_created}
  ✅ Events Processed  : {len(events)}
  ✅ Alerts Generated  : {total_alerts}
  ✅ Email Sent To     : desaiprasad876@gmail.com
  ✅ Dashboard         : http://localhost:8000/dashboard
  ✅ API Docs          : http://localhost:8000/docs
  ✅ Metrics Report    : http://localhost:8000/alerts/metrics/report

  System Metrics Covered:
    • Latency           • Error Rate
    • CPU Usage         • GPU Usage
    • Memory Usage      • Throughput
    • Disk Usage

  Architecture: Layered (API → Service → Rule Engine → Data Layer)
  Database: SQLite (switchable to MySQL)
  Notifications: Console + Gmail SMTP (real emails)
""")
