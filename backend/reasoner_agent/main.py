"""
Reasoner Agent — Port 8004

Receives the Optimizer's ranked output plus the Intake Agent's feature vector.
Streams a chain-of-thought deliberation token-by-token via Server-Sent Events,
then emits a final resolution state (convergence | qualification | override).

SSE event sequence:
  token*     — partial LLM text (streams in real time, one per chunk)
  conclusion — parsed structured decision (decision, flags, override_reason)
  resolution — final state with full attribution
  error      — LLM unavailable; degraded fallback to Optimizer choice
  done       — stream complete
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from shared.models import OptimizerOutput
from reasoner_agent.reasoning import run_reasoning
from reasoner_agent.providers import provider_summary

app = FastAPI(title="Reasoner Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReasonerRequest(BaseModel):
    feature_vector: dict      # FeatureVector serialised as dict from the Intake Agent
    optimizer_output: OptimizerOutput


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    ps = provider_summary()
    return {
        "status": "ok",
        "service": "reasoner_agent",
        "llm_provider": ps["provider"],
        "llm_model": ps["model"],
    }


@app.post("/reason")
async def reason(request: ReasonerRequest):
    """
    Stream the Reasoner's deliberation as Server-Sent Events.

    The client should consume the stream until it receives an event of
    type 'done'. The 'resolution' event (emitted just before 'done')
    contains the final decision state.
    """
    async def generator():
        async for event in run_reasoning(request.feature_vector, request.optimizer_output):
            yield event

    return EventSourceResponse(generator())
