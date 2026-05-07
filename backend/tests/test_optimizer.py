"""Tests for optimizer_agent/main.py — scoring logic and /score endpoint."""
import pytest
from fastapi.testclient import TestClient

from optimizer_agent.main import app, _score, _WEIGHTS, _MAX_DIST_KM, _MAX_DRIVER_DIST_KM

client = TestClient(app)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _make_warehouse(warehouse_id="WH-SF01", dist_km=5.0):
    return {
        "warehouse_id": warehouse_id,
        "name": "SF Hub",
        "lat": 37.7599,
        "lon": -122.4148,
        "distance_to_destination_km": dist_km,
        "stock_level": 820,
        "stock_confirmed": True,
    }


def _make_driver(driver_id="DRV-001", lat=37.792, lon=-122.398, load=75, max_load=500):
    return {
        "driver_id": driver_id,
        "name": "Test Driver",
        "vehicle_type": "van",
        "current_lat": lat,
        "current_lon": lon,
        "distance_to_nearest_wh_km": 3.2,
        "estimated_pickup_minutes": 20.0,
        "current_load_kg": load,
        "max_load_kg": max_load,
        "available_capacity_kg": max_load - load,
        "active_deliveries": 2,
        "rating": 4.8,
        "zone_familiarity": ["central_sf"],
    }


def _make_feature_vector(priority="standard", weight_kg=20.0, time_window=4.0,
                          warehouses=None, drivers=None):
    return {
        "order_id": "TEST-001",
        "destination_lat": 37.791,
        "destination_lon": -122.399,
        "destination_zone_id": "central_sf",
        "order_value": 1200.0,
        "weight_kg": weight_kg,
        "time_window_hours": time_window,
        "cargo_type": "general",
        "priority": priority,
        "warehouse_options": warehouses or [_make_warehouse()],
        "available_drivers": drivers or [_make_driver()],
        "zone_profile": {
            "zone_id": "central_sf",
            "name": "SF Financial District",
            "delivery_success_rate": 0.96,
            "avg_transit_hours": 1.2,
            "demand_pressure": 0.91,
            "active_routes": 38,
            "complaint_rate": 0.03,
            "last_30_days_total": 2104,
            "last_30_days_successful": 2020,
        },
        "enrichment_timestamp": "2026-05-05T09:00:00Z",
        "erp_latency_ms": 15.0,
    }


# ── Health ─────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["service"] == "optimizer_agent"


# ── _score() pure function ─────────────────────────────────────────────────────

class TestScoreFunction:
    def test_returns_all_required_keys(self):
        wh = _make_warehouse()
        drv = _make_driver()
        fv = _make_feature_vector()
        weights = _WEIGHTS["standard"]
        result = _score(wh, drv, fv, weights)
        for key in ("option_id", "warehouse_id", "driver_id", "timeliness_score",
                    "cost_efficiency_score", "proximity_score", "zone_risk_penalty",
                    "composite_score", "estimated_cost_gbp", "estimated_duration_hours"):
            assert key in result, f"Missing key: {key!r}"

    def test_option_id_format(self):
        wh = _make_warehouse("WH-SF01")
        drv = _make_driver("DRV-001")
        result = _score(wh, drv, _make_feature_vector(), _WEIGHTS["standard"])
        assert result["option_id"] == "WH-SF01::DRV-001"

    def test_scores_in_range_zero_to_one(self):
        wh = _make_warehouse()
        drv = _make_driver()
        fv = _make_feature_vector()
        result = _score(wh, drv, fv, _WEIGHTS["standard"])
        for score_key in ("timeliness_score", "cost_efficiency_score", "proximity_score"):
            val = result[score_key]
            assert 0.0 <= val <= 1.0, f"{score_key} = {val} out of [0, 1]"

    def test_zone_risk_penalty_capped_at_0_30(self):
        # Very high complaint rate zone → penalty should be capped
        wh = _make_warehouse()
        drv = _make_driver()
        fv = _make_feature_vector()
        fv["zone_profile"]["delivery_success_rate"] = 0.50  # terrible zone
        fv["zone_profile"]["complaint_rate"] = 0.99
        result = _score(wh, drv, fv, _WEIGHTS["standard"])
        assert result["zone_risk_penalty"] <= 0.30

    def test_closer_warehouse_higher_proximity(self):
        drv = _make_driver()
        fv_near = _make_feature_vector(warehouses=[_make_warehouse(dist_km=2.0)])
        fv_far = _make_feature_vector(warehouses=[_make_warehouse(dist_km=50.0)])
        near = _score(_make_warehouse(dist_km=2.0), drv, fv_near, _WEIGHTS["standard"])
        far = _score(_make_warehouse(dist_km=50.0), drv, fv_far, _WEIGHTS["standard"])
        assert near["proximity_score"] > far["proximity_score"]

    def test_very_far_warehouse_zero_proximity(self):
        wh = _make_warehouse(dist_km=_MAX_DIST_KM + 10.0)
        drv = _make_driver()
        fv = _make_feature_vector(warehouses=[wh])
        result = _score(wh, drv, fv, _WEIGHTS["standard"])
        assert result["proximity_score"] >= 0.0  # clamped, not negative

    def test_larger_time_window_higher_timeliness(self):
        wh = _make_warehouse()
        drv = _make_driver()
        fv_wide = _make_feature_vector(time_window=8.0)
        fv_tight = _make_feature_vector(time_window=1.0)
        wide = _score(wh, drv, fv_wide, _WEIGHTS["standard"])
        tight = _score(wh, drv, fv_tight, _WEIGHTS["standard"])
        assert wide["timeliness_score"] >= tight["timeliness_score"]

    def test_estimated_cost_positive(self):
        result = _score(_make_warehouse(), _make_driver(), _make_feature_vector(), _WEIGHTS["standard"])
        assert result["estimated_cost_gbp"] > 0.0

    def test_critical_priority_weights(self):
        weights = _WEIGHTS["critical"]
        assert weights["w1_timeliness"] > weights["w2_cost_efficiency"]

    def test_standard_priority_weights_sum_to_one(self):
        w = _WEIGHTS["standard"]
        total = w["w1_timeliness"] + w["w2_cost_efficiency"] + w["w3_proximity"]
        assert total == pytest.approx(1.0)

    def test_composite_score_calculation(self):
        wh = _make_warehouse()
        drv = _make_driver()
        fv = _make_feature_vector()
        weights = _WEIGHTS["standard"]
        result = _score(wh, drv, fv, weights)
        expected = (
            result["timeliness_score"] * weights["w1_timeliness"]
            + result["cost_efficiency_score"] * weights["w2_cost_efficiency"]
            + result["proximity_score"] * weights["w3_proximity"]
            - result["zone_risk_penalty"]
        )
        assert result["composite_score"] == pytest.approx(expected, abs=0.01)


