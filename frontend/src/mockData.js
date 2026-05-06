export const MOCK_DATA = {
  convergence: {
    featureVector: {
      order_id: 'ORD-2024-001',
      destination_lat: 37.7880,
      destination_lon: -122.4074,
      destination_zone_id: 'central_sf',
      order_value: 1250.00,
      weight_kg: 8.5,
      time_window_hours: 6,
      cargo_type: 'fragile',
      priority: 'urgent',
      warehouse_options: [
        {
          warehouse_id: 'WH-SF01',
          name: 'SF Mission Fulfillment',
          lat: 37.7599,
          lon: -122.4148,
          distance_to_destination_km: 3.1,
          stock_level: 48,
          stock_confirmed: true,
        },
        {
          warehouse_id: 'WH-OAK01',
          name: 'Oakland Harbor Distribution',
          lat: 37.8044,
          lon: -122.2712,
          distance_to_destination_km: 14.5,
          stock_level: 22,
          stock_confirmed: true,
        },
      ],
      available_drivers: [
        {
          driver_id: 'DRV-001',
          name: 'Marcus Johnson',
          vehicle_type: 'van',
          current_lat: 37.7920,
          current_lon: -122.3985,
          distance_to_nearest_wh_km: 2.1,
          estimated_pickup_minutes: 12.0,
          current_load_kg: 0,
          max_load_kg: 500,
          available_capacity_kg: 500,
          active_deliveries: 0,
          rating: 4.9,
          zone_familiarity: ['central_sf', 'soma_mission', 'east_bay'],
        },
        {
          driver_id: 'DRV-002',
          name: 'Aisha Patel',
          vehicle_type: 'van',
          current_lat: 37.7588,
          current_lon: -122.4148,
          distance_to_nearest_wh_km: 6.4,
          estimated_pickup_minutes: 28.0,
          current_load_kg: 120,
          max_load_kg: 500,
          available_capacity_kg: 380,
          active_deliveries: 1,
          rating: 4.7,
          zone_familiarity: ['central_sf', 'soma_mission', 'peninsula'],
        },
      ],
      zone_profile: {
        zone_id: 'central_sf',
        name: 'SF Financial District / Union Square',
        delivery_success_rate: 0.960,
        avg_transit_hours: 1.2,
        demand_pressure: 0.91,
        active_routes: 38,
        complaint_rate: 0.021,
        last_30_days_total: 2104,
        last_30_days_successful: 2020,
      },
      enrichment_timestamp: '2024-03-15T14:32:18Z',
      erp_latency_ms: 138.4,
    },
    optimizerOutput: {
      order_id: 'ORD-2024-001',
      ranked_options: [
        {
          option_id: 'WH-SF01::DRV-001',
          warehouse_id: 'WH-SF01',
          driver_id: 'DRV-001',
          timeliness_score: 0.91,
          cost_efficiency_score: 0.83,
          proximity_score: 0.95,
          zone_risk_penalty: 0.018,
          composite_score: 0.889,
          estimated_cost_gbp: 45.20,
          estimated_duration_hours: 1.4,
        },
        {
          option_id: 'WH-OAK01::DRV-002',
          warehouse_id: 'WH-OAK01',
          driver_id: 'DRV-002',
          timeliness_score: 0.72,
          cost_efficiency_score: 0.88,
          proximity_score: 0.62,
          zone_risk_penalty: 0.018,
          composite_score: 0.742,
          estimated_cost_gbp: 52.80,
          estimated_duration_hours: 2.1,
        },
      ],
      top_choice: {
        option_id: 'WH-SF01::DRV-001',
        warehouse_id: 'WH-SF01',
        driver_id: 'DRV-001',
        timeliness_score: 0.91,
        cost_efficiency_score: 0.83,
        proximity_score: 0.95,
        zone_risk_penalty: 0.018,
        composite_score: 0.889,
        estimated_cost_gbp: 45.20,
        estimated_duration_hours: 1.4,
      },
      weights_used: { w1_timeliness: 0.4, w2_cost_efficiency: 0.35, w3_proximity: 0.25 },
    },
    reasonerStream: {
      text: `## SIGNAL ANALYSIS

The Optimizer's top choice WH-SF01::DRV-001 earns its rank primarily through warehouse proximity (0.95 × 0.25 = 0.238) and timeliness (0.91 × 0.40 = 0.364). The SF Mission Fulfillment Center at 3.1 km is the natural anchor for Union Square deliveries. The cost efficiency score of 0.83 reflects a reasonable $45.20 estimate for a standard van delivery. The emphasis on proximity is appropriate here — a nearby warehouse eliminates pickup lag for urgent fragile cargo.

## BORDERLINE CHECK

The composite gap between Rank 1 (0.889) and Rank 2 (0.742) is 0.147 — a decisive margin that is not competitive. No plausible single-variable perturbation would reverse this ranking. Even a 20-minute traffic delay would not close a gap of this magnitude.

## GEOGRAPHIC FAIRNESS

The destination zone, SF Financial District / Union Square, shows a delivery success rate of 96.0% and a complaint rate of just 2.1%. Both figures are well above threshold. This is a well-served, high-demand zone with 38 active routes. No redlining concern exists here.

## STRUCTURAL BLIND SPOTS

Driver Marcus Johnson lists central_sf in his zone familiarity — the destination zone. His 12-minute estimated pickup time and zero active deliveries mean no reliability risk. The cargo is standard goods with no special handling requirement.

## CONCLUSION

The Optimizer's recommendation is sound. No material risk or fairness concern applies to this routing decision.

<conclusion>
DECISION: confirm
RECOMMENDED_OPTION: WH-SF01::DRV-001
FLAGS: NONE
OVERRIDE_REASON: NONE
</conclusion>`,
      conclusion: {
        decision: 'confirm',
        recommended_option: 'WH-SF01::DRV-001',
        flags: [],
        override_reason: null,
      },
      resolution: {
        order_id: 'ORD-2024-001',
        state: 'convergence',
        final_option_id: 'WH-SF01::DRV-001',
        optimizer_choice: 'WH-SF01::DRV-001',
        reasoner_choice: 'WH-SF01::DRV-001',
        explanation: 'Both agents agree: [WH-SF01::DRV-001] is the correct routing choice. No material risks identified. Decision confirmed with joint attribution.',
      },
    },
  },

  qualification: {
    featureVector: {
      order_id: 'ORD-2024-002',
      destination_lat: 37.7752,
      destination_lon: -122.2237,
      destination_zone_id: 'outer_east',
      order_value: 3400.00,
      weight_kg: 22.0,
      time_window_hours: 12,
      cargo_type: 'general',
      priority: 'standard',
      warehouse_options: [
        {
          warehouse_id: 'WH-OAK01',
          name: 'Oakland Harbor Distribution',
          lat: 37.8044,
          lon: -122.2712,
          distance_to_destination_km: 4.8,
          stock_level: 200,
          stock_confirmed: true,
        },
        {
          warehouse_id: 'WH-SF01',
          name: 'SF Mission Fulfillment',
          lat: 37.7599,
          lon: -122.4148,
          distance_to_destination_km: 18.2,
          stock_level: 35,
          stock_confirmed: true,
        },
      ],
      available_drivers: [
        {
          driver_id: 'DRV-009',
          name: 'Amara Okonkwo',
          vehicle_type: 'van',
          current_lat: 37.8305,
          current_lon: -122.2441,
          distance_to_nearest_wh_km: 3.8,
          estimated_pickup_minutes: 22.0,
          current_load_kg: 0,
          max_load_kg: 600,
          available_capacity_kg: 600,
          active_deliveries: 0,
          rating: 4.3,
          zone_familiarity: ['east_bay', 'north_bay', 'outer_east'],
        },
        {
          driver_id: 'DRV-007',
          name: 'Diego Morales',
          vehicle_type: 'van',
          current_lat: 37.6688,
          current_lon: -122.0808,
          distance_to_nearest_wh_km: 5.1,
          estimated_pickup_minutes: 31.0,
          current_load_kg: 140,
          max_load_kg: 500,
          available_capacity_kg: 360,
          active_deliveries: 2,
          rating: 4.4,
          zone_familiarity: ['south_bay', 'outer_east'],
        },
      ],
      zone_profile: {
        zone_id: 'outer_east',
        name: 'Outer East (Hayward / Fremont)',
        delivery_success_rate: 0.721,
        avg_transit_hours: 2.8,
        demand_pressure: 0.44,
        active_routes: 11,
        complaint_rate: 0.112,
        last_30_days_total: 590,
        last_30_days_successful: 425,
      },
      enrichment_timestamp: '2024-03-15T14:35:42Z',
      erp_latency_ms: 162.3,
    },
    optimizerOutput: {
      order_id: 'ORD-2024-002',
      ranked_options: [
        {
          option_id: 'WH-OAK01::DRV-009',
          warehouse_id: 'WH-OAK01',
          driver_id: 'DRV-009',
          timeliness_score: 0.78,
          cost_efficiency_score: 0.85,
          proximity_score: 0.71,
          zone_risk_penalty: 0.14,
          composite_score: 0.781,
          estimated_cost_gbp: 88.40,
          estimated_duration_hours: 3.2,
        },
        {
          option_id: 'WH-OAK01::DRV-007',
          warehouse_id: 'WH-OAK01',
          driver_id: 'DRV-007',
          timeliness_score: 0.71,
          cost_efficiency_score: 0.80,
          proximity_score: 0.71,
          zone_risk_penalty: 0.14,
          composite_score: 0.742,
          estimated_cost_gbp: 96.60,
          estimated_duration_hours: 3.8,
        },
      ],
      top_choice: {
        option_id: 'WH-OAK01::DRV-009',
        warehouse_id: 'WH-OAK01',
        driver_id: 'DRV-009',
        timeliness_score: 0.78,
        cost_efficiency_score: 0.85,
        proximity_score: 0.71,
        zone_risk_penalty: 0.14,
        composite_score: 0.781,
        estimated_cost_gbp: 88.40,
        estimated_duration_hours: 3.2,
      },
      weights_used: { w1_timeliness: 0.4, w2_cost_efficiency: 0.35, w3_proximity: 0.25 },
    },
    reasonerStream: {
      text: `## SIGNAL ANALYSIS

The Optimizer selects WH-OAK01::DRV-009 with a composite score of 0.781, driven by a strong cost efficiency signal of 0.85 and adequate timeliness for the 12-hour delivery window. Oakland Harbor is the only viable warehouse — SF Mission is 18.2 km from Fruitvale. Driver Okonkwo's 22-minute pickup time fits within the schedule.

## BORDERLINE CHECK

The composite gap between Rank 1 (0.781) and Rank 2 (0.742) is 0.039 — a narrow margin. A significant traffic incident or loading delay could challenge this gap. However, both options route through the same warehouse (WH-OAK01), so the ranking difference is purely driver-driven. The gap is worth noting but not decisive on its own.

## GEOGRAPHIC FAIRNESS

The destination zone, Outer East (Hayward / Fremont), shows a delivery success rate of only 72.1%. In the last 30 days, 165 of 590 delivery attempts in this zone failed — a 27.9% failure rate. This is significantly below the 80% operational threshold that should trigger enhanced handling protocols. The complaint rate at 11.2% is also elevated.

The routing decision itself is correct given available options. But proceeding without surfacing this risk to the operator would be inappropriate.

## STRUCTURAL BLIND SPOTS

Driver Okonkwo lists outer_east in her zone familiarity — a positive signal. However, her active delivery count of zero and high historical load suggest recent route resets may affect local knowledge. The 11 active routes with 2.8-hour average transit creates real congestion risk for a 3.2-hour estimated duration, threatening the 12-hour window for a $3,400 order.

## CONCLUSION

I confirm the Optimizer's choice but require this risk be escalated to the dispatch team before commitment.

<conclusion>
DECISION: qualify
RECOMMENDED_OPTION: WH-OAK01::DRV-009
FLAGS: Zone delivery success rate 72.1% is below the 80% operational threshold, High zone complaint rate 11.2% warrants enhanced handling protocol, Borderline composite gap of 0.039 between Rank 1 and Rank 2
OVERRIDE_REASON: NONE
</conclusion>`,
      conclusion: {
        decision: 'qualify',
        recommended_option: 'WH-OAK01::DRV-009',
        flags: [
          'Zone delivery success rate 72.1% is below the 80% operational threshold',
          'High zone complaint rate 11.2% warrants enhanced handling protocol',
          'Borderline composite gap of 0.039 between Rank 1 and Rank 2',
        ],
        override_reason: null,
      },
      resolution: {
        order_id: 'ORD-2024-002',
        state: 'qualification',
        final_option_id: 'WH-OAK01::DRV-009',
        optimizer_choice: 'WH-OAK01::DRV-009',
        reasoner_choice: 'WH-OAK01::DRV-009',
        explanation: 'Optimizer recommends [WH-OAK01::DRV-009]. Reasoner confirms this choice but flags the following condition(s) for operator review: Zone delivery success rate 72.1% is below the 80% operational threshold; High zone complaint rate 11.2% warrants enhanced handling protocol; Borderline composite gap of 0.039 between Rank 1 and Rank 2.',
      },
    },
  },

  override: {
    featureVector: {
      order_id: 'ORD-2024-003',
      destination_lat: 37.6688,
      destination_lon: -122.0808,
      destination_zone_id: 'outer_east',
      order_value: 890.00,
      weight_kg: 45.0,
      time_window_hours: 24,
      cargo_type: 'general',
      priority: 'standard',
      warehouse_options: [
        {
          warehouse_id: 'WH-OAK01',
          name: 'Oakland Harbor Distribution',
          lat: 37.8044,
          lon: -122.2712,
          distance_to_destination_km: 12.6,
          stock_level: 500,
          stock_confirmed: true,
        },
        {
          warehouse_id: 'WH-SF01',
          name: 'SF Mission Fulfillment',
          lat: 37.7599,
          lon: -122.4148,
          distance_to_destination_km: 22.1,
          stock_level: 320,
          stock_confirmed: true,
        },
      ],
      available_drivers: [
        {
          driver_id: 'DRV-001',
          name: 'Marcus Johnson',
          vehicle_type: 'van',
          current_lat: 37.7920,
          current_lon: -122.3985,
          distance_to_nearest_wh_km: 8.3,
          estimated_pickup_minutes: 18.0,
          current_load_kg: 0,
          max_load_kg: 500,
          available_capacity_kg: 500,
          active_deliveries: 0,
          rating: 4.9,
          zone_familiarity: ['central_sf', 'soma_mission', 'east_bay'],
        },
        {
          driver_id: 'DRV-009',
          name: 'Amara Okonkwo',
          vehicle_type: 'van',
          current_lat: 37.8305,
          current_lon: -122.2441,
          distance_to_nearest_wh_km: 4.1,
          estimated_pickup_minutes: 26.0,
          current_load_kg: 80,
          max_load_kg: 600,
          available_capacity_kg: 520,
          active_deliveries: 1,
          rating: 4.3,
          zone_familiarity: ['east_bay', 'north_bay', 'outer_east'],
        },
      ],
      zone_profile: {
        zone_id: 'outer_east',
        name: 'Outer East (Hayward / Fremont)',
        delivery_success_rate: 0.830,
        avg_transit_hours: 2.1,
        demand_pressure: 0.45,
        active_routes: 12,
        complaint_rate: 0.140,
        last_30_days_total: 94,
        last_30_days_successful: 78,
      },
      enrichment_timestamp: '2024-03-15T14:38:55Z',
      erp_latency_ms: 149.7,
    },
    optimizerOutput: {
      order_id: 'ORD-2024-003',
      ranked_options: [
        {
          option_id: 'WH-OAK01::DRV-001',
          warehouse_id: 'WH-OAK01',
          driver_id: 'DRV-001',
          timeliness_score: 0.82,
          cost_efficiency_score: 0.91,
          proximity_score: 0.87,
          zone_risk_penalty: 0.11,
          composite_score: 0.868,
          estimated_cost_gbp: 78.40,
          estimated_duration_hours: 2.8,
        },
        {
          option_id: 'WH-OAK01::DRV-009',
          warehouse_id: 'WH-OAK01',
          driver_id: 'DRV-009',
          timeliness_score: 0.74,
          cost_efficiency_score: 0.80,
          proximity_score: 0.87,
          zone_risk_penalty: 0.11,
          composite_score: 0.773,
          estimated_cost_gbp: 86.50,
          estimated_duration_hours: 3.1,
        },
      ],
      top_choice: {
        option_id: 'WH-OAK01::DRV-001',
        warehouse_id: 'WH-OAK01',
        driver_id: 'DRV-001',
        timeliness_score: 0.82,
        cost_efficiency_score: 0.91,
        proximity_score: 0.87,
        zone_risk_penalty: 0.11,
        composite_score: 0.868,
        estimated_cost_gbp: 78.40,
        estimated_duration_hours: 2.8,
      },
      weights_used: { w1_timeliness: 0.4, w2_cost_efficiency: 0.35, w3_proximity: 0.25 },
    },
    reasonerStream: {
      text: `## SIGNAL ANALYSIS

The Optimizer favors WH-OAK01::DRV-001 with a composite score of 0.868, primarily on the strength of cost efficiency (0.91) and warehouse proximity (0.87). The $8.10 cost advantage over the alternative is real. Option A is objectively cheaper and faster on every quantitative measure.

## BORDERLINE CHECK

The composite gap between Rank 1 (0.868) and Rank 2 (0.773) is 0.095 — above the 0.08 scrutiny threshold. On its face, this appears decisive. However, the gap is entirely driven by the cost efficiency differential, not by any timeliness or zone-specific capability. I must look beyond the score.

## GEOGRAPHIC FAIRNESS

The destination zone, Outer East (Hayward / Fremont), has a delivery success rate of 83.0% and a complaint rate of 14.0% — both well below acceptable thresholds. The zone is chronically underserved. Routing the cheapest available option into this zone without regard for driver familiarity compounds the existing service deficit.

## STRUCTURAL BLIND SPOTS

Driver Marcus Johnson's zone_familiarity field lists central_sf, soma_mission, and east_bay — but not outer_east. Hayward is the destination zone. WH-OAK01::DRV-009 routes through a driver, Amara Okonkwo, with explicit outer_east zone familiarity. The $8.10 cost differential does not justify assigning a driver unfamiliar with a high-complaint-rate zone to that zone.

The pattern I am identifying is geographic service deprivation by proxy. No policy excludes outer_east. No human operator made this choice. But the reward function's cost preference systematically assigns outer_east deliveries to the cheapest option — which is not the most appropriate driver for this zone. The compounding effect will degrade the already-poor 83% success rate.

## CONCLUSION

I recommend WH-OAK01::DRV-009.

<conclusion>
DECISION: override
RECOMMENDED_OPTION: WH-OAK01::DRV-009
FLAGS: Systematic zone routing bias detected — outer_east assigned non-specialist drivers via cost optimization, Driver Marcus Johnson has no outer_east familiarity despite 14% zone complaint rate
OVERRIDE_REASON: Zone outer_east has a 14% complaint rate and 83% delivery success rate. Assigning Driver Johnson (no outer_east familiarity) over Driver Okonkwo (explicit outer_east familiarity) for an $8.10 cost saving perpetuates a structural routing bias that will progressively degrade service quality in an already underserved zone.
</conclusion>`,
      conclusion: {
        decision: 'override',
        recommended_option: 'WH-OAK01::DRV-009',
        flags: [
          'Systematic zone routing bias detected — outer_east assigned non-specialist drivers via cost optimization',
          'Driver Marcus Johnson has no outer_east familiarity despite 14% zone complaint rate',
        ],
        override_reason: 'Zone outer_east has a 14% complaint rate and 83% delivery success rate. Assigning Driver Johnson (no outer_east familiarity) over Driver Okonkwo (explicit outer_east familiarity) for an $8.10 cost saving perpetuates a structural routing bias that will progressively degrade service quality in an already underserved zone.',
      },
      resolution: {
        order_id: 'ORD-2024-003',
        state: 'override',
        final_option_id: 'WH-OAK01::DRV-009',
        optimizer_choice: 'WH-OAK01::DRV-001',
        reasoner_choice: 'WH-OAK01::DRV-009',
        explanation: 'DIVERGENCE DETECTED. Optimizer chose [WH-OAK01::DRV-001]; Reasoner recommends [WH-OAK01::DRV-009]. Override reason: Zone outer_east has a 14% complaint rate and 83% delivery success rate. Assigning Driver Johnson (no outer_east familiarity) over Driver Okonkwo (explicit outer_east familiarity) for an $8.10 cost saving perpetuates a structural routing bias that will progressively degrade service quality in an already underserved zone.',
      },
    },
  },
};
