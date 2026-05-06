"""
Pre-seeded demonstration scenarios for the /demo/{scenario_id} endpoint.

Geography: San Francisco Bay Area.
Scenario A → convergence, Scenario B → qualification, Scenario C → override.
"""

# ── Shared sub-objects ─────────────────────────────────────────────────────────

_DRIVERS: dict[str, dict] = {
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

_WAREHOUSES: dict[str, dict] = {
    "WH-SF01":  {"warehouse_id": "WH-SF01",  "name": "SF Mission District Fulfillment Center",
                 "lat": 37.7599, "lon": -122.4148, "stock_level": 820, "stock_confirmed": True},
    "WH-OAK01": {"warehouse_id": "WH-OAK01", "name": "Oakland Harbor Distribution Hub",
                 "lat": 37.8044, "lon": -122.2712, "stock_level": 640, "stock_confirmed": True},
    "WH-SSF01": {"warehouse_id": "WH-SSF01", "name": "South San Francisco Peninsula Hub",
                 "lat": 37.6527, "lon": -122.4477, "stock_level": 710, "stock_confirmed": True},
}


def _wh(wh_id: str, dist: float) -> dict:
    return {**_WAREHOUSES[wh_id], "distance_to_destination_km": dist}


# ── Scenario A — SF Financial District, standard (expected: CONVERGENCE) ───────

_SCENARIO_A_FV: dict = {
    "order_id": "DEMO-A001",
    "destination_lat": 37.7910, "destination_lon": -122.3990,
    "destination_zone_id": "central_sf",
    "order_value": 1200.0, "weight_kg": 32.0,
    "time_window_hours": 4.0,
    "cargo_type": "general", "priority": "standard",
    "warehouse_options": [_wh("WH-SF01", 4.2), _wh("WH-OAK01", 14.8), _wh("WH-SSF01", 8.1)],
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
}

_SCENARIO_A_OPT: dict = {
    "order_id": "DEMO-A001",
    "weights_used": {"w1_timeliness": 0.40, "w2_cost_efficiency": 0.35, "w3_warehouse_proximity": 0.25},
    "ranked_options": [
        {
            "option_id": "WH-SF01::DRV-001", "warehouse_id": "WH-SF01", "driver_id": "DRV-001",
            "timeliness_score": 0.93, "cost_efficiency_score": 0.82,
            "warehouse_proximity_score": 0.92, "zone_risk_penalty": 0.018,
            "composite_score": 0.879,
            "estimated_cost_gbp": 42.80, "estimated_duration_hours": 1.72,
        },
        {
            "option_id": "WH-SSF01::DRV-007", "warehouse_id": "WH-SSF01", "driver_id": "DRV-007",
            "timeliness_score": 0.86, "cost_efficiency_score": 0.74,
            "warehouse_proximity_score": 0.78, "zone_risk_penalty": 0.018,
            "composite_score": 0.785,
            "estimated_cost_gbp": 54.20, "estimated_duration_hours": 1.95,
        },
        {
            "option_id": "WH-OAK01::DRV-005", "warehouse_id": "WH-OAK01", "driver_id": "DRV-005",
            "timeliness_score": 0.80, "cost_efficiency_score": 0.64,
            "warehouse_proximity_score": 0.61, "zone_risk_penalty": 0.018,
            "composite_score": 0.680,
            "estimated_cost_gbp": 68.50, "estimated_duration_hours": 2.14,
        },
    ],
    "top_choice": {
        "option_id": "WH-SF01::DRV-001", "warehouse_id": "WH-SF01", "driver_id": "DRV-001",
        "timeliness_score": 0.93, "cost_efficiency_score": 0.82,
        "warehouse_proximity_score": 0.92, "zone_risk_penalty": 0.018,
        "composite_score": 0.879,
        "estimated_cost_gbp": 42.80, "estimated_duration_hours": 1.72,
    },
}

# ── Scenario B — East Bay, urgent fragile (expected: QUALIFICATION) ────────────
# Stresses: composite gap = 0.031 (borderline); estimated duration = 1.95h ≈ time window;
# Rank 2 is a motorbike carrying fragile goods.

_SCENARIO_B_FV: dict = {
    "order_id": "DEMO-B002",
    "destination_lat": 37.8100, "destination_lon": -122.2650,
    "destination_zone_id": "east_bay",
    "order_value": 5200.0, "weight_kg": 20.0,
    "time_window_hours": 2.0,
    "cargo_type": "fragile", "priority": "urgent",
    "warehouse_options": [_wh("WH-OAK01", 3.5), _wh("WH-SF01", 13.2)],
    "available_drivers": [_DRIVERS["DRV-009"], _DRIVERS["DRV-004"], _DRIVERS["DRV-001"]],
    "zone_profile": {
        "zone_id": "east_bay", "name": "East Bay (Oakland / Berkeley)",
        "delivery_success_rate": 0.91, "avg_transit_hours": 1.7,
        "demand_pressure": 0.75, "active_routes": 24,
        "complaint_rate": 0.07,
        "last_30_days_total": 1380, "last_30_days_successful": 1256,
    },
    "enrichment_timestamp": "2026-05-05T09:00:00Z",
    "erp_latency_ms": 8.7,
}

_SCENARIO_B_OPT: dict = {
    "order_id": "DEMO-B002",
    "weights_used": {"w1_timeliness": 0.40, "w2_cost_efficiency": 0.35, "w3_warehouse_proximity": 0.25},
    "ranked_options": [
        {
            "option_id": "WH-OAK01::DRV-009", "warehouse_id": "WH-OAK01", "driver_id": "DRV-009",
            "timeliness_score": 0.88, "cost_efficiency_score": 0.75,
            "warehouse_proximity_score": 0.95, "zone_risk_penalty": 0.040,
            "composite_score": 0.820,
            "estimated_cost_gbp": 32.10, "estimated_duration_hours": 1.95,
        },
        {
            # Gap = 0.031 — borderline. Motorbike + fragile = risk.
            "option_id": "WH-OAK01::DRV-004", "warehouse_id": "WH-OAK01", "driver_id": "DRV-004",
            "timeliness_score": 0.94, "cost_efficiency_score": 0.70,
            "warehouse_proximity_score": 0.95, "zone_risk_penalty": 0.040,
            "composite_score": 0.789,
            "estimated_cost_gbp": 29.40, "estimated_duration_hours": 1.88,
        },
        {
            "option_id": "WH-SF01::DRV-001", "warehouse_id": "WH-SF01", "driver_id": "DRV-001",
            "timeliness_score": 0.85, "cost_efficiency_score": 0.63,
            "warehouse_proximity_score": 0.68, "zone_risk_penalty": 0.040,
            "composite_score": 0.721,
            "estimated_cost_gbp": 48.90, "estimated_duration_hours": 2.08,
        },
    ],
    "top_choice": {
        "option_id": "WH-OAK01::DRV-009", "warehouse_id": "WH-OAK01", "driver_id": "DRV-009",
        "timeliness_score": 0.88, "cost_efficiency_score": 0.75,
        "warehouse_proximity_score": 0.95, "zone_risk_penalty": 0.040,
        "composite_score": 0.820,
        "estimated_cost_gbp": 32.10, "estimated_duration_hours": 1.95,
    },
}

# ── Scenario C — Hayward / Outer East, standard (expected: OVERRIDE / fairness) ─
# Stresses: zone 83% success / 14% complaint (redlining concern); gap = 0.022;
# Rank 1 driver has NO outer_east familiarity; Rank 2 driver knows outer_east.

_SCENARIO_C_FV: dict = {
    "order_id": "DEMO-C003",
    "destination_lat": 37.6688, "destination_lon": -122.0808,
    "destination_zone_id": "outer_east",
    "order_value": 680.0, "weight_kg": 55.0,
    "time_window_hours": 6.0,
    "cargo_type": "general", "priority": "standard",
    "warehouse_options": [_wh("WH-OAK01", 12.6), _wh("WH-SF01", 22.1)],
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
}

_SCENARIO_C_OPT: dict = {
    "order_id": "DEMO-C003",
    "weights_used": {"w1_timeliness": 0.40, "w2_cost_efficiency": 0.35, "w3_warehouse_proximity": 0.25},
    "ranked_options": [
        {
            # Wins on cost; driver UNFAMILIAR with outer_east
            "option_id": "WH-OAK01::DRV-001", "warehouse_id": "WH-OAK01", "driver_id": "DRV-001",
            "timeliness_score": 0.95, "cost_efficiency_score": 0.83,
            "warehouse_proximity_score": 0.62, "zone_risk_penalty": 0.087,
            "composite_score": 0.718,
            "estimated_cost_gbp": 78.40, "estimated_duration_hours": 3.18,
        },
        {
            # Gap = 0.022 — very borderline; driver KNOWS outer_east
            "option_id": "WH-OAK01::DRV-009", "warehouse_id": "WH-OAK01", "driver_id": "DRV-009",
            "timeliness_score": 0.95, "cost_efficiency_score": 0.76,
            "warehouse_proximity_score": 0.62, "zone_risk_penalty": 0.087,
            "composite_score": 0.696,
            "estimated_cost_gbp": 84.80, "estimated_duration_hours": 3.17,
        },
        {
            "option_id": "WH-SF01::DRV-007", "warehouse_id": "WH-SF01", "driver_id": "DRV-007",
            "timeliness_score": 0.91, "cost_efficiency_score": 0.62,
            "warehouse_proximity_score": 0.39, "zone_risk_penalty": 0.087,
            "composite_score": 0.617,
            "estimated_cost_gbp": 98.60, "estimated_duration_hours": 3.22,
        },
    ],
    "top_choice": {
        "option_id": "WH-OAK01::DRV-001", "warehouse_id": "WH-OAK01", "driver_id": "DRV-001",
        "timeliness_score": 0.95, "cost_efficiency_score": 0.83,
        "warehouse_proximity_score": 0.62, "zone_risk_penalty": 0.087,
        "composite_score": 0.718,
        "estimated_cost_gbp": 78.40, "estimated_duration_hours": 3.18,
    },
}

# ── Public registry ────────────────────────────────────────────────────────────

DEMO_SCENARIOS: dict[str, dict] = {
    "convergence":   {"feature_vector": _SCENARIO_A_FV, "optimizer_output": _SCENARIO_A_OPT},
    "qualification": {"feature_vector": _SCENARIO_B_FV, "optimizer_output": _SCENARIO_B_OPT},
    "override":      {"feature_vector": _SCENARIO_C_FV, "optimizer_output": _SCENARIO_C_OPT},
}

SCENARIO_METADATA: list[dict] = [
    {
        "id": "convergence",
        "label": "Scenario 1 — Clean Convergence",
        "description": "Standard delivery to SF Financial District. Clear winner on all dimensions. Both agents agree.",
        "expected_outcome": "convergence",
        "order": {
            "order_id": "TEST-001",
            "destination_lat": 37.7910, "destination_lon": -122.3990,
            "order_value": 1200.0, "weight_kg": 32.0,
            "time_window_hours": 4.0,
            "cargo_type": "general", "priority": "standard",
            "scenario": "convergence",
        },
    },
    {
        "id": "qualification",
        "label": "Scenario 2 — Qualification",
        "description": "Urgent fragile goods to Oakland. Borderline time window. Reasoner surfaces risk.",
        "expected_outcome": "qualification",
        "order": {
            "order_id": "TEST-002",
            "destination_lat": 37.8100, "destination_lon": -122.2650,
            "order_value": 5200.0, "weight_kg": 20.0,
            "time_window_hours": 2.0,
            "cargo_type": "fragile", "priority": "urgent",
            "scenario": "qualification",
        },
    },
    {
        "id": "override",
        "label": "Scenario 3 — Override",
        "description": "Standard delivery to Hayward. Low zone success rate, unfamiliar driver. Fairness override.",
        "expected_outcome": "override",
        "order": {
            "order_id": "TEST-003",
            "destination_lat": 37.6688, "destination_lon": -122.0808,
            "order_value": 680.0, "weight_kg": 55.0,
            "time_window_hours": 6.0,
            "cargo_type": "general", "priority": "standard",
            "scenario": "override",
        },
    },
]