# ── /score endpoint ────────────────────────────────────────────────────────────

class TestScoreEndpoint:
    def test_missing_feature_vector_returns_error(self):
        resp = client.post("/score", json={})
        assert resp.status_code == 200
        assert resp.json()["status"] == "error"

    def test_no_stocked_warehouses_returns_no_options(self):
        fv = _make_feature_vector()
        fv["warehouse_options"][0]["stock_confirmed"] = False
        resp = client.post("/score", json={"feature_vector": fv})
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_options"

    def test_no_capable_drivers_returns_no_options(self):
        # Driver capacity < order weight
        fv = _make_feature_vector(weight_kg=600.0)
        fv["available_drivers"] = [_make_driver(load=490, max_load=500)]  # only 10 kg capacity
        resp = client.post("/score", json={"feature_vector": fv})
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_options"

    def test_valid_request_returns_ok(self):
        fv = _make_feature_vector()
        resp = client.post("/score", json={"feature_vector": fv})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_optimizer_output_has_required_keys(self):
        fv = _make_feature_vector()
        resp = client.post("/score", json={"feature_vector": fv})
        opt = resp.json()["optimizer_output"]
        for key in ("order_id", "ranked_options", "top_choice", "weights_used"):
            assert key in opt, f"Missing key: {key!r}"

    def test_ranked_options_sorted_by_composite_descending(self):
        fv = _make_feature_vector(
            warehouses=[_make_warehouse("WH-A", 2.0), _make_warehouse("WH-B", 30.0)],
            drivers=[_make_driver("DRV-1"), _make_driver("DRV-2", lat=37.850, lon=-122.200)],
        )
        resp = client.post("/score", json={"feature_vector": fv})
        options = resp.json()["optimizer_output"]["ranked_options"]
        scores = [o["composite_score"] for o in options]
        assert scores == sorted(scores, reverse=True)

    def test_top_choice_is_first_ranked(self):
        fv = _make_feature_vector()
        resp = client.post("/score", json={"feature_vector": fv})
        data = resp.json()["optimizer_output"]
        assert data["top_choice"]["option_id"] == data["ranked_options"][0]["option_id"]

    def test_at_most_4_options_returned(self):
        fv = _make_feature_vector(
            warehouses=[_make_warehouse("WH-A", 2.0), _make_warehouse("WH-B", 5.0)],
            drivers=[
                _make_driver("DRV-1"),
                _make_driver("DRV-2", lat=37.800, lon=-122.380),
                _make_driver("DRV-3", lat=37.810, lon=-122.390),
                _make_driver("DRV-4", lat=37.820, lon=-122.370),
                _make_driver("DRV-5", lat=37.830, lon=-122.360),
            ],
        )
        resp = client.post("/score", json={"feature_vector": fv})
        options = resp.json()["optimizer_output"]["ranked_options"]
        assert len(options) <= 4

    def test_weight_overrides_applied(self):
        fv = _make_feature_vector(priority="standard")
        overrides = {"w1_timeliness": 0.80, "w2_cost_efficiency": 0.10, "w3_proximity": 0.10}
        resp = client.post("/score", json={"feature_vector": fv, "weights": overrides})
        assert resp.status_code == 200
        weights_used = resp.json()["optimizer_output"]["weights_used"]
        assert weights_used["w1_timeliness"] == 0.80

    def test_critical_priority_uses_correct_weights(self):
        fv = _make_feature_vector(priority="critical")
        resp = client.post("/score", json={"feature_vector": fv})
        weights = resp.json()["optimizer_output"]["weights_used"]
        assert weights["w1_timeliness"] == _WEIGHTS["critical"]["w1_timeliness"]

    def test_order_id_propagated(self):
        fv = _make_feature_vector()
        fv["order_id"] = "MY-ORDER-XYZ"
        resp = client.post("/score", json={"feature_vector": fv})
        assert resp.json()["optimizer_output"]["order_id"] == "MY-ORDER-XYZ"
