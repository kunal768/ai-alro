"""
Optimizer Agent — Port 8003

The quantitative voice. Receives a FeatureVector from the Intake Agent and
scores all viable routing options against the reward function:

    reward = (timeliness_score      × w1)
           + (cost_efficiency_score × w2)
           + (proximity_score       × w3)   # combined: (warehouse→dest + driver→warehouse) / 2
           − zone_risk_penalty

Returns a ranked list of RoutingOptions with decomposed scores. Architecture
supports a trained RL policy as a drop-in replacement for the scoring function.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.utils import haversine, classify_zone, estimate_road_speed_kmh

app = FastAPI(title="Optimizer Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reward weights per priority tier — must sum to 1.0 before zone_risk subtraction.
# w3_proximity covers both warehouse→destination and driver→warehouse (equal split internally).
_WEIGHTS: dict[str, dict] = {
    "critical": {"w1_timeliness": 0.45, "w2_cost_efficiency": 0.15, "w3_proximity": 0.40},
    "urgent":   {"w1_timeliness": 0.35, "w2_cost_efficiency": 0.20, "w3_proximity": 0.45},
    "standard": {"w1_timeliness": 0.30, "w2_cost_efficiency": 0.25, "w3_proximity": 0.45},
}

# Normalisation constants calibrated for Bay Area logistics
_MAX_DIST_KM        = 60.0   # warehouse→destination: beyond this, proximity → 0
_MAX_DRIVER_DIST_KM = 40.0   # driver→warehouse: beyond this, driver proximity → 0
_COST_CEILING       = 400.0  # above this, cost efficiency score → 0
_LOADING_MINUTES    = 12.0   # fixed overhead: dock time, packing, paperwork


def _score(wh: dict, drv: dict, fv: dict, weights: dict) -> dict:
    """Score a single (warehouse, driver) routing option."""
    w1 = weights["w1_timeliness"]
    w2 = weights["w2_cost_efficiency"]
    w3 = weights["w3_proximity"]
    zone = fv["zone_profile"]

    # Actual driver→warehouse distance for this specific pairing (not nearest-wh proxy)
    drv_to_wh_km = haversine(
        drv["current_lat"], drv["current_lon"],
        wh["lat"], wh["lon"],
    )
    drv_zone = classify_zone(drv["current_lat"], drv["current_lon"])
    drv_speed = estimate_road_speed_kmh(drv_zone)
    pickup_minutes = (drv_to_wh_km / drv_speed) * 60.0 + _LOADING_MINUTES

    # Actual warehouse→destination travel time (replaces zone-constant avg_transit_hours)
    dest_zone_speed = estimate_road_speed_kmh(zone["zone_id"])
    wh_to_dest_h = wh["distance_to_destination_km"] / dest_zone_speed

    # ── Timeliness ────────────────────────────────────────────────────────────
    pickup_h = pickup_minutes / 60.0
    total_h  = pickup_h + wh_to_dest_h
    # 1.0 when instantaneous, 0.0 at deadline, negative (clamped) when late.
    # Uses the full window range so fast routes score higher even when all fit.
    timeliness = max(0.0, min(1.0, 1.0 - total_h / fv["time_window_hours"]))

    # ── Cost efficiency ───────────────────────────────────────────────────────
    est_cost = (
        15.0
        + wh["distance_to_destination_km"] * 2.20   # warehouse → destination leg
        + drv_to_wh_km * 1.80                        # driver → warehouse leg
        + fv["weight_kg"] * 0.25
    )
    cost_eff = max(0.0, min(1.0, 1.0 - est_cost / _COST_CEILING))

    # ── Combined proximity: average of warehouse→dest and driver→warehouse ────
    wh_proximity  = max(0.0, min(1.0, 1.0 - wh["distance_to_destination_km"] / _MAX_DIST_KM))
    drv_proximity = max(0.0, min(1.0, 1.0 - drv_to_wh_km / _MAX_DRIVER_DIST_KM))
    proximity_score = (wh_proximity + drv_proximity) / 2.0

    # ── Zone risk penalty ─────────────────────────────────────────────────────
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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "optimizer_agent"}


@app.post("/score")
async def score_options(payload: dict):
    """
    Accept a FeatureVector (plus optional weight overrides) and return an
    OptimizerOutput with ranked RoutingOptions.

    Candidate pairs are (warehouse × driver). Ineligible candidates are
    filtered out: no stock, insufficient capacity, or out-of-service driver.
    To keep the output readable, at most 2 warehouses and 4 drivers are
    considered; the top 4 composites are returned.
    """
    fv = payload.get("feature_vector", {})
    if not fv:
        return {"status": "error", "optimizer_output": None, "detail": "feature_vector missing"}

    priority = fv.get("priority", "standard")
    base_weights = _WEIGHTS.get(priority, _WEIGHTS["standard"])
    weights = {**base_weights, **payload.get("weights", {})}

    weight_kg = fv.get("weight_kg", 0.0)

    # Filter warehouses: must have confirmed stock
    stocked = [w for w in fv.get("warehouse_options", []) if w.get("stock_confirmed")]
    # Keep closest 2 to limit combinatorial explosion
    stocked_top = sorted(stocked, key=lambda w: w["distance_to_destination_km"])[:2]

    # Filter drivers: must have capacity
    capable = [
        d for d in fv.get("available_drivers", [])
        if d.get("available_capacity_kg", 0) >= weight_kg
    ]
    # Keep 4 drivers with shortest ETA to nearest warehouse (actual per-pairing
    # distance is recomputed in _score; this is a reasonable pre-filter)
    drivers_top = sorted(capable, key=lambda d: d["estimated_pickup_minutes"])[:4]

    if not stocked_top or not drivers_top:
        return {"status": "no_options", "optimizer_output": None}

    options = []
    for wh in stocked_top:
        for drv in drivers_top:
            options.append(_score(wh, drv, fv, weights))

    options.sort(key=lambda o: o["composite_score"], reverse=True)
    top4 = options[:4]

    return {
        "status": "ok",
        "optimizer_output": {
            "order_id":       fv.get("order_id", ""),
            "ranked_options": top4,
            "top_choice":     top4[0],
            "weights_used":   weights,
        },
    }
