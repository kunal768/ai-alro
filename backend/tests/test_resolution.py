"""Tests for reasoner_agent/resolution.py — resolve() and _lookup_names()."""
import pytest

from shared.models import OptimizerOutput, ReasonerOutput, RoutingOption
from reasoner_agent.resolution import resolve, _lookup_names


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _routing_option(option_id="WH-SF01::DRV-001", composite=0.879):
    wh_id, drv_id = option_id.split("::")
    return RoutingOption(
        option_id=option_id,
        warehouse_id=wh_id,
        driver_id=drv_id,
        timeliness_score=0.93,
        cost_efficiency_score=0.82,
        proximity_score=0.92,
        zone_risk_penalty=0.018,
        composite_score=composite,
        estimated_cost_gbp=42.80,
        estimated_duration_hours=1.72,
    )


def _optimizer(order_id="ORD-001", top_option_id="WH-SF01::DRV-001"):
    top = _routing_option(top_option_id)
    return OptimizerOutput(
        order_id=order_id,
        ranked_options=[top],
        top_choice=top,
        weights_used={"w1_timeliness": 0.30, "w2_cost_efficiency": 0.25, "w3_proximity": 0.45},
    )


def _reasoner(order_id="ORD-001", conclusion="confirm",
              recommended_id="WH-SF01::DRV-001", risks=None, override_reason=None):
    return ReasonerOutput(
        order_id=order_id,
        conclusion=conclusion,
        recommended_option_id=recommended_id,
        chain_of_thought="Full deliberation text...",
        flagged_risks=risks or [],
        override_reason=override_reason,
    )


_FEATURE_VECTOR = {
    "warehouse_options": [
        {"warehouse_id": "WH-SF01", "name": "SF Mission District Fulfillment Center"},
        {"warehouse_id": "WH-OAK01", "name": "Oakland Harbor Distribution Hub"},
    ],
    "available_drivers": [
        {"driver_id": "DRV-001", "name": "Marcus Johnson"},
        {"driver_id": "DRV-009", "name": "Amara Okonkwo"},
    ],
}


# ── _lookup_names ──────────────────────────────────────────────────────────────

class TestLookupNames:
    def test_known_ids_return_names(self):
        wh, drv = _lookup_names(_FEATURE_VECTOR, "WH-SF01::DRV-001")
        assert "SF Mission" in wh
        assert "Marcus" in drv

    def test_unknown_warehouse_falls_back(self):
        wh, drv = _lookup_names(_FEATURE_VECTOR, "WH-GHOST::DRV-001")
        assert "WH-GHOST" in wh

    def test_unknown_driver_falls_back(self):
        wh, drv = _lookup_names(_FEATURE_VECTOR, "WH-SF01::DRV-999")
        assert "DRV-999" in drv

    def test_no_double_colon_returns_option_id(self):
        wh, drv = _lookup_names(_FEATURE_VECTOR, "MALFORMED")
        assert wh == "MALFORMED"
        assert drv == ""

    def test_empty_option_id(self):
        wh, drv = _lookup_names(_FEATURE_VECTOR, "")
        assert wh == "unknown"

    def test_none_feature_vector(self):
        wh, drv = _lookup_names(None, "WH-SF01::DRV-001")
        assert "WH-SF01" in wh


# ── resolve() — convergence ────────────────────────────────────────────────────

class TestResolveConvergence:
    def test_confirm_same_option_is_convergence(self):
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="confirm", recommended_id="WH-SF01::DRV-001")
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert result.state == "convergence"

    def test_convergence_final_option_matches_both(self):
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="confirm", recommended_id="WH-SF01::DRV-001")
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert result.final_option_id == "WH-SF01::DRV-001"
        assert result.optimizer_choice == result.reasoner_choice

    def test_convergence_explanation_mentions_agreement(self):
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="confirm", recommended_id="WH-SF01::DRV-001")
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert "agree" in result.explanation.lower() or "correct" in result.explanation.lower()

    def test_order_id_propagated(self):
        opt = _optimizer(order_id="ORD-XYZ", top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(order_id="ORD-XYZ", conclusion="confirm", recommended_id="WH-SF01::DRV-001")
        result = resolve(opt, rea)
        assert result.order_id == "ORD-XYZ"

    def test_case_insensitive_conclusion(self):
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="CONFIRM", recommended_id="WH-SF01::DRV-001")
        result = resolve(opt, rea)
        assert result.state == "convergence"


