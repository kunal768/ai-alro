"""
Reasoner Agent — Port 8004

Receives the Optimizer's ranked output plus the Intake Agent's feature vector.
Streams a chain-of-thought deliberation token-by-token via Server-Sent Events,
then emits a final resolution state (convergence | qualification | override).

SSE event sequence:
  token*        — partial LLM text (streams in real time, one per chunk)
  conclusion    — parsed structured decision (decision, flags, override_reason)
  resolution    — final state with full attribution
  error         — LLM unavailable; degraded fallback to Optimizer choice
  done          — stream complete

Demo endpoint SSE sequence (GET /demo/{scenario_id}):
  scenario_data — feature_vector + optimizer_output for the scenario (emitted first)
  token* / conclusion / resolution / error / done — identical to /reason
"""
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from shared.models import OptimizerOutput
from reasoner_agent.reasoning import run_reasoning
from reasoner_agent.providers import provider_summary
from reasoner_agent.demo_scenarios import DEMO_SCENARIOS, SCENARIO_METADATA

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


@app.get("/scenarios")
async def list_scenarios():
    """Return the catalog of available demonstration scenarios."""
    return {"scenarios": SCENARIO_METADATA}


@app.get("/demo/{scenario_id}")
async def demo_scenario(scenario_id: str):
    """
    Stream a full deliberation for a predefined demonstration scenario.

    The stream opens with a scenario_data event so the client can immediately
    populate Phase 1 (signal reveal) while the LLM reasoning begins. All
    subsequent events mirror the /reason endpoint sequence.
    """
    if scenario_id not in DEMO_SCENARIOS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown scenario: {scenario_id!r}. Valid: {list(DEMO_SCENARIOS)}",
        )

    entry = DEMO_SCENARIOS[scenario_id]
    fv = entry["feature_vector"]
    opt = OptimizerOutput(**entry["optimizer_output"])

    async def generator():
        # Emit the scenario payload first so the client can start Phase 1 animation
        # concurrently while the LLM reasoning stream begins below.
        yield {
            "event": "scenario_data",
            "data": json.dumps({
                "type": "scenario_data",
                "feature_vector": fv,
                "optimizer_output": opt.model_dump(),
            }),
        }
        async for event in run_reasoning(fv, opt):
            yield event

    return EventSourceResponse(generator())


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
