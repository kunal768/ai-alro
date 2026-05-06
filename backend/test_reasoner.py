#!/usr/bin/env python3
"""
Reasoner Agent + Resolution Layer integration test.

Runs three pre-seeded scenarios designed to trigger the three resolution states:
  Scenario A — Convergence   (clear winner, both agents agree)
  Scenario B — Qualification (tight time window + borderline ranking)
  Scenario C — Override      (fairness / redlining-by-proxy concern)

Requires:
  - Reasoner Agent running on :8004  (bash run_dev.sh from backend/)
  - A real LLM provider configured in .env  OR  LLM_PROVIDER=ollama

Usage:
  cd backend
  bash run_dev.sh          # terminal 1 — starts Reasoner Agent
  python test_reasoner.py  # terminal 2
"""
import asyncio
import json
import sys
import time

import httpx

REASONER_URL = "http://localhost:8004"


# ── Scenario payloads ──────────────────────────────────────────────────────────
# Each payload mirrors a realistic state the system must handle.
# Feature vectors and optimizer outputs are pre-seeded; in production these
# are produced by the Intake Agent and Optimizer Agent respectively.

# Shared driver/warehouse sub-objects reused across scenarios
_DRIVERS = {
    "DRV-001": {
        "driver_id": "DRV-001", "name": "Marcus Johnson", "vehicle_type": "van",
        "current_lat": 37.7920, "current_lon": -122.3985,
        "distance_to_nearest_wh_km": 3.2, "estimated_pickup_minutes": 20.0,
        "current_load_kg": 75.0, "max_load_kg": 500.0, "available_capacity_kg": 425.0,
        "active_deliveries": 2, "rating": 4.8,
        "zone_familiarity": ["central_sf", "soma_mission", "east_bay"],
    },
    "DRV-004": {
        "driver_id": "DRV-004", "name": "Mei Chen", "vehicle_type": "motorbike",
        "current_lat": 37.7855, "current_lon": -122.4000,
        "distance_to_nearest_wh_km": 1.8, "estimated_pickup_minutes": 14.0,
        "current_load_kg": 8.0, "max_load_kg": 50.0, "available_capacity_kg": 42.0,
        "active_deliveries": 1, "rating": 4.7,
        "zone_familiarity": ["central_sf", "soma_mission"],
    },
    "DRV-005": {
        "driver_id": "DRV-005", "name": "Jordan Williams", "vehicle_type": "van",
        "current_lat": 37.9740, "current_lon": -122.5315,
        "distance_to_nearest_wh_km": 5.2, "estimated_pickup_minutes": 26.0,
        "current_load_kg": 0.0, "max_load_kg": 800.0, "available_capacity_kg": 800.0,
        "active_deliveries": 0, "rating": 4.5,
        "zone_familiarity": ["north_bay", "central_sf"],
    },
    "DRV-007": {
        "driver_id": "DRV-007", "name": "Diego Morales", "vehicle_type": "van",
        "current_lat": 37.6688, "current_lon": -122.0808,
        "distance_to_nearest_wh_km": 2.5, "estimated_pickup_minutes": 15.0,
        "current_load_kg": 140.0, "max_load_kg": 500.0, "available_capacity_kg": 360.0,
        "active_deliveries": 2, "rating": 4.4,
        "zone_familiarity": ["south_bay", "outer_east"],
    },
    "DRV-009": {
        "driver_id": "DRV-009", "name": "Amara Okonkwo", "vehicle_type": "van",
        "current_lat": 37.8305, "current_lon": -122.2441,
        "distance_to_nearest_wh_km": 3.8, "estimated_pickup_minutes": 17.0,
        "current_load_kg": 290.0, "max_load_kg": 600.0, "available_capacity_kg": 310.0,
        "active_deliveries": 4, "rating": 4.3,
        "zone_familiarity": ["east_bay", "north_bay", "outer_east"],
    },
}

_WAREHOUSES = {
    "WH-SF01": {
        "warehouse_id": "WH-SF01", "name": "SF Mission District Fulfillment Center",
        "lat": 37.7599, "lon": -122.4148, "stock_level": 820, "stock_confirmed": True,
        # distance set per scenario below
    },
    "WH-OAK01": {
        "warehouse_id": "WH-OAK01", "name": "Oakland Harbor Distribution Hub",
        "lat": 37.8044, "lon": -122.2712, "stock_level": 640, "stock_confirmed": True,
    },
    "WH-SSF01": {
        "warehouse_id": "WH-SSF01", "name": "South San Francisco Peninsula Hub",
        "lat": 37.6527, "lon": -122.4477, "stock_level": 710, "stock_confirmed": True,
    },
}