# ── resolve() — qualification ──────────────────────────────────────────────────

class TestResolveQualification:
    def test_qualify_conclusion_is_qualification_state(self):
        opt = _optimizer(top_option_id="WH-OAK01::DRV-009")
        rea = _reasoner(
            conclusion="qualify",
            recommended_id="WH-OAK01::DRV-009",
            risks=["tight time window", "high complaint zone"],
        )
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert result.state == "qualification"

    def test_qualification_final_option_is_reasoner_choice(self):
        opt = _optimizer(top_option_id="WH-OAK01::DRV-009")
        rea = _reasoner(conclusion="qualify", recommended_id="WH-OAK01::DRV-009",
                        risks=["tight window"])
        result = resolve(opt, rea)
        assert result.final_option_id == "WH-OAK01::DRV-009"

    def test_qualification_explanation_contains_risks(self):
        opt = _optimizer(top_option_id="WH-OAK01::DRV-009")
        rea = _reasoner(conclusion="qualify", recommended_id="WH-OAK01::DRV-009",
                        risks=["tight time window"])
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert "tight time window" in result.explanation

    def test_qualification_no_risks_still_surfaces_condition(self):
        opt = _optimizer(top_option_id="WH-OAK01::DRV-009")
        rea = _reasoner(conclusion="qualify", recommended_id="WH-OAK01::DRV-009", risks=[])
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert result.state == "qualification"
        assert len(result.explanation) > 0


# ── resolve() — override ───────────────────────────────────────────────────────

class TestResolveOverride:
    def test_override_conclusion_is_override_state(self):
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(
            conclusion="override",
            recommended_id="WH-OAK01::DRV-009",
            override_reason="Driver unfamiliar with destination zone.",
        )
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert result.state == "override"

    def test_override_final_option_is_reasoner_choice(self):
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="override", recommended_id="WH-OAK01::DRV-009",
                        override_reason="Zone familiarity concern.")
        result = resolve(opt, rea)
        assert result.final_option_id == "WH-OAK01::DRV-009"

    def test_override_when_options_differ_even_without_override_conclusion(self):
        # confirm conclusion but different option ids → override state
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="confirm", recommended_id="WH-OAK01::DRV-009")
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert result.state == "override"

    def test_override_explanation_mentions_both_choices(self):
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="override", recommended_id="WH-OAK01::DRV-009",
                        override_reason="Different option preferred.")
        result = resolve(opt, rea, _FEATURE_VECTOR)
        # Should mention both sides
        assert len(result.explanation) > 50

    def test_override_reason_in_explanation(self):
        reason_text = "Driver is unfamiliar with this zone and it has high complaint rate."
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="override", recommended_id="WH-OAK01::DRV-009",
                        override_reason=reason_text)
        result = resolve(opt, rea, _FEATURE_VECTOR)
        assert reason_text in result.explanation

    def test_override_optimizer_and_reasoner_choices_differ(self):
        opt = _optimizer(top_option_id="WH-SF01::DRV-001")
        rea = _reasoner(conclusion="override", recommended_id="WH-OAK01::DRV-009",
                        override_reason="Reason.")
        result = resolve(opt, rea)
        assert result.optimizer_choice != result.reasoner_choice


# ── resolve() — result structure ──────────────────────────────────────────────

class TestResolveStructure:
    def test_result_is_resolution_result_model(self):
        from shared.models import ResolutionResult
        opt = _optimizer()
        rea = _reasoner()
        result = resolve(opt, rea)
        assert isinstance(result, ResolutionResult)

    def test_result_has_all_fields(self):
        opt = _optimizer()
        rea = _reasoner()
        result = resolve(opt, rea)
        for field in ("order_id", "state", "final_option_id",
                      "optimizer_choice", "reasoner_choice", "explanation"):
            assert getattr(result, field) is not None
