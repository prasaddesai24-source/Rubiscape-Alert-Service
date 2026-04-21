"""Seed script to add diverse rules and trigger test events."""
import urllib.request
import json
import time

BASE = "http://127.0.0.1:8000"

def api_post(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

def api_delete(path):
    req = urllib.request.Request(f"{BASE}{path}", method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
    except Exception:
        pass

# ── Cleanup duplicate rules ──────────────────────────
print("Cleaning duplicate rules...")
for i in range(2, 20):
    api_delete(f"/rules/{i}")

# ── Create diverse rules ─────────────────────────────
rules = [
    {"metric": "error_rate",    "operator": ">",  "threshold": 5.0,   "severity": "CRITICAL"},
    {"metric": "error_rate",    "operator": ">",  "threshold": 2.0,   "severity": "HIGH"},
    {"metric": "memory_usage",  "operator": ">=", "threshold": 90.0,  "severity": "CRITICAL"},
    {"metric": "memory_usage",  "operator": ">=", "threshold": 75.0,  "severity": "MEDIUM"},
    {"metric": "cpu_usage",     "operator": ">",  "threshold": 85.0,  "severity": "HIGH"},
    {"metric": "cpu_usage",     "operator": ">",  "threshold": 60.0,  "severity": "LOW"},
    {"metric": "response_time", "operator": ">",  "threshold": 500.0, "severity": "CRITICAL"},
    {"metric": "response_time", "operator": ">",  "threshold": 200.0, "severity": "MEDIUM"},
    {"metric": "request_count", "operator": ">=", "threshold": 10000, "severity": "LOW"},
]

print("\nCreating rules:")
for r in rules:
    result = api_post("/rules/", r)
    print(f"  Rule #{result['id']}: {r['metric']} {r['operator']} {r['threshold']} [{r['severity']}]")
    time.sleep(0.2)

# ── Send events to trigger alerts ────────────────────
events = [
    {"service_name": "Model Service",     "metric": "error_rate",    "value": 7.5},
    {"service_name": "Data Pipeline",     "metric": "memory_usage",  "value": 92.3},
    {"service_name": "Inference Engine",   "metric": "cpu_usage",     "value": 88.0},
    {"service_name": "API Gateway",       "metric": "response_time", "value": 750.0},
    {"service_name": "Feature Store",     "metric": "memory_usage",  "value": 78.5},
    {"service_name": "Training Service",  "metric": "request_count", "value": 15000},
    {"service_name": "Model Service",     "metric": "cpu_usage",     "value": 65.0},
    {"service_name": "Data Pipeline",     "metric": "response_time", "value": 350.0},
]

print("\nSending events:")
for evt in events:
    result = api_post("/events/", evt)
    print(f"  {evt['service_name']} | {evt['metric']}={evt['value']} -> {result['alerts_generated']} alerts")
    time.sleep(0.3)

print("\nDone! Refresh http://localhost:8000/dashboard to see results.")
