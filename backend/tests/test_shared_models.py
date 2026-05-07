"""Tests for shared/models.py — Pydantic model validation and defaults."""
import pytest
from pydantic import ValidationError

from shared.models import (
    OrderRequest,
    WarehouseOption,
    DriverOption,
    ZoneProfile,
    FeatureVector,
    RoutingOption,
    OptimizerOutput,
    ReasonerOutput,
    ResolutionResult,
)


# ── OrderRequest ───────────────────────────────────────────────────────────────

class TestOrderRequest:
    def _valid(self, **overrides):
        data = {
            "order_id": "ORD-001",
            "destination_lat": 37.7749,
            "destination_lon": -122.4194,
            "order_value": 500.0,
            "weight_kg": 20.0,
            "time_window_hours": 4.0,
        }
        data.update(overrides)
        return OrderRequest(**data)

    def test_minimal_valid(self):
        order = self._valid()
        assert order.order_id == "ORD-001"
        assert order.cargo_type == "general"   # default
        assert order.priority == "standard"    # default
        assert order.scenario is None          # default

    def test_custom_cargo_and_priority(self):
        order = self._valid(cargo_type="fragile", priority="critical")
        assert order.cargo_type == "fragile"
        assert order.priority == "critical"

    def test_scenario_optional(self):
        order = self._valid(scenario="convergence")
        assert order.scenario == "convergence"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            OrderRequest(
                destination_lat=37.7749,
                destination_lon=-122.4194,
                order_value=500.0,
                weight_kg=20.0,
                time_window_hours=4.0,
                # order_id missing
            )

    def test_float_fields_accept_int(self):
        order = self._valid(order_value=500, weight_kg=20, time_window_hours=4)
        assert isinstance(order.order_value, float)
        assert isinstance(order.weight_kg, float)


# ── WarehouseOption ────────────────────────────────────────────────────────────

class TestWarehouseOption:
    def test_valid(self):
        wh = WarehouseOption(
            warehouse_id="WH-SF01",
            name="SF Hub",
            lat=37.7599,
            lon=-122.4148,
            distance_to_destination_km=4.2,
            stock_level=820,
            stock_confirmed=True,
        )
        assert wh.warehouse_id == "WH-SF01"
        assert wh.stock_confirmed is True

    def test_stock_confirmed_false(self):
        wh = WarehouseOption(
            warehouse_id="WH-X", name="X", lat=0, lon=0,
            distance_to_destination_km=0, stock_level=0, stock_confirmed=False,
        )
        assert wh.stock_confirmed is False


# ── DriverOption ───────────────────────────────────────────────────────────────

class TestDriverOption:
    def _valid(self):
        return DriverOption(
            driver_id="DRV-001",
            name="Marcus Johnson",
            vehicle_type="van",
            current_lat=37.792,
            current_lon=-122.398,
            distance_to_nearest_wh_km=3.2,
            estimated_pickup_minutes=20.0,
            current_load_kg=75.0,
            max_load_kg=500.0,
            available_capacity_kg=425.0,
            active_deliveries=2,
            rating=4.8,
            zone_familiarity=["central_sf", "east_bay"],
        )

    def test_valid(self):
        drv = self._valid()
        assert drv.driver_id == "DRV-001"
        assert drv.zone_familiarity == ["central_sf", "east_bay"]

    def test_empty_zone_familiarity(self):
        drv = DriverOption(
            driver_id="DRV-X", name="X", vehicle_type="van",
            current_lat=0, current_lon=0, distance_to_nearest_wh_km=0,
            estimated_pickup_minutes=0, current_load_kg=0, max_load_kg=100,
            available_capacity_kg=100, active_deliveries=0, rating=4.0,
            zone_familiarity=[],
        )
        assert drv.zone_familiarity == []


# ── ZoneProfile ────────────────────────────────────────────────────────────────

class TestZoneProfile:
    def test_valid(self):
        zp = ZoneProfile(
            zone_id="central_sf",
            name="SF Financial District",
            delivery_success_rate=0.96,
            avg_transit_hours=1.2,
            demand_pressure=0.91,
            active_routes=38,
            complaint_rate=0.03,
            last_30_days_total=2104,
            last_30_days_successful=2020,
        )
        assert zp.zone_id == "central_sf"
        assert zp.delivery_success_rate == 0.96


# ── RoutingOption ──────────────────────────────────────────────────────────────

class TestRoutingOption:
    def test_valid(self):
        opt = RoutingOption(
            option_id="WH-SF01::DRV-001",
            warehouse_id="WH-SF01",
            driver_id="DRV-001",
            timeliness_score=0.93,
            cost_efficiency_score=0.82,
            proximity_score=0.92,
            zone_risk_penalty=0.018,
            composite_score=0.879,
            estimated_cost_gbp=42.80,
            estimated_duration_hours=1.72,
        )
        assert "::" in opt.option_id


# ── OptimizerOutput ────────────────────────────────────────────────────────────

class TestOptimizerOutput:
    def _routing_option(self, option_id="WH-SF01::DRV-001"):
        return RoutingOption(
            option_id=option_id,
            warehouse_id=option_id.split("::")[0],
            driver_id=option_id.split("::")[1],
            timeliness_score=0.9,
            cost_efficiency_score=0.8,
            proximity_score=0.7,
            zone_risk_penalty=0.02,
            composite_score=0.8,
            estimated_cost_gbp=50.0,
            estimated_duration_hours=2.0,
        )

    def test_valid(self):
        top = self._routing_option()
        out = OptimizerOutput(
            order_id="ORD-001",
            ranked_options=[top],
            top_choice=top,
            weights_used={"w1": 0.3, "w2": 0.25, "w3": 0.45},
        )
        assert out.order_id == "ORD-001"
        assert len(out.ranked_options) == 1


# ── ReasonerOutput ─────────────────────────────────────────────────────────────

class TestReasonerOutput:
    def test_confirm_no_override_reason(self):
        out = ReasonerOutput(
            order_id="ORD-001",
            conclusion="confirm",
            recommended_option_id="WH-SF01::DRV-001",
            chain_of_thought="...",
            flagged_risks=[],
        )
        assert out.override_reason is None

    def test_override_with_reason(self):
        out = ReasonerOutput(
            order_id="ORD-001",
            conclusion="override",
            recommended_option_id="WH-OAK01::DRV-009",
            chain_of_thought="...",
            flagged_risks=["zone familiarity"],
            override_reason="Driver unfamiliar with destination zone.",
        )
        assert out.override_reason is not None


# ── ResolutionResult ───────────────────────────────────────────────────────────

class TestResolutionResult:
    def test_valid_convergence(self):
        r = ResolutionResult(
            order_id="ORD-001",
            state="convergence",
            final_option_id="WH-SF01::DRV-001",
            optimizer_choice="WH-SF01::DRV-001",
            reasoner_choice="WH-SF01::DRV-001",
            explanation="Both systems agree.",
        )
        assert r.state == "convergence"
        assert r.final_option_id == r.reasoner_choice
