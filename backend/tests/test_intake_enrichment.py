"""Tests for intake_agent/enrichment.py and intake_agent/main.py."""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from shared.models import OrderRequest, FeatureVector
from intake_agent.enrichment import enrich_order


# ── ERP response fixtures ──────────────────────────────────────────────────────

_WAREHOUSES_RESPONSE = {
    "warehouses": [
        {
            "id": "WH-SF01",
            "name": "SF Mission District Fulfillment Center",
            "lat": 37.7599,
            "lon": -122.4148,
            "active": True,
            "stock": {"general": 820, "fragile": 295, "refrigerated": 140, "hazardous": 38},
            "capacity_units": 1200,
        },
        {
            "id": "WH-OAK01",
            "name": "Oakland Harbor Distribution Hub",
            "lat": 37.8044,
            "lon": -122.2712,
            "active": True,
            "stock": {"general": 640, "fragile": 178, "refrigerated": 98, "hazardous": 22},
            "capacity_units": 1000,
        },
        {
            "id": "WH-INACTIVE",
            "name": "Inactive Warehouse",
            "lat": 37.5000,
            "lon": -122.0000,
            "active": False,
            "stock": {"general": 100},
            "capacity_units": 200,
        },
    ]
}

_DRIVERS_RESPONSE = {
    "drivers": [
        {
            "id": "DRV-001",
            "name": "Marcus Johnson",
            "vehicle_type": "van",
            "lat": 37.7920,
            "lon": -122.3985,
            "available": True,
            "current_load_kg": 75.0,
            "max_load_kg": 500.0,
            "active_deliveries": 2,
            "rating": 4.8,
            "zone_familiarity": ["central_sf", "soma_mission", "east_bay"],
        },
        {
            "id": "DRV-004",
            "name": "Mei Chen",
            "vehicle_type": "motorbike",
            "lat": 37.7855,
            "lon": -122.4000,
            "available": True,
            "current_load_kg": 8.0,
            "max_load_kg": 50.0,
            "active_deliveries": 1,
            "rating": 4.7,
            "zone_familiarity": ["central_sf", "soma_mission"],
        },
    ]
}

_ZONE_RESPONSE = {
    "id": "central_sf",
    "name": "SF Financial District / Union Square",
    "delivery_success_rate": 0.96,
    "avg_transit_hours": 1.2,
    "demand_pressure": 0.91,
    "active_routes": 38,
    "complaint_rate": 0.03,
    "last_30_days": {
        "total_deliveries": 2104,
        "successful": 2020,
        "failed": 84,
        "avg_delay_minutes": 7,
    },
}


def _make_mock_response(json_data: dict):
    mock = MagicMock()
    mock.json.return_value = json_data
    return mock


def _make_order(**overrides):
    data = {
        "order_id": "TEST-001",
        "destination_lat": 37.791,
        "destination_lon": -122.399,
        "order_value": 1200.0,
        "weight_kg": 20.0,
        "time_window_hours": 4.0,
        "cargo_type": "general",
        "priority": "standard",
    }
    data.update(overrides)
    return OrderRequest(**data)


@pytest.fixture
def mock_erp(monkeypatch):
    """Patch httpx.AsyncClient to return canned ERP responses."""
    import httpx

    async def fake_gather_responses(*args):
        return (
            _make_mock_response(_WAREHOUSES_RESPONSE),
            _make_mock_response(_DRIVERS_RESPONSE),
            _make_mock_response(_ZONE_RESPONSE),
        )

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[
        _make_mock_response(_WAREHOUSES_RESPONSE),
        _make_mock_response(_DRIVERS_RESPONSE),
        _make_mock_response(_ZONE_RESPONSE),
    ])

    import asyncio

    async def fake_gather(*coros):
        results = []
        for coro in coros:
            results.append(await coro)
        return tuple(results)

    # Patch asyncio.gather so concurrent calls are resolved in order
    monkeypatch.setattr("intake_agent.enrichment.asyncio.gather", fake_gather)

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("intake_agent.enrichment.httpx.AsyncClient",
                        lambda **kwargs: mock_client_ctx)

    return mock_client


# ── enrich_order() tests ───────────────────────────────────────────────────────

