"""
Optimizer Agent — Port 8003

The quantitative voice. Receives a FeatureVector from the Intake Agent and
scores all viable routing options against the reward function:

    reward = (timeliness_score × w1)
           + (cost_efficiency_score × w2)
           + (warehouse_proximity_score × w3)
           − zone_risk_penalty

Returns a ranked list of RoutingOptions with decomposed scores. Architecture
supports a trained RL policy as a drop-in replacement for the scoring function.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Optimizer Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reward weights per priority tier
_WEIGHTS: dict[str, dict] = {
    "critical": {"w1_timeliness": 0.55, "w2_cost_efficiency": 0.20, "w3_warehouse_proximity": 0.25},
    "urgent":   {"w1_timeliness": 0.45, "w2_cost_efficiency": 0.25, "w3_warehouse_proximity": 0.30},
    "standard": {"w1_timeliness": 0.40, "w2_cost_efficiency": 0.35, "w3_warehouse_proximity": 0.25},
}

# Normalisation constants tuned for Greater London logistics
_MAX_DIST_KM  = 30.0   # beyond this, proximity score → 0
_COST_CEILING = 260.0  # above this, cost efficiency score → 0


def _score(wh: dict, drv: dict, fv: dict, weights: dict) -> dict:
    """Score a single (warehouse, driver) routing option."""
    w1 = weights["w1_timeliness"]
    w2 = weights["w2_cost_efficiency"]
    w3 = weights["w3_warehouse_proximity"]
    zone = fv["zone_profile"]

    # ── Timeliness ────────────────────────────────────────────────────────────
    pickup_h = drv["estimated_pickup_minutes"] / 60.0
    total_h  = pickup_h + zone["avg_transit_hours"]
    margin   = fv["time_window_hours"] - total_h
    # Score = 0.5 when margin = 0 (just makes it), 1.0 when margin = time_window
    timeliness = max(0.0, min(1.0, 0.5 + margin / fv["time_window_hours"]))

    # ── Cost efficiency ───────────────────────────────────────────────────────
    # Simplified cost model: base + per-km + per-kg + driver-time
    est_cost = (
        12.0
        + wh["distance_to_destination_km"] * 1.80
        + fv["weight_kg"] * 0.25
        + drv["estimated_pickup_minutes"] * 0.35
    )
    cost_eff = max(0.0, min(1.0, 1.0 - est_cost / _COST_CEILING))

    # ── Warehouse proximity ───────────────────────────────────────────────────
    proximity = max(0.0, min(1.0, 1.0 - wh["distance_to_destination_km"] / _MAX_DIST_KM))

    # ── Zone risk penalty ─────────────────────────────────────────────────────
    zone_risk = min(
        0.30,
        (1.0 - zone["delivery_success_rate"]) * 0.60
        + zone.get("complaint_rate", 0.0) * 0.25,
    )

    composite = timeliness * w1 + cost_eff * w2 + proximity * w3 - zone_risk

    return {
        "option_id":                  f"{wh['warehouse_id']}::{drv['driver_id']}",
        "warehouse_id":               wh["warehouse_id"],
        "driver_id":                  drv["driver_id"],
        "timeliness_score":           round(timeliness, 3),
        "cost_efficiency_score":      round(cost_eff, 3),
        "warehouse_proximity_score":  round(proximity, 3),
        "zone_risk_penalty":          round(zone_risk, 3),
        "composite_score":            round(composite, 3),
        "estimated_cost_gbp":         round(est_cost, 2),
        "estimated_duration_hours":   round(total_h, 2),
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
    To keep the output readable, at most 2 warehouses and 3 drivers are
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
    # Keep 3 drivers with shortest ETA
    drivers_top = sorted(capable, key=lambda d: d["estimated_pickup_minutes"])[:3]

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
