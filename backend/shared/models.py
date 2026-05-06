"""Shared Pydantic models used across all agent services."""
from typing import Optional
from pydantic import BaseModel


# ── Input ─────────────────────────────────────────────────────────────────────

class OrderRequest(BaseModel):
    order_id: str
    destination_lat: float
    destination_lon: float
    order_value: float           # GBP
    weight_kg: float
    time_window_hours: float     # delivery deadline from now
    cargo_type: str = "general"  # general | fragile | refrigerated | hazardous
    priority: str = "standard"   # standard | urgent | critical
    scenario: Optional[str] = None


# ── Intake Agent output sub-types ─────────────────────────────────────────────

class WarehouseOption(BaseModel):
    warehouse_id: str
    name: str
    lat: float
    lon: float
    distance_to_destination_km: float
    stock_level: int       # units of the requested cargo_type
    stock_confirmed: bool


class DriverOption(BaseModel):
    driver_id: str
    name: str
    vehicle_type: str      # van | motorbike | truck
    current_lat: float
    current_lon: float
    distance_to_nearest_wh_km: float
    estimated_pickup_minutes: float
    current_load_kg: float
    max_load_kg: float
    available_capacity_kg: float
    active_deliveries: int
    rating: float
    zone_familiarity: list[str]


class ZoneProfile(BaseModel):
    zone_id: str
    name: str
    delivery_success_rate: float   # 0–1
    avg_transit_hours: float
    demand_pressure: float         # 0–1, higher = more congested
    active_routes: int
    complaint_rate: float          # 0–1
    last_30_days_total: int
    last_30_days_successful: int


# ── Intake Agent primary output ────────────────────────────────────────────────

class FeatureVector(BaseModel):
    order_id: str
    destination_lat: float
    destination_lon: float
    destination_zone_id: str
    order_value: float
    weight_kg: float
    time_window_hours: float
    cargo_type: str
    priority: str
    warehouse_options: list[WarehouseOption]   # all warehouses, sorted by distance
    available_drivers: list[DriverOption]       # filtered + sorted by ETA
    zone_profile: ZoneProfile
    enrichment_timestamp: str
    erp_latency_ms: float


# ── Optimizer Agent output ────────────────────────────────────────────────────

class RoutingOption(BaseModel):
    option_id: str          # "{warehouse_id}::{driver_id}"
    warehouse_id: str
    driver_id: str
    timeliness_score: float
    cost_efficiency_score: float
    warehouse_proximity_score: float
    zone_risk_penalty: float
    composite_score: float
    estimated_cost_gbp: float
    estimated_duration_hours: float


class OptimizerOutput(BaseModel):
    order_id: str
    ranked_options: list[RoutingOption]
    top_choice: RoutingOption
    weights_used: dict


# ── Reasoner Agent output ─────────────────────────────────────────────────────

class ReasonerOutput(BaseModel):
    order_id: str
    conclusion: str                # confirm | qualify | override
    recommended_option_id: str
    chain_of_thought: str
    flagged_risks: list[str]
    override_reason: Optional[str] = None


# ── Resolution Layer output ───────────────────────────────────────────────────

class ResolutionResult(BaseModel):
    order_id: str
    state: str              # convergence | qualification | override
    final_option_id: str
    optimizer_choice: str
    reasoner_choice: str
    explanation: str
