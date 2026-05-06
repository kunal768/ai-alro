"""
Pre-seeded demonstration scenarios for the /demo/{scenario_id} endpoint.

Geography: San Francisco Bay Area.
Scenario A → convergence, Scenario B → qualification, Scenario C → override.

Optimizer outputs are computed at import time using the same scoring logic as
the Optimizer Agent — no hardcoded scores.
"""
from shared.utils import haversine, classify_zone, estimate_road_speed_kmh

# ── Scoring constants (must mirror optimizer_agent/main.py) ───────────────────

_MAX_DIST_KM        = 60.0
_MAX_DRIVER_DIST_KM = 40.0
_COST_CEILING       = 400.0
_LOADING_MINUTES    = 12.0

_WEIGHTS: dict[str, dict] = {
    "critical": {"w1_timeliness": 0.45, "w2_cost_efficiency": 0.15, "w3_proximity": 0.40},
    "urgent":   {"w1_timeliness": 0.35, "w2_cost_efficiency": 0.20, "w3_proximity": 0.45},
    "standard": {"w1_timeliness": 0.30, "w2_cost_efficiency": 0.25, "w3_proximity": 0.45},
}


def _score_option(wh: dict, drv: dict, fv: dict, weights: dict) -> dict:
    w1 = weights["w1_timeliness"]
    w2 = weights["w2_cost_efficiency"]
    w3 = weights["w3_proximity"]
    zone = fv["zone_profile"]

    drv_to_wh_km = haversine(drv["current_lat"], drv["current_lon"], wh["lat"], wh["lon"])
    drv_zone  = classify_zone(drv["current_lat"], drv["current_lon"])
    drv_speed = estimate_road_speed_kmh(drv_zone)
    pickup_minutes = (drv_to_wh_km / drv_speed) * 60.0 + _LOADING_MINUTES

    dest_zone_speed = estimate_road_speed_kmh(zone["zone_id"])
    wh_to_dest_h = wh["distance_to_destination_km"] / dest_zone_speed

    pickup_h = pickup_minutes / 60.0
    total_h  = pickup_h + wh_to_dest_h
    margin   = fv["time_window_hours"] - total_h
    timeliness = max(0.0, min(1.0, 0.5 + margin / fv["time_window_hours"]))

    est_cost = (
        15.0
        + wh["distance_to_destination_km"] * 2.20
        + drv_to_wh_km * 1.80
        + fv["weight_kg"] * 0.25
    )
    cost_eff = max(0.0, min(1.0, 1.0 - est_cost / _COST_CEILING))

    wh_proximity  = max(0.0, min(1.0, 1.0 - wh["distance_to_destination_km"] / _MAX_DIST_KM))
    drv_proximity = max(0.0, min(1.0, 1.0 - drv_to_wh_km / _MAX_DRIVER_DIST_KM))
    proximity_score = (wh_proximity + drv_proximity) / 2.0

    zone_risk = min(
        0.30,
        (1.0 - zone["delivery_success_rate"]) * 0.60
        + zone.get("complaint_rate", 0.0) * 0.25,
    )

    composite = timeliness * w1 + cost_eff * w2 + proximity_score * w3 - zone_risk

    return {
        "option_id":                f"{wh['warehouse_id']}::{drv['driver_id']}",
        "warehouse_id":             wh["warehouse_id"],
        "driver_id":                drv["driver_id"],
        "timeliness_score":         round(timeliness, 3),
        "cost_efficiency_score":    round(cost_eff, 3),
        "proximity_score":          round(proximity_score, 3),
        "zone_risk_penalty":        round(zone_risk, 3),
        "composite_score":          round(composite, 3),
        "estimated_cost_gbp":       round(est_cost, 2),
        "estimated_duration_hours": round(total_h, 2),
    }


def _compute_opt(fv: dict) -> dict:
    priority = fv.get("priority", "standard")
    weights  = _WEIGHTS.get(priority, _WEIGHTS["standard"])
    weight_kg = fv.get("weight_kg", 0.0)

    stocked     = [w for w in fv.get("warehouse_options", []) if w.get("stock_confirmed")]
    stocked_top = sorted(stocked, key=lambda w: w["distance_to_destination_km"])[:2]

    capable     = [d for d in fv.get("available_drivers", []) if d.get("available_capacity_kg", 0) >= weight_kg]
    drivers_top = sorted(capable, key=lambda d: d["estimated_pickup_minutes"])[:4]

    options = []
    for wh in stocked_top:
        for drv in drivers_top:
            options.append(_score_option(wh, drv, fv, weights))

    options.sort(key=lambda o: o["composite_score"], reverse=True)
    top4 = options[:4]

    return {
        "order_id":       fv.get("order_id", ""),
        "weights_used":   weights,
        "ranked_options": top4,
        "top_choice":     top4[0],
    }


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

# ── Scenario B — East Bay, urgent fragile (expected: QUALIFICATION) ────────────
# Stresses: composite gap ≈ borderline; estimated duration ≈ time window;
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

# ── Scenario C — Hayward / Outer East, standard (expected: OVERRIDE / fairness) ─
# Stresses: zone 83% success / 14% complaint (redlining concern); gap ≈ borderline;
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

# ── Public registry ────────────────────────────────────────────────────────────

DEMO_SCENARIOS: dict[str, dict] = {
    "convergence":   {"feature_vector": _SCENARIO_A_FV, "optimizer_output": _compute_opt(_SCENARIO_A_FV)},
    "qualification": {"feature_vector": _SCENARIO_B_FV, "optimizer_output": _compute_opt(_SCENARIO_B_FV)},
    "override":      {"feature_vector": _SCENARIO_C_FV, "optimizer_output": _compute_opt(_SCENARIO_C_FV)},
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
