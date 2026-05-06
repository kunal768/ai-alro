"""
Pre-seeded demonstration scenarios for the /demo/{scenario_id} endpoint.

These are identical to the payloads in test_reasoner.py — the same data the
integration tests use — so the demo always surfaces the designed decision states.

scenario_id → {"feature_vector": dict, "optimizer_output": dict}
"""

# ── Shared sub-objects ─────────────────────────────────────────────────��──────

_DRIVERS: dict[str, dict] = {
    "DRV-001": {
        "driver_id": "DRV-001", "name": "Marcus Webb", "vehicle_type": "van",
        "current_lat": 51.5235, "current_lon": -0.0755,
        "distance_to_nearest_wh_km": 3.8, "estimated_pickup_minutes": 24.0,
        "current_load_kg": 85.0, "max_load_kg": 500.0, "available_capacity_kg": 415.0,
        "active_deliveries": 2, "rating": 4.8,
        "zone_familiarity": ["central", "east", "north"],
    },
    "DRV-004": {
        "driver_id": "DRV-004", "name": "Priya Sharma", "vehicle_type": "motorbike",
        "current_lat": 51.5054, "current_lon": -0.0235,
        "distance_to_nearest_wh_km": 2.1, "estimated_pickup_minutes": 19.0,
        "current_load_kg": 12.0, "max_load_kg": 50.0, "available_capacity_kg": 38.0,
        "active_deliveries": 1, "rating": 4.7,
        "zone_familiarity": ["east", "central"],
    },
    "DRV-005": {
        "driver_id": "DRV-005", "name": "Tommy Fraser", "vehicle_type": "van",
        "current_lat": 51.4927, "current_lon": -0.2235,
        "distance_to_nearest_wh_km": 5.7, "estimated_pickup_minutes": 28.0,
        "current_load_kg": 0.0, "max_load_kg": 800.0, "available_capacity_kg": 800.0,
        "active_deliveries": 0, "rating": 4.5,
        "zone_familiarity": ["west", "central", "outer_west"],
    },
    "DRV-007": {
        "driver_id": "DRV-007", "name": "Dan Okafor", "vehicle_type": "van",
        "current_lat": 51.4614, "current_lon": -0.0210,
        "distance_to_nearest_wh_km": 2.8, "estimated_pickup_minutes": 16.0,
        "current_load_kg": 155.0, "max_load_kg": 500.0, "available_capacity_kg": 345.0,
        "active_deliveries": 2, "rating": 4.4,
        "zone_familiarity": ["south", "east", "outer_east"],
    },
    "DRV-009": {
        "driver_id": "DRV-009", "name": "Raj Patel", "vehicle_type": "van",
        "current_lat": 51.5362, "current_lon": 0.0798,
        "distance_to_nearest_wh_km": 5.6, "estimated_pickup_minutes": 19.0,
        "current_load_kg": 320.0, "max_load_kg": 600.0, "available_capacity_kg": 280.0,
        "active_deliveries": 4, "rating": 4.3,
        "zone_familiarity": ["east", "outer_east", "north"],
    },
}

_WAREHOUSES: dict[str, dict] = {
    "WH-E01":  {"warehouse_id": "WH-E01",  "name": "Stratford Logistics Hub",
                "lat": 51.5416, "lon": -0.0001, "stock_level": 847, "stock_confirmed": True},
    "WH-SE01": {"warehouse_id": "WH-SE01", "name": "Greenwich Warehouse",
                "lat": 51.4826, "lon":  0.0077, "stock_level": 312, "stock_confirmed": True},
    "WH-W01":  {"warehouse_id": "WH-W01",  "name": "Park Royal Depot",
                "lat": 51.5302, "lon": -0.2805, "stock_level": 734, "stock_confirmed": True},
}


def _wh(wh_id: str, dist: float) -> dict:
    return {**_WAREHOUSES[wh_id], "distance_to_destination_km": dist}


# ── Scenario A — Central London, standard (expected: CONVERGENCE) ─────────────