def _wh(wh_id: str, dist: float) -> dict:
    return {**_WAREHOUSES[wh_id], "distance_to_destination_km": dist}


# ── Scenario A — SF Financial District, standard delivery (expected: CONVERGENCE) ─
SCENARIO_A = {
    "label": "Scenario A — SF Financial District, standard delivery  [expected: CONVERGENCE]",
    "payload": {
        "feature_vector": {
            "order_id": "TEST-A001",
            "destination_lat": 37.7910, "destination_lon": -122.3990,
            "destination_zone_id": "central_sf",
            "order_value": 1200.0, "weight_kg": 32.0,
            "time_window_hours": 4.0,
            "cargo_type": "general", "priority": "standard",
            "warehouse_options": [
                _wh("WH-SF01", 4.2), _wh("WH-OAK01", 14.8), _wh("WH-SSF01", 8.1),
            ],
            "available_drivers": [
                _DRIVERS["DRV-001"], _DRIVERS["DRV-007"], _DRIVERS["DRV-005"],
            ],
            "zone_profile": {
                "zone_id": "central_sf", "name": "SF Financial District / Union Square",
                "delivery_success_rate": 0.96, "avg_transit_hours": 1.2,
                "demand_pressure": 0.91, "active_routes": 38,
                "complaint_rate": 0.03,
                "last_30_days_total": 2104, "last_30_days_successful": 2020,
            },
            "enrichment_timestamp": "2026-05-05T09:00:00Z",
            "erp_latency_ms": 15.2,
        },
        "optimizer_output": {
            "order_id": "TEST-A001",
            "weights_used": {
                "w1_timeliness": 0.30, "w2_cost_efficiency": 0.25,
                "w3_proximity": 0.45,
            },
            "ranked_options": [
                {   # Clear winner — large gap to rank 2, driver knows central_sf
                    "option_id": "WH-SF01::DRV-001",
                    "warehouse_id": "WH-SF01", "driver_id": "DRV-001",
                    "timeliness_score": 0.93, "cost_efficiency_score": 0.82,
                    "proximity_score": 0.92, "zone_risk_penalty": 0.018,
                    "composite_score": 0.879,
                    "estimated_cost_gbp": 42.80, "estimated_duration_hours": 1.72,
                },
                {
                    "option_id": "WH-SSF01::DRV-007",
                    "warehouse_id": "WH-SSF01", "driver_id": "DRV-007",
                    "timeliness_score": 0.86, "cost_efficiency_score": 0.74,
                    "proximity_score": 0.78, "zone_risk_penalty": 0.018,
                    "composite_score": 0.785,
                    "estimated_cost_gbp": 54.20, "estimated_duration_hours": 1.95,
                },
                {
                    "option_id": "WH-OAK01::DRV-005",
                    "warehouse_id": "WH-OAK01", "driver_id": "DRV-005",
                    "timeliness_score": 0.80, "cost_efficiency_score": 0.64,
                    "proximity_score": 0.61, "zone_risk_penalty": 0.018,
                    "composite_score": 0.680,
                    "estimated_cost_gbp": 68.50, "estimated_duration_hours": 2.14,
                },
            ],
            "top_choice": {
                "option_id": "WH-SF01::DRV-001",
                "warehouse_id": "WH-SF01", "driver_id": "DRV-001",
                "timeliness_score": 0.93, "cost_efficiency_score": 0.82,
                "proximity_score": 0.92, "zone_risk_penalty": 0.018,
                "composite_score": 0.879,
                "estimated_cost_gbp": 42.80, "estimated_duration_hours": 1.72,
            },
        },
    },
}

