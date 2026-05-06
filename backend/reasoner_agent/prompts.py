"""
System prompt and user-prompt builder for the Reasoner Agent.

The system prompt defines the Reasoner's identity and the five reasoning areas
it must work through. The user prompt is built from the live feature vector
and optimizer output — it gives the LLM every number it needs to reason about.
"""

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are the Reasoner Agent in a two-agent logistics decision-making system.

Your counterpart, the Optimizer Agent, scores and ranks routing options using a \
weighted reward function:

  reward = (timeliness_score × w1)
         + (cost_efficiency_score × w2)
         + (warehouse_proximity_score × w3)
         − zone_risk_penalty

The Optimizer is fast, deterministic, and blind to anything its reward function \
cannot encode. Your role is to audit its top choice with genuine chain-of-thought \
deliberation — not to summarise the output, but to argue about it. Your reasoning \
streams live to a human operator who must decide whether to act.

Work through five areas, in order. Be specific about numbers.

## 1. SIGNAL ANALYSIS
Which score component is doing the most work in the Optimizer's top choice? \
Compute the weighted contributions (score × weight) and name the dominant one. \
Ask: is that emphasis appropriate for this cargo type, priority level, and time \
window? Name the dominant signal and assess whether the Optimizer is optimising \
for the right thing.

## 2. BORDERLINE CHECK
State the composite score gap between Rank 1 and Rank 2 explicitly. If the gap \
is less than 0.08, the ranking is competitive and deserves scrutiny. Would a \
plausible real-world variation — a 10-minute traffic delay, a vehicle issue, a \
loading dock queue — plausibly reverse the ranking? Name the dimension on which \
the two options are closest.

## 3. GEOGRAPHIC FAIRNESS CHECK
Inspect the destination zone's historical data: delivery success rate, complaint \
rate, demand pressure. A delivery success rate below 88% or a complaint rate \
above 10% signals a zone that may already be systematically underserved.

Ask: does the Optimizer's top choice do anything to improve outcomes in this \
zone — or does it route the most cost-efficient option into a zone with chronic \
poor performance? A system that consistently sends its cheapest option into \
low-success-rate zones is engaged in redlining by proxy: functionally \
discriminatory even when the intent is purely economic. Flag this concern \
explicitly if it applies. If the zone is healthy (success rate ≥ 88%, complaint \
rate ≤ 10%), state that clearly.

## 4. STRUCTURAL BLIND SPOTS
Identify factors the reward function structurally cannot encode. Consider each:

- Driver zone familiarity: Is the assigned driver familiar with the destination \
zone? An unfamiliar driver in a high-complaint-rate zone compounds existing risk.
- Time window feasibility: Add the estimated pickup ETA (minutes) to the zone's \
average transit time (hours). Does the total fall within the order's time window? \
If it is within 10 minutes of the deadline, call this out precisely.
- Driver reliability: Does the driver's active delivery count or current load \
create a reliability risk for this order?
- Cargo risk: Does the cargo type (fragile, refrigerated, hazardous) create \
additional risk given zone performance history or vehicle type?

## 5. CONCLUSION
State one of three decisions, using exactly these labels:

- CONFIRM — The Optimizer's top choice is sound. No material risk to surface.
- QUALIFY — The top choice is acceptable but a specific condition or risk must \
be surfaced to the operator. Name it in one or two sentences.
- OVERRIDE — The top choice is the wrong call. Name the alternative option_id \
from the ranked list and state the reason in one sentence.

After your reasoning, output your structured conclusion in this exact block. \
Do not omit or rename any field:

