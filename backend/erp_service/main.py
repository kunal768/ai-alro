"""
Simulated ERP Service — Port 8001

Production-compatible REST interface returning seeded London logistics data.
Replacing this service with a real ERP connector requires no changes to
the interface contract consumed by the Intake Agent.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from erp_service.seed_data import WAREHOUSES, DRIVERS, ZONES, PENDING_ORDERS

app = FastAPI(title="Simulated ERP Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "erp_service"}


# ── Warehouses ─────────────────────────────────────────────────────────────────

@app.get("/warehouses")
async def get_warehouses():
    """Return all warehouses with current stock levels."""
    return {"warehouses": WAREHOUSES}


@app.get("/warehouses/{warehouse_id}")
async def get_warehouse(warehouse_id: str):
    """Return a single warehouse record."""
    match = next((w for w in WAREHOUSES if w["id"] == warehouse_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Warehouse {warehouse_id!r} not found")
    return match


@app.get("/warehouses/{warehouse_id}/stock")
async def get_warehouse_stock(warehouse_id: str):
    """Return stock levels for a specific warehouse."""
    match = next((w for w in WAREHOUSES if w["id"] == warehouse_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Warehouse {warehouse_id!r} not found")
    return {
        "warehouse_id": warehouse_id,
        "stock": match["stock"],
        "capacity_units": match["capacity_units"],
    }


# ── Drivers ────────────────────────────────────────────────────────────────────

@app.get("/drivers")
async def get_drivers(available: bool | None = None):
    """Return the driver pool. Pass ?available=true to filter to free drivers."""
    result = DRIVERS
    if available is not None:
        result = [d for d in result if d["available"] == available]
    return {"drivers": result, "total": len(result)}


@app.get("/drivers/{driver_id}")
async def get_driver(driver_id: str):
    """Return a single driver record."""
    match = next((d for d in DRIVERS if d["id"] == driver_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Driver {driver_id!r} not found")
    return match


# ── Zones ──────────────────────────────────────────────────────────────────────

@app.get("/zones")
async def get_zones():
    """Return summary data for all delivery zones."""
    summaries = [
        {
            "id": z["id"],
            "name": z["name"],
            "delivery_success_rate": z["delivery_success_rate"],
            "demand_pressure": z["demand_pressure"],
            "active_routes": z["active_routes"],
        }
        for z in ZONES.values()
    ]
    return {"zones": summaries}


@app.get("/zones/{zone_id}")
async def get_zone(zone_id: str):
    """Return the full profile for a delivery zone, including 30-day history."""
    zone = ZONES.get(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id!r} not found")
    return zone


# ── Orders ─────────────────────────────────────────────────────────────────────

@app.get("/orders/pending")
async def get_pending_orders(limit: int = 50):
    """Return the pending order queue, newest first."""
    return {
        "orders": PENDING_ORDERS[:limit],
        "total": len(PENDING_ORDERS),
    }
