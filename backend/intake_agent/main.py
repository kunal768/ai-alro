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


@app.post("/enrich")
async def enrich(order: OrderRequest):
    """
    Enrich a raw order with ERP data and return a FeatureVector.

    The FeatureVector is the shared context consumed by both the Optimizer
    and Reasoner agents downstream.
    """
    try:
        feature_vector = await enrich_order(order, ERP_URL)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ERP enrichment failed: {exc}",
        ) from exc

    return {"order_id": order.order_id, "feature_vector": feature_vector.model_dump()}
