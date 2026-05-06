"""
Intake Agent — Port 8002

Receives a routing scenario, enriches it with ERP data, and emits a structured
FeatureVector that both the Optimizer and Reasoner agents consume.
"""
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from intake_agent.enrichment import enrich_order
from shared.models import OrderRequest
from shared.utils import validate_bay_area

ERP_URL = os.getenv("ERP_SERVICE_URL", "http://localhost:8001")

app = FastAPI(title="Intake Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "intake_agent", "erp_url": ERP_URL}


@app.get("/scenarios")
async def list_scenarios():
    """
    Return the catalog of predefined demonstration scenarios.

    Proxied from the Reasoner Agent's registry so the frontend has a single
    discovery endpoint behind the intake path.
    """
    import httpx
    reasoner_url = os.getenv("REASONER_AGENT_URL", "http://localhost:8004")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{reasoner_url}/scenarios")
            r.raise_for_status()
            return r.json()
    except Exception:
        # Return empty list rather than hard-failing; frontend has local fallback
        return {"scenarios": []}


@app.post("/enrich")
async def enrich(order: OrderRequest):
    """
    Enrich a raw order with ERP data and return a FeatureVector.

    The FeatureVector is the shared context consumed by both the Optimizer
    and Reasoner agents downstream.
    """
    valid, geo_error = validate_bay_area(order.destination_lat, order.destination_lon)
    if not valid:
        raise HTTPException(status_code=422, detail=geo_error)

    try:
        feature_vector = await enrich_order(order, ERP_URL)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ERP enrichment failed: {exc}",
        ) from exc

    return {"order_id": order.order_id, "feature_vector": feature_vector.model_dump()}
