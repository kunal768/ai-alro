"""
Resolution Layer — compares Optimizer and Reasoner conclusions.

Three output states:
  convergence   — both agents agree, no significant flags raised
  qualification — Reasoner confirms the choice but surfaces a risk the operator must see
  override      — Reasoner recommends a different routing option
"""
from __future__ import annotations
from shared.models import OptimizerOutput, ReasonerOutput, ResolutionResult


def _lookup_names(feature_vector: dict | None, option_id: str) -> tuple[str, str]:
    """Return (warehouse_label, driver_label) for an option_id like 'WH-SF01::DRV-001'."""
    if not option_id or "::" not in option_id:
        return option_id or "unknown", ""
    wh_id, drv_id = option_id.split("::", 1)
    fv = feature_vector or {}
    wh_name = next(
        (w["name"] for w in fv.get("warehouse_options", []) if w.get("warehouse_id") == wh_id),
        None,
    )
    drv_name = next(
        (d["name"] for d in fv.get("available_drivers", []) if d.get("driver_id") == drv_id),
        None,
    )
    wh_label = wh_name if wh_name else f"Warehouse {wh_id}"
    drv_label = drv_name if drv_name else f"Driver {drv_id}"
    return wh_label, drv_label


def resolve(
    optimizer: OptimizerOutput,
    reasoner: ReasonerOutput,
    feature_vector: dict | None = None,
) -> ResolutionResult:
    """
    Compare the Optimizer's top choice with the Reasoner's conclusion and
    return a ResolutionResult with the final decision state.

    The final_option_id is always the Reasoner's recommendation — the Reasoner
    has the last word. In convergence, this matches the Optimizer's choice.
    In override, it differs and the explanation names both sides of the divergence.
    """
    opt_choice = optimizer.top_choice.option_id
    rea_choice = reasoner.recommended_option_id
    conclusion = reasoner.conclusion.lower().strip()

    opt_wh, opt_drv = _lookup_names(feature_vector, opt_choice)
    rea_wh, rea_drv = _lookup_names(feature_vector, rea_choice)

    if conclusion == "confirm" and opt_choice == rea_choice:
        state = "convergence"
        explanation = (
            f"Both systems agree: route from {opt_wh} with {opt_drv} is the correct choice. "
            "No material risks identified. Decision confirmed with joint attribution."
        )

    elif conclusion == "qualify":
        state = "qualification"
        if reasoner.flagged_risks:
            risk_summary = "; ".join(reasoner.flagged_risks)
            explanation = (
                f"The optimizer recommends {opt_wh} with {opt_drv}. "
                f"The reasoner confirms this route but flags the following "
                f"condition(s) for operator review: {risk_summary}."
            )
        else:
            explanation = (
                f"The optimizer recommends {opt_wh} with {opt_drv}. "
                "The reasoner confirms this route but has surfaced a condition — see reasoning chain."
            )

    elif conclusion == "override" or (opt_choice != rea_choice):
        state = "override"
        reason = (
            reasoner.override_reason
            or "The reasoner assessed an alternative route as more appropriate — see reasoning chain."
        )
        explanation = (
            f"The optimizer preferred {opt_wh} with {opt_drv}, "
            f"but the reasoner recommends {rea_wh} with {rea_drv}. "
            f"Override reason: {reason}"
        )

    else:
        state = "convergence"
        explanation = (
            f"Both systems reach the same recommendation: {rea_wh} with {rea_drv}."
        )

    return ResolutionResult(
        order_id=optimizer.order_id,
        state=state,
        final_option_id=rea_choice,
        optimizer_choice=opt_choice,
        reasoner_choice=rea_choice,
        explanation=explanation,
    )