<conclusion>
DECISION: confirm|qualify|override
RECOMMENDED_OPTION: [option_id exactly as it appears in the ranked list]
FLAGS: [comma-separated risk flags, or NONE]
OVERRIDE_REASON: [one sentence if override, or NONE]
</conclusion>
"""


# ── User prompt builder ────────────────────────────────────────────────────────

def build_user_prompt(fv: dict, opt: dict) -> str:
    """
    Serialise a FeatureVector dict and OptimizerOutput dict into a structured
    text prompt the LLM can reason about.
    """
    zp = fv["zone_profile"]
    weights = opt["weights_used"]
    w1 = weights.get("w1_timeliness", 0.40)
    w2 = weights.get("w2_cost_efficiency", 0.35)
    w3 = weights.get("w3_warehouse_proximity", 0.25)

    lines: list[str] = [
        "=== ROUTING SCENARIO ===",
        "",
        f"Order ID    : {fv['order_id']}",
        f"Cargo       : {fv['cargo_type']}  |  "
        f"Weight: {fv['weight_kg']} kg  |  "
        f"Value: £{fv['order_value']:,.2f}  |  "
        f"Priority: {fv['priority']}",
        f"Time window : {fv['time_window_hours']} hours from dispatch",
        "",
        f"DESTINATION ZONE: {zp['zone_id']} — {zp['name']}",
        f"  Delivery success rate : {zp['delivery_success_rate'] * 100:.0f}%",
        f"  Average transit time  : {zp['avg_transit_hours']:.1f} hours",
        f"  Demand pressure       : {zp['demand_pressure'] * 100:.0f}%",
        f"  Complaint rate        : {zp['complaint_rate'] * 100:.0f}%",
        f"  Active routes         : {zp['active_routes']}",
        f"  Last 30 days          : {zp['last_30_days_total']} deliveries  |  "
        f"{zp['last_30_days_successful']} successful  |  "
        f"{zp['last_30_days_total'] - zp['last_30_days_successful']} failed",
        "",
        "=== OPTIMIZER OUTPUT ===",
        "",
        f"Reward weights: timeliness={w1}, cost={w2}, proximity={w3}",
        "",
    ]

    # Index driver and warehouse lookups from feature vector
    drivers_by_id = {d["driver_id"]: d for d in fv.get("available_drivers", [])}
    wh_by_id = {w["warehouse_id"]: w for w in fv.get("warehouse_options", [])}
    dest_zone = fv.get("destination_zone_id", "")

    for i, option in enumerate(opt["ranked_options"], 1):
        drv = drivers_by_id.get(option["driver_id"], {})
        wh = wh_by_id.get(option["warehouse_id"], {})

        familiar = drv.get("zone_familiarity", [])
        wh_dist = wh.get("distance_to_destination_km", "?")
        eta = drv.get("estimated_pickup_minutes", "?")
        rating = drv.get("rating", "?")
        vehicle = drv.get("vehicle_type", "?")
        active_del = drv.get("active_deliveries", "?")
        drv_name = drv.get("name", option["driver_id"])

        ts = option["timeliness_score"]
        cs = option["cost_efficiency_score"]
        ps = option["warehouse_proximity_score"]
        zpen = option["zone_risk_penalty"]

        label = "TOP CHOICE — " if i == 1 else ""
        lines += [
            f"RANK {i} — {label}[{option['option_id']}]",
            f"  Warehouse : {option['warehouse_id']} | {wh_dist} km to destination",
            f"  Driver    : {drv_name} ({vehicle}) | ETA ≈{eta} min | "
            f"★{rating} | active deliveries: {active_del}",
            f"  Zone familiarity: {', '.join(familiar) if familiar else 'not listed'}"
            + (" ← destination zone NOT in familiarity list" if dest_zone and dest_zone not in familiar else ""),
            "  Scores:",
            f"    Timeliness  : {ts:.3f} × {w1} = {ts * w1:.3f}",
            f"    Cost        : {cs:.3f} × {w2} = {cs * w2:.3f}",
            f"    Proximity   : {ps:.3f} × {w3} = {ps * w3:.3f}",
            f"    Zone penalty: −{zpen:.3f}",
            f"    COMPOSITE   : {option['composite_score']:.3f}",
            f"  Estimated cost: £{option['estimated_cost_gbp']:.2f}",
            f"  Estimated duration: {option['estimated_duration_hours']:.2f} h "
            f"(pickup ≈{eta} min + zone transit ≈{zp['avg_transit_hours']:.1f} h)",
            "",
        ]

    return "\n".join(lines)
