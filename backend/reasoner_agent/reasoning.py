"""
Streaming orchestration for the Reasoner Agent.

run_reasoning() is an async generator that yields SSE-ready event dicts.
Each dict has the shape {"event": str, "data": str} where data is a JSON string.

Event sequence:
  token*      — one per LLM chunk, carries partial text
  conclusion  — parsed structured conclusion (decision, flags, override_reason)
  resolution  — final resolution state (convergence | qualification | override)
  error       — LLM unavailable; includes fallback decision (degraded mode)
  done        — stream complete; safe to close the SSE connection
"""
import json
import re
from typing import AsyncIterator

from shared.models import OptimizerOutput, ReasonerOutput, ResolutionResult
from reasoner_agent.providers import stream_llm
from reasoner_agent.prompts import SYSTEM_PROMPT, build_user_prompt
from reasoner_agent.resolution import resolve


# ── Conclusion parser ──────────────────────────────────────────────────────────

def _parse_conclusion(full_text: str, fallback_option_id: str) -> dict:
    """
    Extract the structured <conclusion> block from the LLM's output.

    Robust to minor formatting variations: missing block, extra whitespace,
    NONE in various casings, extra punctuation on field values.
    """
    block_match = re.search(
        r"<conclusion>(.*?)</conclusion>", full_text, re.DOTALL | re.IGNORECASE
    )
    block = block_match.group(1) if block_match else full_text

    # DECISION
    dec_match = re.search(r"DECISION:\s*(confirm|qualify|override)", block, re.IGNORECASE)
    decision = dec_match.group(1).lower() if dec_match else "qualify"

    # RECOMMENDED_OPTION
    opt_match = re.search(r"RECOMMENDED_OPTION:\s*(\S+)", block)
    raw_opt = opt_match.group(1).strip("`[]()") if opt_match else ""
    recommended_option = raw_opt if raw_opt and raw_opt.upper() not in ("NONE", "") else fallback_option_id

    # FLAGS — may be comma-separated on one line or NONE
    flags_match = re.search(r"FLAGS:\s*(.+?)(?:\n|$)", block)
    if flags_match:
        flags_raw = flags_match.group(1).strip()
        if re.match(r"^NONE[.\s]*$", flags_raw, re.IGNORECASE):
            flags: list[str] = []
        else:
            flags = [
                f.strip().strip(",`")
                for f in re.split(r"[,\n]", flags_raw)
                if f.strip() and not re.match(r"^NONE[.\s]*$", f.strip(), re.IGNORECASE)
            ]
    else:
        flags = []

    # OVERRIDE_REASON — may span to end of block
    reason_match = re.search(
        r"OVERRIDE_REASON:\s*(.+?)(?:</conclusion>|\Z)", block, re.DOTALL
    )
    if reason_match:
        reason_raw = reason_match.group(1).strip()
        override_reason = (
            None if re.match(r"^NONE[.\s]*$", reason_raw, re.IGNORECASE) else reason_raw
        )
    else:
        override_reason = None

    return {
        "decision": decision,
        "recommended_option": recommended_option,
        "flags": flags,
        "override_reason": override_reason,
        "parse_ok": bool(block_match),
    }


# ── SSE event helpers ──────────────────────────────────────────────────────────

def _evt(event: str, payload: dict) -> dict:
    return {"event": event, "data": json.dumps(payload)}


# ── Main streaming generator ───────────────────────────────────────────────────

async def run_reasoning(
    feature_vector: dict,
    optimizer_output: OptimizerOutput,
) -> AsyncIterator[dict]:
    """
    Stream the full reasoning + resolution pipeline as SSE-ready event dicts.

    Degraded-mode behaviour: if the LLM call fails, an error event is emitted,
    the resolution defaults to the Optimizer's top choice, and the stream ends
    cleanly so the frontend can surface the degraded state.
    """
    system = SYSTEM_PROMPT
    user = build_user_prompt(feature_vector, optimizer_output.model_dump())
    fallback_id = optimizer_output.top_choice.option_id

    full_text = ""

    # ── Stream LLM tokens ──────────────────────────────────────────────────────
    try:
        async for chunk in stream_llm(system, user):
            full_text += chunk
            yield _evt("token", {"type": "token", "text": chunk})

    except Exception as exc:
        # Degraded mode: surface the failure, fall back to Optimizer choice
        yield _evt("error", {
            "type": "error",
            "message": f"Reasoning layer unavailable: {exc}",
            "fallback": "Proceeding on Optimizer output alone — no chain of thought available.",
        })
        degraded_resolution = ResolutionResult(
            order_id=optimizer_output.order_id,
            state="convergence",
            final_option_id=fallback_id,
            optimizer_choice=fallback_id,
            reasoner_choice=fallback_id,
            explanation=(
                "Reasoner Agent unavailable. "
                "Decision defaults to Optimizer recommendation without deliberation."
            ),
        )
        yield _evt("resolution", {"type": "resolution", **degraded_resolution.model_dump()})
        yield _evt("done", {"type": "done"})
        return

    # ── Parse conclusion ───────────────────────────────────────────────────────
    parsed = _parse_conclusion(full_text, fallback_id)

    reasoner_output = ReasonerOutput(
        order_id=optimizer_output.order_id,
        conclusion=parsed["decision"],
        recommended_option_id=parsed["recommended_option"],
        chain_of_thought=full_text,
        flagged_risks=parsed["flags"],
        override_reason=parsed["override_reason"],
    )

    yield _evt("conclusion", {
        "type": "conclusion",
        "decision": parsed["decision"],
        "recommended_option": parsed["recommended_option"],
        "flags": parsed["flags"],
        "override_reason": parsed["override_reason"],
        "parse_ok": parsed["parse_ok"],
    })

    # ── Resolution Layer ───────────────────────────────────────────────────────
    resolution = resolve(optimizer_output, reasoner_output, feature_vector)

    yield _evt("resolution", {"type": "resolution", **resolution.model_dump()})
    yield _evt("done", {"type": "done"})