# ── Scenario B — East Bay, urgent fragile (expected: QUALIFICATION) ────────────
# Key stresses: composite gap = 0.031 (borderline); estimated_duration = 1.95h
# approx equals the time window; Rank 2 is a motorbike carrying fragile cargo.
SCENARIO_B = {
    "label": "Scenario B — Oakland / East Bay, urgent fragile goods  [expected: QUALIFICATION]",
    "payload": {
        "feature_vector": {
            "order_id": "TEST-B002",
            "destination_lat": 37.8100, "destination_lon": -122.2650,
            "destination_zone_id": "east_bay",
            "order_value": 5200.0, "weight_kg": 20.0,
            "time_window_hours": 2.0,
            "cargo_type": "fragile", "priority": "urgent",
            "warehouse_options": [
                _wh("WH-OAK01", 3.5), _wh("WH-SF01", 13.2),
            ],
            "available_drivers": [
                _DRIVERS["DRV-009"], _DRIVERS["DRV-004"], _DRIVERS["DRV-001"],
            ],
            "zone_profile": {
                "zone_id": "east_bay", "name": "East Bay (Oakland / Berkeley)",
                "delivery_success_rate": 0.91, "avg_transit_hours": 1.7,
                "demand_pressure": 0.75, "active_routes": 24,
                "complaint_rate": 0.07,
                "last_30_days_total": 1380, "last_30_days_successful": 1256,
            },
            "enrichment_timestamp": "2026-05-05T09:00:00Z",
            "erp_latency_ms": 8.7,
        },
        "optimizer_output": {
            "order_id": "TEST-B002",
            "weights_used": {
                "w1_timeliness": 0.35, "w2_cost_efficiency": 0.20,
                "w3_proximity": 0.45,
            },
            "ranked_options": [
                {   # Wins on proximity; but duration = 1.95h near window edge
                    "option_id": "WH-OAK01::DRV-009",
                    "warehouse_id": "WH-OAK01", "driver_id": "DRV-009",
                    "timeliness_score": 0.88, "cost_efficiency_score": 0.75,
                    "proximity_score": 0.95, "zone_risk_penalty": 0.040,
                    "composite_score": 0.820,
                    "estimated_cost_gbp": 32.10, "estimated_duration_hours": 1.95,
                },
                {   # Gap = 0.031 — borderline. Motorbike + fragile = risk.
                    "option_id": "WH-OAK01::DRV-004",
                    "warehouse_id": "WH-OAK01", "driver_id": "DRV-004",
                    "timeliness_score": 0.94, "cost_efficiency_score": 0.70,
                    "proximity_score": 0.95, "zone_risk_penalty": 0.040,
                    "composite_score": 0.789,
                    "estimated_cost_gbp": 29.40, "estimated_duration_hours": 1.88,
                },
                {
                    "option_id": "WH-SF01::DRV-001",
                    "warehouse_id": "WH-SF01", "driver_id": "DRV-001",
                    "timeliness_score": 0.85, "cost_efficiency_score": 0.63,
                    "proximity_score": 0.68, "zone_risk_penalty": 0.040,
                    "composite_score": 0.721,
                    "estimated_cost_gbp": 48.90, "estimated_duration_hours": 2.08,
                },
            ],
            "top_choice": {
                "option_id": "WH-OAK01::DRV-009",
                "warehouse_id": "WH-OAK01", "driver_id": "DRV-009",
                "timeliness_score": 0.88, "cost_efficiency_score": 0.75,
                "proximity_score": 0.95, "zone_risk_penalty": 0.040,
                "composite_score": 0.820,
                "estimated_cost_gbp": 32.10, "estimated_duration_hours": 1.95,
            },
        },
    },
}

