#!/usr/bin/env python3
"""
Intake Agent integration test.

Requires both the ERP Service and Intake Agent to be running.
Start them first:

    bash run_dev.sh          # from the backend/ directory

Then in another terminal:

    python test_intake.py    # from the backend/ directory
"""
import json
import sys

import httpx

INTAKE_URL = "http://localhost:8002"
ERP_URL = "http://localhost:8001"

# ── Test scenarios ─────────────────────────────────────────────────────────────
# These mirror the three demonstration scenarios from the project concept.

SCENARIOS = [
    {
        "label": "Scenario 1 — Standard delivery, Central London (Clean Convergence candidate)",
        "payload": {
            "order_id": "TEST-001",
            "destination_lat": 51.5155,
            "destination_lon": -0.0922,
            "order_value": 1200.00,
            "weight_kg": 35.0,
            "time_window_hours": 4.0,
            "cargo_type": "general",
            "priority": "standard",
            "scenario": "convergence",
        },
    },
    {
        "label": "Scenario 2 — Urgent fragile goods, East London (Qualification candidate)",
        "payload": {
            "order_id": "TEST-002",
            "destination_lat": 51.5150,
            "destination_lon": 0.0350,
            "order_value": 4800.00,
            "weight_kg": 22.0,
            "time_window_hours": 2.0,
            "cargo_type": "fragile",
            "priority": "urgent",
            "scenario": "qualification",
        },
    },
    {
        "label": "Scenario 3 — Standard delivery, Outer East / Romford (Override / Fairness candidate)",
        "payload": {
            "order_id": "TEST-003",
            "destination_lat": 51.5640,
            "destination_lon": 0.1960,
            "order_value": 650.00,
            "weight_kg": 60.0,
            "time_window_hours": 6.0,
            "cargo_type": "general",
            "priority": "standard",
            "scenario": "override",
        },
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def check_service(url: str, name: str) -> bool:
    try:
        r = httpx.get(f"{url}/health", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


def bar(value: float, width: int = 20) -> str:
    """Render a simple ASCII progress bar for a 0–1 value."""
    filled = round(value * width)
    return "[" + "█" * filled + "░" * (width - filled) + f"] {value*100:.0f}%"


def print_feature_vector(fv: dict) -> None:
    zp = fv["zone_profile"]

    print(f"\n  ┌─ DESTINATION ───────────────────────────────────────────┐")
    print(f"  │  Zone   : {zp['zone_id']:<12}  {zp['name']}")
    print(f"  │  Success rate  {bar(zp['delivery_success_rate'])}")
    print(f"  │  Demand        {bar(zp['demand_pressure'])}")
    print(f"  │  Complaint rate: {zp['complaint_rate']*100:.0f}%   "
          f"Avg transit: {zp['avg_transit_hours']:.1f}h   "
          f"Active routes: {zp['active_routes']}")
    print(f"  │  30-day: {zp['last_30_days_total']} deliveries, "
          f"{zp['last_30_days_successful']} successful")
    print(f"  └─────────────────────────────────────────────────────────┘")

    wh_with_stock = [w for w in fv["warehouse_options"] if w["stock_confirmed"]]
    print(f"\n  WAREHOUSE OPTIONS  ({len(wh_with_stock)} with stock / {len(fv['warehouse_options'])} total)")
    print(f"  {'ID':<8} {'Name':<30} {'Dist (km)':>9}  {'Stock':>6}  Status")
    print(f"  {'─'*8} {'─'*30} {'─'*9}  {'─'*6}  {'─'*14}")
    for wh in fv["warehouse_options"]:
        status = f"stock={wh['stock_level']}" if wh["stock_confirmed"] else "OUT OF STOCK"
        flag = " ◄" if wh["stock_confirmed"] and wh == fv["warehouse_options"][0] else ""
        print(f"  {wh['warehouse_id']:<8} {wh['name']:<30} "
              f"{wh['distance_to_destination_km']:>8.1f}  {wh['stock_level']:>6}  {status}{flag}")

    print(f"\n  AVAILABLE DRIVERS  ({len(fv['available_drivers'])} matched for this cargo/weight)")
    print(f"  {'ID':<9} {'Name':<15} {'Type':<10} {'ETA (min)':>9}  "
          f"{'Cap (kg)':>8}  {'Load':>4}  {'Rating':>6}  Familiar zones")
    print(f"  {'─'*9} {'─'*15} {'─'*10} {'─'*9}  {'─'*8}  {'─'*4}  {'─'*6}  {'─'*20}")
    for drv in fv["available_drivers"]:
        zones = ", ".join(drv["zone_familiarity"][:3])
        flag = " ◄" if drv == fv["available_drivers"][0] else ""
        print(f"  {drv['driver_id']:<9} {drv['name']:<15} {drv['vehicle_type']:<10} "
              f"{drv['estimated_pickup_minutes']:>8.0f}  "
              f"{drv['available_capacity_kg']:>8.0f}  "
              f"{drv['active_deliveries']:>4}  "
              f"★{drv['rating']:.1f}    {zones}{flag}")

    print(f"\n  ERP latency: {fv['erp_latency_ms']:.0f} ms   "
          f"Enriched at: {fv['enrichment_timestamp']}")


def run_scenario(scenario: dict) -> None:
    label = scenario["label"]
    payload = scenario["payload"]
    sep = "═" * 72

    print(f"\n{sep}")
    print(f"  {label}")
    print(sep)
    print(f"  order_id  : {payload['order_id']}")
    print(f"  cargo     : {payload['cargo_type']}   weight: {payload['weight_kg']} kg   "
          f"value: £{payload['order_value']:,.0f}")
    print(f"  priority  : {payload['priority']}   time window: {payload['time_window_hours']} h")
    print(f"  dest      : ({payload['destination_lat']}, {payload['destination_lon']})")

    try:
        resp = httpx.post(f"{INTAKE_URL}/enrich", json=payload, timeout=15.0)
        resp.raise_for_status()
        body = resp.json()
        fv = body["feature_vector"]
    except httpx.HTTPStatusError as exc:
        print(f"\n  HTTP ERROR {exc.response.status_code}: {exc.response.text}")
        return
    except Exception as exc:
        print(f"\n  REQUEST FAILED: {exc}")
        return

    print_feature_vector(fv)

    # Dump full JSON for inspection
    print(f"\n  ── Full feature_vector JSON ──────────────────────────────────────")
    print(json.dumps(fv, indent=4))


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          Intake Agent — Feature Vector Integration Test              ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    ok_erp = check_service(ERP_URL, "ERP Service")
    ok_intake = check_service(INTAKE_URL, "Intake Agent")

    print(f"\n  ERP Service  ({ERP_URL})   {'✓ OK' if ok_erp else '✗ NOT REACHABLE'}")
    print(f"  Intake Agent ({INTAKE_URL})   {'✓ OK' if ok_intake else '✗ NOT REACHABLE'}")

    if not ok_erp or not ok_intake:
        print("\n  One or more services are not running.")
        print("  Start them with:  bash run_dev.sh   (from the backend/ directory)")
        sys.exit(1)

    for scenario in SCENARIOS:
        run_scenario(scenario)

    print(f"\n{'═'*72}")
    print("  All scenarios complete.")


if __name__ == "__main__":
    main()