_SCENARIO_A_FV: dict = {
    "order_id": "DEMO-A001",
    "destination_lat": 51.5155, "destination_lon": -0.0922,
    "destination_zone_id": "central",
    "order_value": 1200.0, "weight_kg": 35.0,
    "time_window_hours": 4.0,
    "cargo_type": "general", "priority": "standard",
    "warehouse_options": [
        _wh("WH-E01", 7.0), _wh("WH-SE01", 7.8), _wh("WH-W01", 13.1),
    ],
    "available_drivers": [
        _DRIVERS["DRV-001"], _DRIVERS["DRV-007"], _DRIVERS["DRV-005"],
    ],
    "zone_profile": {
        "zone_id": "central", "name": "Central London",
        "delivery_success_rate": 0.96, "avg_transit_hours": 1.4,
        "demand_pressure": 0.89, "active_routes": 34,
        "complaint_rate": 0.03,
        "last_30_days_total": 1842, "last_30_days_successful": 1768,
    },
    "enrichment_timestamp": "2026-05-05T09:00:00Z",
    "erp_latency_ms": 18.4,
}

_SCENARIO_A_OPT: dict = {
    "order_id": "DEMO-A001",
    "weights_used": {"w1_timeliness": 0.40, "w2_cost_efficiency": 0.35, "w3_warehouse_proximity": 0.25},
    "ranked_options": [
        {
            "option_id": "WH-E01::DRV-001", "warehouse_id": "WH-E01", "driver_id": "DRV-001",
            "timeliness_score": 0.92, "cost_efficiency_score": 0.81,
            "warehouse_proximity_score": 0.89, "zone_risk_penalty": 0.020,
            "composite_score": 0.855,
            "estimated_cost_gbp": 38.50, "estimated_duration_hours": 1.85,
        },
        {
            "option_id": "WH-SE01::DRV-007", "warehouse_id": "WH-SE01", "driver_id": "DRV-007",
            "timeliness_score": 0.88, "cost_efficiency_score": 0.71,
            "warehouse_proximity_score": 0.85, "zone_risk_penalty": 0.020,
            "composite_score": 0.768,
            "estimated_cost_gbp": 44.20, "estimated_duration_hours": 1.73,
        },
        {
            "option_id": "WH-W01::DRV-005", "warehouse_id": "WH-W01", "driver_id": "DRV-005",
            "timeliness_score": 0.83, "cost_efficiency_score": 0.65,
            "warehouse_proximity_score": 0.72, "zone_risk_penalty": 0.020,
            "composite_score": 0.681,
            "estimated_cost_gbp": 52.80, "estimated_duration_hours": 1.87,
        },
    ],
    "top_choice": {
        "option_id": "WH-E01::DRV-001", "warehouse_id": "WH-E01", "driver_id": "DRV-001",
        "timeliness_score": 0.92, "cost_efficiency_score": 0.81,
        "warehouse_proximity_score": 0.89, "zone_risk_penalty": 0.020,
        "composite_score": 0.855,
        "estimated_cost_gbp": 38.50, "estimated_duration_hours": 1.85,
    },
}

# ── Scenario B — East London, urgent fragile (expected: QUALIFICATION) ─────────
# Stresses: composite gap = 0.032 (borderline); duration = 2.00h = time window;
# Rank 2 is a motorbike carrying fragile goods.

_SCENARIO_B_FV: dict = {
    "order_id": "DEMO-B002",
    "destination_lat": 51.5150, "destination_lon": 0.0350,
    "destination_zone_id": "east",
    "order_value": 4800.0, "weight_kg": 22.0,
    "time_window_hours": 2.0,
    "cargo_type": "fragile", "priority": "urgent",
    "warehouse_options": [_wh("WH-E01", 3.8), _wh("WH-SE01", 4.1)],
    "available_drivers": [_DRIVERS["DRV-001"], _DRIVERS["DRV-004"], _DRIVERS["DRV-007"]],
    "zone_profile": {
        "zone_id": "east", "name": "East London",
        "delivery_success_rate": 0.91, "avg_transit_hours": 1.6,
        "demand_pressure": 0.78, "active_routes": 27,
        "complaint_rate": 0.07,
        "last_30_days_total": 1567, "last_30_days_successful": 1426,
    },
    "enrichment_timestamp": "2026-05-05T09:00:00Z",
    "erp_latency_ms": 9.1,
}

