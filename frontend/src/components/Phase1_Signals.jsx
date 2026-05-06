import { capitalizePriority, formatCurrencyUSD } from '../utils/formatters.js';

function extractSignals(fv) {
  const wh = fv.warehouse_options?.[0];
  const drv = fv.available_drivers?.[0];
  const zone = fv.zone_profile;

  const whDist = wh?.distance_to_destination_km ?? 0;
  const maxDist = 20;
  const proximityVal = Math.max(0, Math.min(1, 1 - whDist / maxDist));

  const etaMin = drv?.estimated_pickup_minutes ?? 60;
  const etaVal = Math.max(0, Math.min(1, 1 - etaMin / 90));

  const zoneVal = zone?.delivery_success_rate ?? 0;
  const demandVal = 1 - (zone?.demand_pressure ?? 0);

  const twHours = fv.time_window_hours ?? 12;
  const twVal = Math.min(1, twHours / 24);

  const priorityMap = { critical: 1.0, urgent: 0.85, standard: 0.5 };
  const priorityVal = priorityMap[fv.priority] ?? 0.5;

  const orderVal = Math.min(1, (fv.order_value ?? 0) / 5000);

  const activeRoutes = zone?.active_routes ?? 0;

  return [
    {
      key: 'proximity',
      label: 'Warehouse Proximity',
      value: proximityVal,
      display: wh ? `${whDist} km · ${wh.name}` : '—',
      category: proximityVal > 0.6 ? 'positive' : proximityVal > 0.3 ? 'neutral' : 'risk',
    },
    {
      key: 'stock',
      label: 'Stock Confirmed',
      value: wh?.stock_confirmed ? 1.0 : 0.0,
      display: wh?.stock_confirmed ? `${wh.stock_level} units available` : 'NO STOCK',
      category: wh?.stock_confirmed ? 'positive' : 'risk',
    },
    {
      key: 'eta',
      label: 'Driver ETA',
      value: etaVal,
      display: drv ? `${drv.estimated_pickup_minutes} min · ${drv.name}` : '—',
      category: etaMin < 20 ? 'positive' : etaMin < 45 ? 'neutral' : 'risk',
    },
    {
      key: 'zone_reliability',
      label: 'Zone Reliability',
      value: zoneVal,
      display: zone ? `${(zoneVal * 100).toFixed(1)}% · ${zone.name}` : '—',
      category: zoneVal >= 0.85 ? 'positive' : zoneVal >= 0.75 ? 'neutral' : 'risk',
    },
    {
      key: 'demand',
      label: 'Demand Pressure',
      value: demandVal,
      display: zone
        ? `${zone.demand_pressure >= 0.7 ? 'HIGH' : zone.demand_pressure >= 0.4 ? 'MODERATE' : 'LOW'} · ${activeRoutes} active routes`
        : '—',
      category: zone?.demand_pressure >= 0.7 ? 'risk' : 'neutral',
    },
    {
      key: 'time_window',
      label: 'Time Window',
      value: twVal,
      display: `${twHours}h delivery window`,
      category: 'neutral',
    },
    {
      key: 'priority',
      label: 'Order Priority',
      value: priorityVal,
      display: capitalizePriority(fv.priority ?? 'standard'),
      category: fv.priority === 'urgent' || fv.priority === 'critical' ? 'risk' : 'neutral',
    },
    {
      key: 'order_value',
      label: 'Order Value',
      value: orderVal,
      display: formatCurrencyUSD(fv.order_value ?? 0),
      category: 'neutral',
    },
  ];
}

export default function Phase1_Signals({ featureVector, signalRevealCount, phase }) {
  if (!featureVector) {
    return (
      <div className="phase1-container">
        <div className="phase1-header">
          <div className="phase1-title">
            <div className="phase1-agent-label">Intake Agent</div>
            <div className="phase1-order-desc">Connecting to ERP service…</div>
          </div>
          <div className="phase1-status">
            <div className="phase1-spinner" />
            Enriching
          </div>
        </div>
      </div>
    );
  }

  const signals = extractSignals(featureVector);

  return (
    <div className="phase1-container">
      <div className="phase1-header">
        <div className="phase1-title">
          <div className="phase1-agent-label">Intake Agent — Signal Population</div>
          <div className="phase1-order-desc">
            <strong>{featureVector.order_id}</strong>
            {' · '}
            {featureVector.cargo_type}
            {' · '}
            {capitalizePriority(featureVector.priority)}
            {' · '}
            {featureVector.time_window_hours}h window
          </div>
        </div>
        {signalRevealCount < signals.length && (
          <div className="phase1-status">
            <div className="phase1-spinner" />
            Enriching
          </div>
        )}
      </div>

      <div className="signals-list">
        {signals.map((sig, i) => {
          const revealed = signalRevealCount > i;
          return (
            <div key={sig.key} className={`signal-row ${revealed ? 'visible' : ''}`}>
              <div className="signal-label">{sig.label}</div>
              <div className="signal-bar-track">
                <div
                  className={`signal-bar-fill cat-${sig.category} ${revealed ? 'revealed' : ''}`}
                  style={{ '--target-width': `${sig.value * 100}%` }}
                />
              </div>
              <div className={`signal-value cat-${sig.category}`}>{sig.display}</div>
            </div>
          );
        })}
      </div>

      {phase === 'intake' && signalRevealCount >= signals.length && (
        <div className="phase1-advance">
          <div className="phase1-advance-dot" />
          Advancing to deliberation…
        </div>
      )}
    </div>
  );
}
