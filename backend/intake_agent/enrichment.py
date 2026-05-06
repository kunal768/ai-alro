"""
Enrichment logic for the Intake Agent.

Calls the ERP service (concurrently) to fetch warehouses, drivers, and zone data,
then assembles a FeatureVector that both the Optimizer and Reasoner consume.
"""
import asyncio
import time
from datetime import datetime, timezone

import httpx

from shared.models import (
    DriverOption,
    FeatureVector,
    OrderRequest,
    WarehouseOption,
    ZoneProfile,
)
from shared.utils import classify_zone, haversine, estimate_road_speed_kmh

_LOADING_TIME_MINUTES = 12.0   # fixed overhead: dock time, packing, paperwork


async def enrich_order(order: OrderRequest, erp_url: str) -> FeatureVector:
    """
    Enrich a raw OrderRequest with ERP data and return a FeatureVector.

    ERP calls are made concurrently. Driver ETAs are computed as:
        distance(driver → nearest stocked warehouse) / zone_speed + loading_time
    """
    t0 = time.perf_counter()

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Three concurrent ERP calls
        zone_id = classify_zone(order.destination_lat, order.destination_lon)
        warehouses_task, drivers_task, zone_task = await asyncio.gather(
            client.get(f"{erp_url}/warehouses"),
            client.get(f"{erp_url}/drivers?available=true"),
            client.get(f"{erp_url}/zones/{zone_id}"),
        )

    erp_latency_ms = (time.perf_counter() - t0) * 1000

    warehouses_raw: list[dict] = warehouses_task.json()["warehouses"]
    drivers_raw: list[dict] = drivers_task.json()["drivers"]
    zone_raw: dict = zone_task.json()

    # ── Warehouse options ──────────────────────────────────────────────────────

    warehouse_options: list[WarehouseOption] = []
    for wh in warehouses_raw:
        if not wh["active"]:
            continue
        dist = haversine(
            order.destination_lat, order.destination_lon, wh["lat"], wh["lon"]
        )
        stock = wh["stock"].get(order.cargo_type, 0)
        warehouse_options.append(
            WarehouseOption(
                warehouse_id=wh["id"],
                name=wh["name"],
                lat=wh["lat"],
                lon=wh["lon"],
                distance_to_destination_km=round(dist, 2),
                stock_level=stock,
                stock_confirmed=stock > 0,
            )
        )

    warehouse_options.sort(key=lambda w: w.distance_to_destination_km)

    # Precompute nearest-stocked-warehouse location for each driver ETA lookup
    stocked_warehouses = [w for w in warehouse_options if w.stock_confirmed]

    # ── Driver options ─────────────────────────────────────────────────────────

    available_drivers: list[DriverOption] = []
    driver_zone_speed = estimate_road_speed_kmh(zone_id)

    for drv in drivers_raw:
        capacity_remaining = drv["max_load_kg"] - drv["current_load_kg"]
        if capacity_remaining < order.weight_kg:
            continue  # can't carry this load

        if stocked_warehouses:
            nearest_wh_dist = min(
                haversine(drv["lat"], drv["lon"], wh.lat, wh.lon)
                for wh in stocked_warehouses
            )
        else:
            nearest_wh_dist = 999.0

        # Travel time (driver → warehouse) + loading overhead
        pickup_minutes = (nearest_wh_dist / driver_zone_speed) * 60 + _LOADING_TIME_MINUTES

        available_drivers.append(
            DriverOption(
                driver_id=drv["id"],
                name=drv["name"],
                vehicle_type=drv["vehicle_type"],
                current_lat=drv["lat"],
                current_lon=drv["lon"],
                distance_to_nearest_wh_km=round(nearest_wh_dist, 2),
                estimated_pickup_minutes=round(pickup_minutes, 1),
                current_load_kg=drv["current_load_kg"],
                max_load_kg=drv["max_load_kg"],
                available_capacity_kg=round(capacity_remaining, 1),
                active_deliveries=drv["active_deliveries"],
                rating=drv["rating"],
                zone_familiarity=drv["zone_familiarity"],
            )
        )

    available_drivers.sort(key=lambda d: d.estimated_pickup_minutes)

    # ── Zone profile ───────────────────────────────────────────────────────────

    zone_profile = ZoneProfile(
        zone_id=zone_raw["id"],
        name=zone_raw["name"],
        delivery_success_rate=zone_raw["delivery_success_rate"],
        avg_transit_hours=zone_raw["avg_transit_hours"],
        demand_pressure=zone_raw["demand_pressure"],
        active_routes=zone_raw["active_routes"],
        complaint_rate=zone_raw["complaint_rate"],
        last_30_days_total=zone_raw["last_30_days"]["total_deliveries"],
        last_30_days_successful=zone_raw["last_30_days"]["successful"],
    )

    return FeatureVector(
        order_id=order.order_id,
        destination_lat=order.destination_lat,
        destination_lon=order.destination_lon,
        destination_zone_id=zone_id,
        order_value=order.order_value,
        weight_kg=order.weight_kg,
        time_window_hours=order.time_window_hours,
        cargo_type=order.cargo_type,
        priority=order.priority,
        warehouse_options=warehouse_options,
        available_drivers=available_drivers,
        zone_profile=zone_profile,
        enrichment_timestamp=datetime.now(timezone.utc).isoformat(),
        erp_latency_ms=round(erp_latency_ms, 1),
    )