_SCENARIO_B_OPT: dict = {
    "order_id": "DEMO-B002",
    "weights_used": {"w1_timeliness": 0.40, "w2_cost_efficiency": 0.35, "w3_warehouse_proximity": 0.25},
    "ranked_options": [
        {
            "option_id": "WH-E01::DRV-001", "warehouse_id": "WH-E01", "driver_id": "DRV-001",
            "timeliness_score": 0.90, "cost_efficiency_score": 0.77,
            "warehouse_proximity_score": 0.94, "zone_risk_penalty": 0.045,
            "composite_score": 0.823,
            "estimated_cost_gbp": 29.50, "estimated_duration_hours": 2.00,
        },
        {
            # Gap = 0.032 — borderline. Motorbike + fragile = risk.
            "option_id": "WH-E01::DRV-004", "warehouse_id": "WH-E01", "driver_id": "DRV-004",
            "timeliness_score": 0.95, "cost_efficiency_score": 0.72,
            "warehouse_proximity_score": 0.94, "zone_risk_penalty": 0.045,
            "composite_score": 0.791,
            "estimated_cost_gbp": 26.80, "estimated_duration_hours": 1.91,
        },
        {
            "option_id": "WH-SE01::DRV-007", "warehouse_id": "WH-SE01", "driver_id": "DRV-007",
            "timeliness_score": 0.91, "cost_efficiency_score": 0.68,
            "warehouse_proximity_score": 0.93, "zone_risk_penalty": 0.045,
            "composite_score": 0.741,
            "estimated_cost_gbp": 28.90, "estimated_duration_hours": 1.91,
        },
    ],
    "top_choice": {
        "option_id": "WH-E01::DRV-001", "warehouse_id": "WH-E01", "driver_id": "DRV-001",
        "timeliness_score": 0.90, "cost_efficiency_score": 0.77,
        "warehouse_proximity_score": 0.94, "zone_risk_penalty": 0.045,
        "composite_score": 0.823,
        "estimated_cost_gbp": 29.50, "estimated_duration_hours": 2.00,
    },
}

# ── Scenario C — Outer East, standard (expected: OVERRIDE / fairness) ──────────
# Stresses: zone 83% success / 14% complaint (redlining concern); gap = 0.023;
# Rank 1 driver has NO outer_east familiarity; Rank 2 driver knows outer_east.

_SCENARIO_C_FV: dict = {
    "order_id": "DEMO-C003",
    "destination_lat": 51.5640, "destination_lon": 0.1960,
    "destination_zone_id": "outer_east",
    "order_value": 650.0, "weight_kg": 60.0,
    "time_window_hours": 6.0,
    "cargo_type": "general", "priority": "standard",
    "warehouse_options": [_wh("WH-E01", 13.8), _wh("WH-SE01", 15.9)],
    "available_drivers": [
        {**_DRIVERS["DRV-001"], "estimated_pickup_minutes": 20.0},
        {**_DRIVERS["DRV-009"], "estimated_pickup_minutes": 19.0},
        {**_DRIVERS["DRV-007"], "estimated_pickup_minutes": 16.0},
    ],
    "zone_profile": {
        "zone_id": "outer_east", "name": "Outer East (Essex borders)",
        "delivery_success_rate": 0.83, "avg_transit_hours": 2.8,
        "demand_pressure": 0.44, "active_routes": 11,
        "complaint_rate": 0.14,
        "last_30_days_total": 612, "last_30_days_successful": 508,
    },
    "enrichment_timestamp": "2026-05-05T09:00:00Z",
    "erp_latency_ms": 7.3,
}