# ── Scenario C — Hayward / Outer East, standard delivery (expected: OVERRIDE) ───
# Key stresses: zone 83% success / 14% complaint (redlining-by-proxy concern);
# composite gap = 0.022 (very borderline); Rank 1 driver has NO outer_east
# familiarity; Rank 2 driver knows outer_east.
SCENARIO_C = {
    "label": "Scenario C — Hayward / Outer East, standard delivery  [expected: OVERRIDE / fairness]",
    "payload": {
        "feature_vector": {
            "order_id": "TEST-C003",
            "destination_lat": 37.6688, "destination_lon": -122.0808,
            "destination_zone_id": "outer_east",
            "order_value": 680.0, "weight_kg": 55.0,
            "time_window_hours": 6.0,
            "cargo_type": "general", "priority": "standard",
            "warehouse_options": [
                _wh("WH-OAK01", 12.6), _wh("WH-SF01", 22.1),
            ],
            "available_drivers": [
                {**_DRIVERS["DRV-001"], "estimated_pickup_minutes": 22.0},
                {**_DRIVERS["DRV-009"], "estimated_pickup_minutes": 20.0},
                {**_DRIVERS["DRV-007"], "estimated_pickup_minutes": 16.0},
            ],
            "zone_profile": {
                "zone_id": "outer_east", "name": "Outer East (Hayward / Fremont)",
                "delivery_success_rate": 0.83, "avg_transit_hours": 2.8,
                "demand_pressure": 0.44, "active_routes": 11,
                "complaint_rate": 0.14,
                "last_30_days_total": 590, "last_30_days_successful": 490,
            },
            "enrichment_timestamp": "2026-05-05T09:00:00Z",
            "erp_latency_ms": 6.8,
        },
        "optimizer_output": {
            "order_id": "TEST-C003",
            "weights_used": {
                "w1_timeliness": 0.30, "w2_cost_efficiency": 0.25,
                "w3_proximity": 0.45,
            },
            "ranked_options": [
                {   # Wins on cost; driver UNFAMILIAR with outer_east
                    "option_id": "WH-OAK01::DRV-001",
                    "warehouse_id": "WH-OAK01", "driver_id": "DRV-001",
                    "timeliness_score": 0.95, "cost_efficiency_score": 0.83,
                    "proximity_score": 0.62, "zone_risk_penalty": 0.087,
                    "composite_score": 0.718,
                    "estimated_cost_gbp": 78.40, "estimated_duration_hours": 3.18,
                },
                {   # Gap = 0.022 — very borderline; driver KNOWS outer_east
                    "option_id": "WH-OAK01::DRV-009",
                    "warehouse_id": "WH-OAK01", "driver_id": "DRV-009",
                    "timeliness_score": 0.95, "cost_efficiency_score": 0.76,
                    "proximity_score": 0.62, "zone_risk_penalty": 0.087,
                    "composite_score": 0.696,
                    "estimated_cost_gbp": 84.80, "estimated_duration_hours": 3.17,
                },
                {   # Driver also knows outer_east
                    "option_id": "WH-SF01::DRV-007",
                    "warehouse_id": "WH-SF01", "driver_id": "DRV-007",
                    "timeliness_score": 0.91, "cost_efficiency_score": 0.62,
                    "proximity_score": 0.39, "zone_risk_penalty": 0.087,
                    "composite_score": 0.617,
                    "estimated_cost_gbp": 98.60, "estimated_duration_hours": 3.22,
                },
            ],
            "top_choice": {
                "option_id": "WH-OAK01::DRV-001",
                "warehouse_id": "WH-OAK01", "driver_id": "DRV-001",
                "timeliness_score": 0.95, "cost_efficiency_score": 0.83,
                "proximity_score": 0.62, "zone_risk_penalty": 0.087,
                "composite_score": 0.718,
                "estimated_cost_gbp": 78.40, "estimated_duration_hours": 3.18,
            },
        },
    },
}

SCENARIOS = [SCENARIO_A, SCENARIO_B, SCENARIO_C]


# ── SSE stream reader ──────────────────────────────────────────────────────────

async def stream_reason(payload: dict):
    """Consume the /reason SSE stream and yield (event_type, data_dict) tuples."""
    async with httpx.AsyncClient(timeout=180.0) as client:
        async with client.stream(
            "POST", f"{REASONER_URL}/reason", json=payload
        ) as response:
            response.raise_for_status()
            current_event: str | None = None
            async for line in response.aiter_lines():
                if line.startswith("event: "):
                    current_event = line[7:].strip()
                elif line.startswith("data: ") and current_event:
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        data = {"raw": line[6:]}
                    yield current_event, data
                    if current_event == "done":
                        return
                    current_event = None


# ── Scenario runner ────────────────────────────────────────────────────────────

