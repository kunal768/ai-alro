"""Tests for reasoner_agent/prompts.py — build_user_prompt()."""
import pytest

from reasoner_agent.prompts import build_user_prompt, SYSTEM_PROMPT


_FEATURE_VECTOR = {
    "order_id": "TEST-001",
    "destination_lat": 37.791,
    "destination_lon": -122.399,
    "destination_zone_id": "central_sf",
    "order_value": 1200.0,
    "weight_kg": 32.0,
    "time_window_hours": 4.0,
    "cargo_type": "general",
    "priority": "standard",
    "warehouse_options": [
        {
            "warehouse_id": "WH-SF01",
            "name": "SF Mission Fulfillment Center",
            "lat": 37.7599,
            "lon": -122.4148,
            "distance_to_destination_km": 4.2,
            "stock_level": 820,
            "stock_confirmed": True,
        }
    ],
    "available_drivers": [
        {
            "driver_id": "DRV-001",
            "name": "Marcus Johnson",
            "vehicle_type": "van",
            "current_lat": 37.792,
            "current_lon": -122.398,
            "distance_to_nearest_wh_km": 3.2,
            "estimated_pickup_minutes": 20.0,
            "current_load_kg": 75.0,
            "max_load_kg": 500.0,
            "available_capacity_kg": 425.0,
            "active_deliveries": 2,
            "rating": 4.8,
            "zone_familiarity": ["central_sf", "east_bay"],
        }
    ],
    "zone_profile": {
        "zone_id": "central_sf",
        "name": "SF Financial District / Union Square",
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

_OPTIMIZER_OUTPUT = {
    "order_id": "TEST-001",
    "weights_used": {
        "w1_timeliness": 0.30,
        "w2_cost_efficiency": 0.25,
        "w3_proximity": 0.45,
    },
    "ranked_options": [
        {
            "option_id": "WH-SF01::DRV-001",
            "warehouse_id": "WH-SF01",
            "driver_id": "DRV-001",
            "timeliness_score": 0.93,
            "cost_efficiency_score": 0.82,
            "proximity_score": 0.92,
            "zone_risk_penalty": 0.018,
            "composite_score": 0.879,
            "estimated_cost_gbp": 42.80,
            "estimated_duration_hours": 1.72,
        }
    ],
    "top_choice": {
        "option_id": "WH-SF01::DRV-001",
        "warehouse_id": "WH-SF01",
        "driver_id": "DRV-001",
        "timeliness_score": 0.93,
        "cost_efficiency_score": 0.82,
        "proximity_score": 0.92,
        "zone_risk_penalty": 0.018,
        "composite_score": 0.879,
        "estimated_cost_gbp": 42.80,
        "estimated_duration_hours": 1.72,
    },
}


class TestSystemPrompt:
    def test_system_prompt_is_non_empty_string(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 200

    def test_system_prompt_defines_three_decisions(self):
        assert "CONFIRM" in SYSTEM_PROMPT
        assert "QUALIFY" in SYSTEM_PROMPT
        assert "OVERRIDE" in SYSTEM_PROMPT

    def test_system_prompt_has_conclusion_format(self):
        assert "<conclusion>" in SYSTEM_PROMPT
        assert "DECISION:" in SYSTEM_PROMPT
        assert "RECOMMENDED_OPTION:" in SYSTEM_PROMPT
        assert "FLAGS:" in SYSTEM_PROMPT
        assert "OVERRIDE_REASON:" in SYSTEM_PROMPT


class TestBuildUserPrompt:
    def _build(self, fv=None, opt=None):
        return build_user_prompt(fv or _FEATURE_VECTOR, opt or _OPTIMIZER_OUTPUT)

    def test_returns_string(self):
        assert isinstance(self._build(), str)

    def test_contains_order_id(self):
        prompt = self._build()
        assert "TEST-001" in prompt

    def test_contains_cargo_type(self):
        prompt = self._build()
        assert "general" in prompt

    def test_contains_priority(self):
        prompt = self._build()
        assert "standard" in prompt

    def test_contains_time_window(self):
        prompt = self._build()
        assert "4.0" in prompt or "4" in prompt

    def test_contains_zone_info(self):
        prompt = self._build()
        assert "central_sf" in prompt

    def test_contains_delivery_success_rate(self):
        prompt = self._build()
        assert "96%" in prompt or "0.96" in prompt

    def test_contains_complaint_rate(self):
        prompt = self._build()
        # 0.03 → 3%
        assert "3%" in prompt or "0.03" in prompt

    def test_contains_optimizer_section(self):
        prompt = self._build()
        assert "OPTIMIZER" in prompt.upper()

    def test_contains_rank_labels(self):
        prompt = self._build()
        assert "RANK 1" in prompt

    def test_contains_top_choice_label(self):
        prompt = self._build()
        assert "TOP CHOICE" in prompt

    def test_contains_option_id(self):
        prompt = self._build()
        assert "WH-SF01::DRV-001" in prompt

    def test_contains_composite_score(self):
        prompt = self._build()
        assert "0.879" in prompt

    def test_contains_driver_name(self):
        prompt = self._build()
        assert "Marcus Johnson" in prompt

    def test_contains_weights(self):
        prompt = self._build()
        assert "0.3" in prompt or "0.30" in prompt

    def test_unfamiliar_zone_flagged(self):
        fv = {**_FEATURE_VECTOR, "destination_zone_id": "north_bay"}
        prompt = self._build(fv=fv)
        assert "NOT in familiarity" in prompt or "NOT" in prompt

    def test_familiar_zone_not_flagged_negatively(self):
        # Driver IS familiar with central_sf
        prompt = self._build()
        assert "NOT in familiarity" not in prompt

    def test_multiple_ranked_options_all_present(self):
        opt = {
            **_OPTIMIZER_OUTPUT,
            "ranked_options": [
                _OPTIMIZER_OUTPUT["ranked_options"][0],
                {**_OPTIMIZER_OUTPUT["ranked_options"][0],
                 "option_id": "WH-OAK01::DRV-009",
                 "warehouse_id": "WH-OAK01",
                 "driver_id": "DRV-009",
                 "composite_score": 0.750},
            ],
        }
        prompt = self._build(opt=opt)
        assert "RANK 1" in prompt
        assert "RANK 2" in prompt