_SCENARIO_C_OPT: dict = {
    "order_id": "DEMO-C003",
    "weights_used": {"w1_timeliness": 0.40, "w2_cost_efficiency": 0.35, "w3_warehouse_proximity": 0.25},
    "ranked_options": [
        {
            # Wins on cost; driver UNFAMILIAR with outer_east
            "option_id": "WH-E01::DRV-001", "warehouse_id": "WH-E01", "driver_id": "DRV-001",
            "timeliness_score": 0.94, "cost_efficiency_score": 0.82,
            "warehouse_proximity_score": 0.58, "zone_risk_penalty": 0.085,
            "composite_score": 0.712,
            "estimated_cost_gbp": 74.50, "estimated_duration_hours": 3.13,
        },
        {
            # Gap = 0.023 — very borderline; driver KNOWS outer_east
            "option_id": "WH-E01::DRV-009", "warehouse_id": "WH-E01", "driver_id": "DRV-009",
            "timeliness_score": 0.94, "cost_efficiency_score": 0.75,
            "warehouse_proximity_score": 0.58, "zone_risk_penalty": 0.085,
            "composite_score": 0.689,
            "estimated_cost_gbp": 81.30, "estimated_duration_hours": 3.12,
        },
        {
            "option_id": "WH-SE01::DRV-007", "warehouse_id": "WH-SE01", "driver_id": "DRV-007",
            "timeliness_score": 0.95, "cost_efficiency_score": 0.65,
            "warehouse_proximity_score": 0.52, "zone_risk_penalty": 0.085,
            "composite_score": 0.655,
            "estimated_cost_gbp": 89.70, "estimated_duration_hours": 3.07,
        },
    ],
    "top_choice": {
        "option_id": "WH-E01::DRV-001", "warehouse_id": "WH-E01", "driver_id": "DRV-001",
        "timeliness_score": 0.94, "cost_efficiency_score": 0.82,
        "warehouse_proximity_score": 0.58, "zone_risk_penalty": 0.085,
        "composite_score": 0.712,
        "estimated_cost_gbp": 74.50, "estimated_duration_hours": 3.13,
    },
}

# ── Public registry ───────────────────────────────────────────────────────────

DEMO_SCENARIOS: dict[str, dict] = {
    "convergence":   {"feature_vector": _SCENARIO_A_FV, "optimizer_output": _SCENARIO_A_OPT},
    "qualification": {"feature_vector": _SCENARIO_B_FV, "optimizer_output": _SCENARIO_B_OPT},
    "override":      {"feature_vector": _SCENARIO_C_FV, "optimizer_output": _SCENARIO_C_OPT},
}

SCENARIO_METADATA: list[dict] = [
    {
        "id": "convergence",
        "label": "Scenario 1 — Clean Convergence",
        "description": "Standard delivery to Central London. Clear winner on all dimensions. Both agents agree.",
        "expected_outcome": "convergence",
        "order": {
            "order_id": "TEST-001",
            "destination_lat": 51.5155, "destination_lon": -0.0922,
            "order_value": 1200.0, "weight_kg": 35.0,
            "time_window_hours": 4.0,
            "cargo_type": "general", "priority": "standard",
            "scenario": "convergence",
        },
    },
    {
        "id": "qualification",
        "label": "Scenario 2 — Qualification",
        "description": "Urgent fragile goods to East London. Borderline time window. Reasoner surfaces risk.",
        "expected_outcome": "qualification",
        "order": {
            "order_id": "TEST-002",
            "destination_lat": 51.5150, "destination_lon": 0.0350,
            "order_value": 4800.0, "weight_kg": 22.0,
            "time_window_hours": 2.0,
            "cargo_type": "fragile", "priority": "urgent",
            "scenario": "qualification",
        },
    },
    {
        "id": "override",
        "label": "Scenario 3 — Override",
        "description": "Standard delivery to Outer East. Low zone success rate, unfamiliar driver. Fairness override.",
        "expected_outcome": "override",
        "order": {
            "order_id": "TEST-003",
            "destination_lat": 51.5640, "destination_lon": 0.1960,
            "order_value": 650.0, "weight_kg": 60.0,
            "time_window_hours": 6.0,
            "cargo_type": "general", "priority": "standard",
            "scenario": "override",
        },
    },
]