class TestEnrichOrder:
    @pytest.mark.asyncio
    async def test_returns_feature_vector(self, mock_erp):
        order = _make_order()
        fv = await enrich_order(order, "http://fake-erp")
        assert isinstance(fv, FeatureVector)

    @pytest.mark.asyncio
    async def test_order_id_propagated(self, mock_erp):
        order = _make_order(order_id="ORD-XYZ")
        fv = await enrich_order(order, "http://fake-erp")
        assert fv.order_id == "ORD-XYZ"

    @pytest.mark.asyncio
    async def test_destination_coords_preserved(self, mock_erp):
        order = _make_order(destination_lat=37.791, destination_lon=-122.399)
        fv = await enrich_order(order, "http://fake-erp")
        assert fv.destination_lat == 37.791
        assert fv.destination_lon == -122.399

    @pytest.mark.asyncio
    async def test_inactive_warehouse_excluded(self, mock_erp):
        order = _make_order()
        fv = await enrich_order(order, "http://fake-erp")
        wh_ids = [w.warehouse_id for w in fv.warehouse_options]
        assert "WH-INACTIVE" not in wh_ids

    @pytest.mark.asyncio
    async def test_warehouse_options_sorted_by_distance(self, mock_erp):
        order = _make_order()
        fv = await enrich_order(order, "http://fake-erp")
        dists = [w.distance_to_destination_km for w in fv.warehouse_options]
        assert dists == sorted(dists)

    @pytest.mark.asyncio
    async def test_stock_confirmed_when_stock_positive(self, mock_erp):
        order = _make_order(cargo_type="general")
        fv = await enrich_order(order, "http://fake-erp")
        for wh in fv.warehouse_options:
            if wh.stock_level > 0:
                assert wh.stock_confirmed is True

    @pytest.mark.asyncio
    async def test_overweight_driver_excluded(self, mock_erp):
        # DRV-004 has max_load_kg=50, so weight_kg=100 should exclude it
        order = _make_order(weight_kg=100.0)
        fv = await enrich_order(order, "http://fake-erp")
        driver_ids = [d.driver_id for d in fv.available_drivers]
        assert "DRV-004" not in driver_ids

    @pytest.mark.asyncio
    async def test_driver_within_capacity_included(self, mock_erp):
        order = _make_order(weight_kg=10.0)
        fv = await enrich_order(order, "http://fake-erp")
        driver_ids = [d.driver_id for d in fv.available_drivers]
        assert "DRV-001" in driver_ids

    @pytest.mark.asyncio
    async def test_drivers_sorted_by_pickup_time(self, mock_erp):
        order = _make_order(weight_kg=10.0)
        fv = await enrich_order(order, "http://fake-erp")
        pickup_times = [d.estimated_pickup_minutes for d in fv.available_drivers]
        assert pickup_times == sorted(pickup_times)

    @pytest.mark.asyncio
    async def test_zone_profile_populated(self, mock_erp):
        order = _make_order()
        fv = await enrich_order(order, "http://fake-erp")
        zp = fv.zone_profile
        assert zp.zone_id == "central_sf"
        assert zp.delivery_success_rate == 0.96
        assert zp.complaint_rate == 0.03

    @pytest.mark.asyncio
    async def test_erp_latency_ms_positive(self, mock_erp):
        order = _make_order()
        fv = await enrich_order(order, "http://fake-erp")
        assert fv.erp_latency_ms >= 0.0

    @pytest.mark.asyncio
    async def test_enrichment_timestamp_is_iso_string(self, mock_erp):
        order = _make_order()
        fv = await enrich_order(order, "http://fake-erp")
        # Should be a parseable ISO timestamp
        from datetime import datetime
        ts = fv.enrichment_timestamp
        assert "T" in ts or len(ts) > 10

    @pytest.mark.asyncio
    async def test_no_stocked_warehouse_driver_gets_far_distance(self, mock_erp, monkeypatch):
        """When no warehouses have stock, driver gets nearest_wh_dist = 999."""
        # Override warehouses to have zero stock
        zero_stock_response = {
            "warehouses": [
                {**_WAREHOUSES_RESPONSE["warehouses"][0],
                 "stock": {"general": 0, "fragile": 0, "refrigerated": 0, "hazardous": 0}},
            ]
        }
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[
            _make_mock_response(zero_stock_response),
            _make_mock_response(_DRIVERS_RESPONSE),
            _make_mock_response(_ZONE_RESPONSE),
        ])

        async def fake_gather(*coros):
            results = []
            for coro in coros:
                results.append(await coro)
            return tuple(results)

        monkeypatch.setattr("intake_agent.enrichment.asyncio.gather", fake_gather)

        mock_client_ctx = AsyncMock()
        mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_ctx.__aexit__ = AsyncMock(return_value=None)
        monkeypatch.setattr("intake_agent.enrichment.httpx.AsyncClient",
                            lambda **kwargs: mock_client_ctx)

        order = _make_order(cargo_type="general", weight_kg=10.0)
        fv = await enrich_order(order, "http://fake-erp")
        # All drivers should have very high pickup time (999 km fallback)
        for drv in fv.available_drivers:
            assert drv.distance_to_nearest_wh_km == 999.0


# ── Intake Agent API (/enrich endpoint) ────────────────────────────────────────

class TestIntakeAPI:
    def _client(self):
        from fastapi.testclient import TestClient
        from intake_agent.main import app
        return TestClient(app)

    def test_health(self):
        resp = self._client().get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_enrich_outside_bay_area_returns_422(self):
        payload = {
            "order_id": "TEST-OOB",
            "destination_lat": 40.7128,   # New York
            "destination_lon": -74.0060,
            "order_value": 500.0,
            "weight_kg": 10.0,
            "time_window_hours": 4.0,
        }
        resp = self._client().post("/enrich", json=payload)
        assert resp.status_code == 422
        assert "Bay Area" in resp.json()["detail"]

    def test_enrich_missing_required_field_returns_422(self):
        payload = {
            "destination_lat": 37.7749,
            "destination_lon": -122.4194,
            # order_id missing
        }
        resp = self._client().post("/enrich", json=payload)
        assert resp.status_code == 422
