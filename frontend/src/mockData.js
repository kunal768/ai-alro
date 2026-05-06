export const MOCK_DATA = {
  convergence: {
    featureVector: {
      order_id: 'ORD-2024-001',
      destination_lat: 51.5074,
      destination_lon: -0.1278,
      destination_zone_id: 'ZONE-C1',
      order_value: 1250.00,
      weight_kg: 8.5,
      time_window_hours: 6,
      cargo_type: 'fragile',
      priority: 'urgent',
      warehouse_options: [
        {
          warehouse_id: 'WH-NORTH',
          name: 'Warehouse North',
          lat: 51.5524,
          lon: -0.1108,
          distance_to_destination_km: 4.2,
          stock_level: 48,
          stock_confirmed: true,
        },
        {
          warehouse_id: 'WH-EAST',
          name: 'Warehouse East',
          lat: 51.5081,
          lon: -0.0759,
          distance_to_destination_km: 11.8,
          stock_level: 12,
          stock_confirmed: true,
        },
      ],
      available_drivers: [
        {
          driver_id: 'DRV-001',
          name: 'James Chen',
          vehicle_type: 'van',
          current_lat: 51.5420,
          current_lon: -0.1200,
          distance_to_nearest_wh_km: 2.1,
          estimated_pickup_minutes: 12.0,
          current_load_kg: 0,
          max_load_kg: 800,
          available_capacity_kg: 800,
          active_deliveries: 0,
          rating: 4.9,
          zone_familiarity: ['ZONE-C1', 'ZONE-N1'],
        },
        {
          driver_id: 'DRV-003',
          name: 'Sara Okonkwo',
          vehicle_type: 'van',
          current_lat: 51.4980,
          current_lon: -0.1050,
          distance_to_nearest_wh_km: 6.4,
          estimated_pickup_minutes: 28.0,
          current_load_kg: 120,
          max_load_kg: 800,
          available_capacity_kg: 680,
          active_deliveries: 1,
          rating: 4.7,
          zone_familiarity: ['ZONE-C1', 'ZONE-E1'],
        },
      ],
      zone_profile: {
        zone_id: 'ZONE-C1',
        name: 'Central London',
        delivery_success_rate: 0.942,
        avg_transit_hours: 1.8,
        demand_pressure: 0.35,
        active_routes: 8,
        complaint_rate: 0.021,
        last_30_days_total: 284,
        last_30_days_successful: 267,
      },
      enrichment_timestamp: '2024-03-15T14:32:18Z',
      erp_latency_ms: 142.3,
    },
    optimizerOutput: {
      order_id: 'ORD-2024-001',
      ranked_options: [
        {
          option_id: 'WH-NORTH::DRV-001',
          warehouse_id: 'WH-NORTH',
          driver_id: 'DRV-001',
          timeliness_score: 0.91,
          cost_efficiency_score: 0.82,
          warehouse_proximity_score: 0.95,
          zone_risk_penalty: 0.06,
          composite_score: 0.889,
          estimated_cost_gbp: 124.50,
          estimated_duration_hours: 1.4,
        },
        {
          option_id: 'WH-EAST::DRV-003',
          warehouse_id: 'WH-EAST',
          driver_id: 'DRV-003',
          timeliness_score: 0.71,
          cost_efficiency_score: 0.88,
          warehouse_proximity_score: 0.62,
          zone_risk_penalty: 0.06,
          composite_score: 0.742,
          estimated_cost_gbp: 142.80,
          estimated_duration_hours: 2.3,
        },
      ],
      top_choice: {
        option_id: 'WH-NORTH::DRV-001',
        warehouse_id: 'WH-NORTH',
        driver_id: 'DRV-001',
        timeliness_score: 0.91,
        cost_efficiency_score: 0.82,
        warehouse_proximity_score: 0.95,
        zone_risk_penalty: 0.06,
        composite_score: 0.889,
        estimated_cost_gbp: 124.50,
        estimated_duration_hours: 1.4,
      },
      weights_used: { w1_timeliness: 0.4, w2_cost_efficiency: 0.35, w3_warehouse_proximity: 0.25 },
    },
    reasonerStream: {
      text: `The Optimizer's top-ranked option WH-NORTH::DRV-001 is the clear choice in this scenario. Warehouse North at 4.2 km offers the strongest proximity advantage, and Driver Chen's 12-minute estimated pickup time is comfortably within the 6-hour delivery window for these urgent fragile goods.

The timeliness signal scores 0.91 — reflecting both the short pickup window and the low zone transit time of 1.8 hours average. The proximity score of 0.95 dominates the warehouse selection. The cost differential of £18.30 against Option B does not represent a meaningful trade-off against this time advantage given the urgent priority classification.

Zone Central London presents no operational risk. The 94.2% delivery success rate is well above threshold. Active routes are low at 8, and demand pressure is moderate at 0.35. No congestion or reliability concerns apply here.

I find no fairness or zone equity concerns. This is a well-served central zone with consistent delivery outcomes. Both signals and scores are clean.

I confirm the Optimizer's recommendation without qualification.

<conclusion>
DECISION: confirm
RECOMMENDED_OPTION: WH-NORTH::DRV-001
FLAGS: NONE
OVERRIDE_REASON: NONE
</conclusion>`,
      conclusion: {
        decision: 'confirm',
        recommended_option: 'WH-NORTH::DRV-001',
        flags: [],
        override_reason: null,
      },
      resolution: {
        order_id: 'ORD-2024-001',
        state: 'convergence',
        final_option_id: 'WH-NORTH::DRV-001',
        optimizer_choice: 'WH-NORTH::DRV-001',
        reasoner_choice: 'WH-NORTH::DRV-001',
        explanation: 'Both agents agree: [WH-NORTH::DRV-001] is the correct routing choice. No material risks identified. Decision confirmed with joint attribution.',
      },
    },
  },

  qualification: {
    featureVector: {
      order_id: 'ORD-2024-002',
      destination_lat: 51.4861,
      destination_lon: -0.1420,
      destination_zone_id: 'ZONE-S2',
      order_value: 3400.00,
      weight_kg: 22.0,
      time_window_hours: 12,
      cargo_type: 'general',
      priority: 'standard',
      warehouse_options: [
        {
          warehouse_id: 'WH-EAST',
          name: 'Warehouse East',
          lat: 51.5081,
          lon: -0.0759,
          distance_to_destination_km: 7.3,
          stock_level: 200,
          stock_confirmed: true,
        },
        {
          warehouse_id: 'WH-SOUTH',
          name: 'Warehouse South',
          lat: 51.4420,
          lon: -0.1180,
          distance_to_destination_km: 5.2,
          stock_level: 0,
          stock_confirmed: false,
        },
      ],
      available_drivers: [
        {
          driver_id: 'DRV-003',
          name: 'Sara Okonkwo',
          vehicle_type: 'van',
          current_lat: 51.5100,
          current_lon: -0.0900,
          distance_to_nearest_wh_km: 3.8,
          estimated_pickup_minutes: 22.0,
          current_load_kg: 0,
          max_load_kg: 800,
          available_capacity_kg: 800,
          active_deliveries: 0,
          rating: 4.7,
          zone_familiarity: ['ZONE-S2', 'ZONE-E1'],
        },
        {
          driver_id: 'DRV-007',
          name: 'Marcus Webb',
          vehicle_type: 'truck',
          current_lat: 51.4700,
          current_lon: -0.1300,
          distance_to_nearest_wh_km: 5.1,
          estimated_pickup_minutes: 31.0,
          current_load_kg: 200,
          max_load_kg: 2000,
          available_capacity_kg: 1800,
          active_deliveries: 2,
          rating: 4.5,
          zone_familiarity: ['ZONE-S2'],
        },
      ],
      zone_profile: {
        zone_id: 'ZONE-S2',
        name: 'South London SW4',
        delivery_success_rate: 0.721,
        avg_transit_hours: 2.4,
        demand_pressure: 0.74,
        active_routes: 23,
        complaint_rate: 0.112,
        last_30_days_total: 113,
        last_30_days_successful: 81,
      },
      enrichment_timestamp: '2024-03-15T14:35:42Z',
      erp_latency_ms: 168.7,
    },
    optimizerOutput: {
      order_id: 'ORD-2024-002',
      ranked_options: [
        {
          option_id: 'WH-EAST::DRV-003',
          warehouse_id: 'WH-EAST',
          driver_id: 'DRV-003',
          timeliness_score: 0.78,
          cost_efficiency_score: 0.84,
          warehouse_proximity_score: 0.71,
          zone_risk_penalty: 0.14,
          composite_score: 0.781,
          estimated_cost_gbp: 198.40,
          estimated_duration_hours: 3.2,
        },
        {
          option_id: 'WH-EAST::DRV-007',
          warehouse_id: 'WH-EAST',
          driver_id: 'DRV-007',
          timeliness_score: 0.71,
          cost_efficiency_score: 0.79,
          warehouse_proximity_score: 0.71,
          zone_risk_penalty: 0.14,
          composite_score: 0.742,
          estimated_cost_gbp: 221.60,
          estimated_duration_hours: 3.8,
        },
      ],
      top_choice: {
        option_id: 'WH-EAST::DRV-003',
        warehouse_id: 'WH-EAST',
        driver_id: 'DRV-003',
        timeliness_score: 0.78,
        cost_efficiency_score: 0.84,
        warehouse_proximity_score: 0.71,
        zone_risk_penalty: 0.14,
        composite_score: 0.781,
        estimated_cost_gbp: 198.40,
        estimated_duration_hours: 3.2,
      },
      weights_used: { w1_timeliness: 0.4, w2_cost_efficiency: 0.35, w3_warehouse_proximity: 0.25 },
    },
    reasonerStream: {
      text: `The Optimizer selects WH-EAST::DRV-003 with a composite score of 0.781, driven by a strong cost efficiency signal of 0.84 and adequate timeliness for the 12-hour delivery window. Warehouse East is the only viable option — Warehouse South carries zero stock. Driver Okonkwo's 22-minute pickup time fits within the schedule.

However, I must flag a material operational concern that the reward function cannot fully encode.

The destination zone, South London SW4, shows a delivery success rate of only 72.1%. In the last 30 days, 32 of 113 delivery attempts in this zone failed — a 27.9% failure rate. This is significantly below the 80% operational threshold that should trigger enhanced handling protocols. The zone's complaint rate at 11.2% is also notably elevated.

The demand pressure of 0.74 and 23 active routes indicate the zone is operating near congestion capacity. The average transit time of 2.4 hours, combined with high route load, creates real risk that the 3.2-hour estimated duration extends significantly in practice — potentially threatening the 12-hour window for a £3,400 order.

The routing decision itself is correct given available options. But proceeding without surfacing this risk to the operator would be inappropriate.

I confirm the Optimizer's choice but require this risk be escalated to the dispatch team before commitment.

<conclusion>
DECISION: qualify
RECOMMENDED_OPTION: WH-EAST::DRV-003
FLAGS: Zone delivery success rate 72.1% is below the 80% operational threshold, High demand pressure (0.74) and 23 active routes create congestion risk, Complaint rate 11.2% warrants enhanced handling protocol
OVERRIDE_REASON: NONE
</conclusion>`,
      conclusion: {
        decision: 'qualify',
        recommended_option: 'WH-EAST::DRV-003',
        flags: [
          'Zone delivery success rate 72.1% is below the 80% operational threshold',
          'High demand pressure (0.74) and 23 active routes create congestion risk',
          'Complaint rate 11.2% warrants enhanced handling protocol',
        ],
        override_reason: null,
      },
      resolution: {
        order_id: 'ORD-2024-002',
        state: 'qualification',
        final_option_id: 'WH-EAST::DRV-003',
        optimizer_choice: 'WH-EAST::DRV-003',
        reasoner_choice: 'WH-EAST::DRV-003',
        explanation: 'Optimizer recommends [WH-EAST::DRV-003]. Reasoner confirms this choice but flags the following condition(s) for operator review: Zone delivery success rate 72.1% is below the 80% operational threshold; High demand pressure (0.74) and 23 active routes create congestion risk; Complaint rate 11.2% warrants enhanced handling protocol.',
      },
    },
  },

  override: {
    featureVector: {
      order_id: 'ORD-2024-003',
      destination_lat: 51.4571,
      destination_lon: -0.1157,
      destination_zone_id: 'ZONE-SW9',
      order_value: 890.00,
      weight_kg: 45.0,
      time_window_hours: 24,
      cargo_type: 'general',
      priority: 'standard',
      warehouse_options: [
        {
          warehouse_id: 'WH-SOUTH',
          name: 'Warehouse South',
          lat: 51.4420,
          lon: -0.1180,
          distance_to_destination_km: 5.1,
          stock_level: 500,
          stock_confirmed: true,
        },
        {
          warehouse_id: 'WH-WEST',
          name: 'Warehouse West',
          lat: 51.4992,
          lon: -0.1875,
          distance_to_destination_km: 8.7,
          stock_level: 320,
          stock_confirmed: true,
        },
      ],
      available_drivers: [
        {
          driver_id: 'DRV-005',
          name: 'Priya Sharma',
          vehicle_type: 'truck',
          current_lat: 51.4380,
          current_lon: -0.1100,
          distance_to_nearest_wh_km: 2.3,
          estimated_pickup_minutes: 18.0,
          current_load_kg: 0,
          max_load_kg: 2000,
          available_capacity_kg: 2000,
          active_deliveries: 0,
          rating: 4.8,
          zone_familiarity: ['ZONE-SW7', 'ZONE-SW8'],
        },
        {
          driver_id: 'DRV-002',
          name: 'Tom Fielding',
          vehicle_type: 'truck',
          current_lat: 51.5100,
          current_lon: -0.1700,
          distance_to_nearest_wh_km: 4.1,
          estimated_pickup_minutes: 26.0,
          current_load_kg: 80,
          max_load_kg: 2000,
          available_capacity_kg: 1920,
          active_deliveries: 1,
          rating: 4.6,
          zone_familiarity: ['ZONE-SW9', 'ZONE-W1'],
        },
      ],
      zone_profile: {
        zone_id: 'ZONE-SW9',
        name: 'South West London SW9',
        delivery_success_rate: 0.883,
        avg_transit_hours: 2.1,
        demand_pressure: 0.45,
        active_routes: 12,
        complaint_rate: 0.034,
        last_30_days_total: 94,
        last_30_days_successful: 83,
      },
      enrichment_timestamp: '2024-03-15T14:38:55Z',
      erp_latency_ms: 155.1,
    },
    optimizerOutput: {
      order_id: 'ORD-2024-003',
      ranked_options: [
        {
          option_id: 'WH-SOUTH::DRV-005',
          warehouse_id: 'WH-SOUTH',
          driver_id: 'DRV-005',
          timeliness_score: 0.82,
          cost_efficiency_score: 0.91,
          warehouse_proximity_score: 0.87,
          zone_risk_penalty: 0.11,
          composite_score: 0.868,
          estimated_cost_gbp: 134.50,
          estimated_duration_hours: 2.8,
        },
        {
          option_id: 'WH-WEST::DRV-002',
          warehouse_id: 'WH-WEST',
          driver_id: 'DRV-002',
          timeliness_score: 0.74,
          cost_efficiency_score: 0.79,
          warehouse_proximity_score: 0.68,
          zone_risk_penalty: 0.11,
          composite_score: 0.751,
          estimated_cost_gbp: 151.80,
          estimated_duration_hours: 3.4,
        },
      ],
      top_choice: {
        option_id: 'WH-SOUTH::DRV-005',
        warehouse_id: 'WH-SOUTH',
        driver_id: 'DRV-005',
        timeliness_score: 0.82,
        cost_efficiency_score: 0.91,
        warehouse_proximity_score: 0.87,
        zone_risk_penalty: 0.11,
        composite_score: 0.868,
        estimated_cost_gbp: 134.50,
        estimated_duration_hours: 2.8,
      },
      weights_used: { w1_timeliness: 0.4, w2_cost_efficiency: 0.35, w3_warehouse_proximity: 0.25 },
    },
    reasonerStream: {
      text: `The Optimizer favours WH-SOUTH::DRV-005 with a composite score of 0.868, primarily on the strength of cost efficiency (0.91) and warehouse proximity (0.87). The £17.30 cost advantage over the alternative is real. Option A is objectively cheaper and faster on every quantitative measure.

However, I must examine what lies beneath this recommendation.

Driver Sharma's zone_familiarity field lists SW7 and SW8 exclusively — not SW9. Warehouse South's routing corridors serve SW7 and SW8 for bulk commodity orders. Zone SW9, where this order is destined, has been routed through the Warehouse South corridor in the last eight consecutive bulk decisions. Option B, WH-WEST::DRV-002, routes directly through a driver with explicit zone familiarity for SW9 and W1.

The pattern I am identifying is what responsible AI governance calls geographic service deprivation by proxy. No policy excludes SW9. No human operator made this choice. But the reward function's cost preference has systematically assigned SW9 bulk orders to a warehouse-driver combination not optimised for that zone. The compounding effect is that drivers without SW9 familiarity are repeatedly assigned to it — increasing latent delivery risk that does not yet appear in the zone's current 88.3% success rate, but will if this pattern continues uncorrected.

The £17.30 cost differential does not justify perpetuating a routing bias that will structurally degrade service quality in a specific geographic zone. This is precisely the scenario where the reward function's structural limitations must be overridden by explicit fairness consideration.

I recommend WH-WEST::DRV-002.

<conclusion>
DECISION: override
RECOMMENDED_OPTION: WH-WEST::DRV-002
FLAGS: Systematic zone routing bias detected — SW9 assigned non-specialist drivers in 8 consecutive bulk decisions, Cost optimisation creating geographic service deprivation by proxy
OVERRIDE_REASON: Zone SW9 has been assigned non-specialist routing in 8 consecutive bulk decisions via Warehouse South. The £17.30 cost advantage of Option A does not justify perpetuating a structural routing bias that will progressively degrade SW9 service quality. Equitable zone coverage takes precedence over marginal cost efficiency.
</conclusion>`,
      conclusion: {
        decision: 'override',
        recommended_option: 'WH-WEST::DRV-002',
        flags: [
          'Systematic zone routing bias detected — SW9 assigned non-specialist drivers in 8 consecutive bulk decisions',
          'Cost optimisation creating geographic service deprivation by proxy',
        ],
        override_reason: 'Zone SW9 has been assigned non-specialist routing in 8 consecutive bulk decisions via Warehouse South. The £17.30 cost advantage of Option A does not justify perpetuating a structural routing bias that will progressively degrade SW9 service quality. Equitable zone coverage takes precedence over marginal cost efficiency.',
      },
      resolution: {
        order_id: 'ORD-2024-003',
        state: 'override',
        final_option_id: 'WH-WEST::DRV-002',
        optimizer_choice: 'WH-SOUTH::DRV-005',
        reasoner_choice: 'WH-WEST::DRV-002',
        explanation: 'DIVERGENCE DETECTED. Optimizer chose [WH-SOUTH::DRV-005]; Reasoner recommends [WH-WEST::DRV-002]. Override reason: Zone SW9 has been assigned non-specialist routing in 8 consecutive bulk decisions via Warehouse South. The £17.30 cost advantage of Option A does not justify perpetuating a structural routing bias that will progressively degrade SW9 service quality. Equitable zone coverage takes precedence over marginal cost efficiency.',
      },
    },
  },
};
