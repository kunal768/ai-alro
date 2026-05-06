"""
Resolution Layer — compares Optimizer and Reasoner conclusions.

Three output states:
  convergence   — both agents agree, no significant flags raised
  qualification — Reasoner confirms the choice but surfaces a risk the operator must see
  override      — Reasoner recommends a different routing option
"""
from shared.models import OptimizerOutput, ReasonerOutput, ResolutionResult


def resolve(optimizer: OptimizerOutput, reasoner: ReasonerOutput) -> ResolutionResult:
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

    if conclusion == "confirm" and opt_choice == rea_choice:
        state = "convergence"
        explanation = (
            f"Both agents agree: [{opt_choice}] is the correct routing choice. "
            "No material risks identified. Decision confirmed with joint attribution."
        )

    elif conclusion == "qualify":
        state = "qualification"
        if reasoner.flagged_risks:
            risk_summary = "; ".join(reasoner.flagged_risks)
            explanation = (
                f"Optimizer recommends [{opt_choice}]. "
                f"Reasoner confirms this choice but flags the following "
                f"condition(s) for operator review: {risk_summary}."
            )
        else:
            explanation = (
                f"Optimizer recommends [{opt_choice}]. "
                "Reasoner confirms but has surfaced a condition — see reasoning chain."
            )

    elif conclusion == "override" or (opt_choice != rea_choice):
        state = "override"
        reason = (
            reasoner.override_reason
            or "Reasoner assessed an alternative option as more appropriate — see reasoning chain."
        )
        explanation = (
            f"DIVERGENCE DETECTED. "
            f"Optimizer chose [{opt_choice}]; Reasoner recommends [{rea_choice}]. "
            f"Override reason: {reason}"
        )

    else:
        # Fallback: treat unexpected states as convergence on the Reasoner's pick
        state = "convergence"
        explanation = (
            f"Agents reach the same recommendation: [{rea_choice}]."
        )

    return ResolutionResult(
        order_id=optimizer.order_id,
        state=state,
        final_option_id=rea_choice,
        optimizer_choice=opt_choice,
        reasoner_choice=rea_choice,
        explanation=explanation,
    )