async def run_scenario(scenario: dict) -> None:
    label = scenario["label"]
    payload = scenario["payload"]
    sep = "═" * 74

    print(f"\n{sep}")
    print(f"  {label}")
    print(sep)

    fv = payload["feature_vector"]
    opt = payload["optimizer_output"]
    print(f"  Order: {fv['order_id']}  │  {fv['cargo_type']}  │  "
          f"{fv['weight_kg']} kg  │  ${fv['order_value']:,.0f}  │  "
          f"priority: {fv['priority']}  │  window: {fv['time_window_hours']}h")
    print(f"  Zone : {fv['destination_zone_id']} — "
          f"success {fv['zone_profile']['delivery_success_rate']*100:.0f}%  │  "
          f"complaints {fv['zone_profile']['complaint_rate']*100:.0f}%")
    print(f"  Optimizer top choice: {opt['top_choice']['option_id']}  "
          f"(composite {opt['top_choice']['composite_score']:.3f})")
    print()

    # Stream reasoning
    print("  ── Reasoner deliberation (streaming) ──────────────────────────────")
    reasoning_text = ""
    resolution_data = None
    conclusion_data = None
    t_start = time.perf_counter()

    try:
        async for event_type, data in stream_reason(payload):
            if event_type == "token":
                chunk = data.get("text", "")
                reasoning_text += chunk
                print(chunk, end="", flush=True)

            elif event_type == "conclusion":
                conclusion_data = data
                print()  # newline after streaming text

            elif event_type == "resolution":
                resolution_data = data

            elif event_type == "error":
                print(f"\n  ⚠ ERROR: {data.get('message')}")
                print(f"  Fallback: {data.get('fallback')}")

            elif event_type == "done":
                break

    except httpx.HTTPStatusError as exc:
        print(f"\n  HTTP {exc.response.status_code}: {exc.response.text}")
        return
    except Exception as exc:
        print(f"\n  REQUEST FAILED: {exc}")
        return

    elapsed = time.perf_counter() - t_start

    # Summary
    if conclusion_data:
        print()
        print(f"  ── Conclusion ─────────────────────────────────────────────────────")
        print(f"  DECISION          : {conclusion_data.get('decision', '?').upper()}")
        print(f"  RECOMMENDED OPTION: {conclusion_data.get('recommended_option', '?')}")
        flags = conclusion_data.get("flags", [])
        print(f"  FLAGS             : {', '.join(flags) if flags else 'NONE'}")
        or_ = conclusion_data.get("override_reason")
        if or_:
            print(f"  OVERRIDE REASON   : {or_}")
        parse_ok = conclusion_data.get("parse_ok", True)
        if not parse_ok:
            print("  ⚠ conclusion block not found — parser used fallback heuristics")

    if resolution_data:
        state = resolution_data.get("state", "?").upper()
        state_icon = {"CONVERGENCE": "✓", "QUALIFICATION": "⚠", "OVERRIDE": "✗"}.get(state, "·")
        print()
        print(f"  ── Resolution: {state_icon} {state} ──────────────────────────────────────")
        print(f"  Optimizer choice : {resolution_data.get('optimizer_choice')}")
        print(f"  Reasoner choice  : {resolution_data.get('reasoner_choice')}")
        print(f"  Final decision   : {resolution_data.get('final_option_id')}")
        print(f"  Explanation      : {resolution_data.get('explanation')}")

    print()
    print(f"  Elapsed: {elapsed:.1f}s  │  Reasoning length: {len(reasoning_text)} chars")


# ── Main ───────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║       Reasoner Agent + Resolution Layer — Integration Test               ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")

    # Health check
    try:
        r = httpx.get(f"{REASONER_URL}/health", timeout=3.0)
        r.raise_for_status()
        h = r.json()
        print(f"\n  Reasoner Agent: ✓ OK  │  provider={h['llm_provider']}  │  model={h['llm_model']}")
    except Exception as exc:
        print(f"\n  Reasoner Agent NOT reachable at {REASONER_URL}: {exc}")
        print("  Start services with: bash run_dev.sh  (from the backend/ directory)")
        sys.exit(1)

    # Select scenarios
    if len(sys.argv) > 1:
        idx = [int(a) - 1 for a in sys.argv[1:] if a.isdigit()]
        selected = [SCENARIOS[i] for i in idx if 0 <= i < len(SCENARIOS)]
    else:
        selected = SCENARIOS

    for scenario in selected:
        await run_scenario(scenario)

    print(f"\n{'═'*74}")
    print("  All scenarios complete.")
    print()
    print("  Tip: run a single scenario with:")
    print("    python test_reasoner.py 1   # Convergence")
    print("    python test_reasoner.py 2   # Qualification")
    print("    python test_reasoner.py 3   # Override")


if __name__ == "__main__":
    asyncio.run(main())
