"""Tests for erp_service/main.py — ERP REST API endpoints."""
import pytest
from fastapi.testclient import TestClient

from erp_service.main import app
from erp_service.seed_data import WAREHOUSES, DRIVERS, ZONES, PENDING_ORDERS

client = TestClient(app)


# ── Health ─────────────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["service"] == "erp_service"


# ── Warehouses ─────────────────────────────────────────────────────────────────

class TestWarehouses:
    def test_get_all_warehouses(self):
        resp = client.get("/warehouses")
        assert resp.status_code == 200
        data = resp.json()
        assert "warehouses" in data
        assert len(data["warehouses"]) == len(WAREHOUSES)

    def test_warehouse_has_required_fields(self):
        resp = client.get("/warehouses")
        wh = resp.json()["warehouses"][0]
        for field in ("id", "name", "lat", "lon", "stock", "active"):
            assert field in wh, f"Field {field!r} missing from warehouse"

    def test_get_single_warehouse(self):
        wh_id = WAREHOUSES[0]["id"]
        resp = client.get(f"/warehouses/{wh_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == wh_id

    def test_get_nonexistent_warehouse_returns_404(self):
        resp = client.get("/warehouses/WH-DOESNOTEXIST")
        assert resp.status_code == 404

    def test_get_warehouse_stock(self):
        wh_id = WAREHOUSES[0]["id"]
        resp = client.get(f"/warehouses/{wh_id}/stock")
        assert resp.status_code == 200
        data = resp.json()
        assert data["warehouse_id"] == wh_id
        assert "stock" in data
        assert "capacity_units" in data

    def test_get_stock_nonexistent_warehouse_returns_404(self):
        resp = client.get("/warehouses/WH-GHOST/stock")
        assert resp.status_code == 404

    def test_stock_contains_cargo_types(self):
        wh_id = WAREHOUSES[0]["id"]
        resp = client.get(f"/warehouses/{wh_id}/stock")
        stock = resp.json()["stock"]
        for cargo_type in ("general", "fragile", "refrigerated", "hazardous"):
            assert cargo_type in stock


# ── Drivers ────────────────────────────────────────────────────────────────────

class TestDrivers:
    def test_get_all_drivers(self):
        resp = client.get("/drivers")
        assert resp.status_code == 200
        data = resp.json()
        assert "drivers" in data
        assert "total" in data
        assert data["total"] == len(DRIVERS)

    def test_filter_available_drivers(self):
        resp = client.get("/drivers?available=true")
        assert resp.status_code == 200
        drivers = resp.json()["drivers"]
        assert all(d["available"] is True for d in drivers)

    def test_filter_unavailable_drivers(self):
        resp = client.get("/drivers?available=false")
        assert resp.status_code == 200
        drivers = resp.json()["drivers"]
        assert all(d["available"] is False for d in drivers)

    def test_available_and_unavailable_counts_add_up(self):
        total = client.get("/drivers").json()["total"]
        available = client.get("/drivers?available=true").json()["total"]
        unavailable = client.get("/drivers?available=false").json()["total"]
        assert available + unavailable == total

    def test_driver_has_required_fields(self):
        resp = client.get("/drivers")
        drv = resp.json()["drivers"][0]
        for field in ("id", "name", "vehicle_type", "lat", "lon", "available",
                      "current_load_kg", "max_load_kg", "rating"):
            assert field in drv, f"Field {field!r} missing from driver"

    def test_get_single_driver(self):
        drv_id = DRIVERS[0]["id"]
        resp = client.get(f"/drivers/{drv_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == drv_id

    def test_get_nonexistent_driver_returns_404(self):
        resp = client.get("/drivers/DRV-GHOST")
        assert resp.status_code == 404


# ── Zones ──────────────────────────────────────────────────────────────────────

class TestZones:
    def test_get_all_zones(self):
        resp = client.get("/zones")
        assert resp.status_code == 200
        data = resp.json()
        assert "zones" in data
        assert len(data["zones"]) == len(ZONES)

    def test_zone_summary_has_required_fields(self):
        resp = client.get("/zones")
        zone = resp.json()["zones"][0]
        for field in ("id", "name", "delivery_success_rate", "demand_pressure", "active_routes"):
            assert field in zone, f"Field {field!r} missing from zone summary"

    def test_get_single_zone(self):
        zone_id = "central_sf"
        resp = client.get(f"/zones/{zone_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == zone_id

    def test_single_zone_has_history(self):
        resp = client.get("/zones/central_sf")
        data = resp.json()
        assert "last_30_days" in data
        assert "total_deliveries" in data["last_30_days"]

    def test_get_nonexistent_zone_returns_404(self):
        resp = client.get("/zones/mars_colony")
        assert resp.status_code == 404

    def test_all_seeded_zones_retrievable(self):
        for zone_id in ZONES:
            resp = client.get(f"/zones/{zone_id}")
            assert resp.status_code == 200, f"Zone {zone_id!r} not retrievable"

    def test_delivery_success_rate_in_range(self):
        resp = client.get("/zones")
        for zone in resp.json()["zones"]:
            rate = zone["delivery_success_rate"]
            assert 0.0 <= rate <= 1.0, f"delivery_success_rate out of range for {zone['id']}"


# ── Orders ─────────────────────────────────────────────────────────────────────

class TestOrders:
    def test_get_pending_orders(self):
        resp = client.get("/orders/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert "orders" in data
        assert "total" in data
        assert data["total"] == len(PENDING_ORDERS)

    def test_default_limit_50(self):
        resp = client.get("/orders/pending")
        orders = resp.json()["orders"]
        assert len(orders) <= 50

    def test_limit_param(self):
        resp = client.get("/orders/pending?limit=3")
        assert resp.status_code == 200
        orders = resp.json()["orders"]
        assert len(orders) <= 3

    def test_order_has_required_fields(self):
        resp = client.get("/orders/pending")
        order = resp.json()["orders"][0]
        for field in ("order_id", "destination_lat", "destination_lon",
                      "order_value", "weight_kg", "cargo_type", "priority"):
            assert field in order, f"Field {field!r} missing from order"
