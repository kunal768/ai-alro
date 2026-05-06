import { useEffect, useRef } from 'react';

function lookupNames(featureVector, warehouseId, driverId) {
  const wh = featureVector?.warehouse_options?.find(w => w.warehouse_id === warehouseId);
  const drv = featureVector?.available_drivers?.find(d => d.driver_id === driverId);
  return {
    warehouseName: wh?.name ?? warehouseId,
    driverName: drv?.name ?? driverId,
    vehicleType: drv?.vehicle_type ?? '',
  };
}

function getAgreementState(reasonerText, reasonerConclusion) {
  if (reasonerConclusion) {
    const map = { confirm: 'confirmed', qualify: 'qualified', override: 'overridden' };
    return map[reasonerConclusion.decision] ?? 'neutral';
  }
  if (!reasonerText || reasonerText.length < 100) return 'neutral';
  const lower = reasonerText.toLowerCase();
  const divergeWords = ['however', 'must flag', 'concern', 'bias', 'inequit', 'deprivat', 'problematic', 'override', 'inequitable'];
  const convergeWords = ['clear choice', 'confirm', 'correct', 'optimal', 'appropriate', 'best'];
  const dCount = divergeWords.filter(w => lower.includes(w)).length;
  const cCount = convergeWords.filter(w => lower.includes(w)).length;
  if (dCount >= 2 && dCount > cCount) return 'diverging';
  if (cCount > dCount) return 'converging';
  return 'neutral';
}

const AGREEMENT_TEXT = {
  neutral:    'TRACKING',
  converging: 'CONVER-\nGING',
  diverging:  'DIVER-\nGING',
  confirmed:  'CONFIR-\nMED',
  qualified:  'QUALIF-\nIED',
  overridden: 'OVER-\nRIDE',
};

function OptimizerPanel({ optimizerOutput, featureVector }) {
  const { ranked_options, top_choice, weights_used } = optimizerOutput;
  const w1 = weights_used?.w1_timeliness ?? 0.4;
  const w2 = weights_used?.w2_cost_efficiency ?? 0.35;
  const w3 = weights_used?.w3_warehouse_proximity ?? 0.25;

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-agent">
          <div className="panel-agent-name optimizer">Optimizer</div>
          <div className="panel-agent-role">Quantitative Voice</div>
        </div>
        <div className="label-caps mono" style={{ color: 'var(--text-muted)', fontSize: '9px' }}>
          w₁={w1} w₂={w2} w₃={w3}
        </div>
      </div>
      <div className="panel-body">
        {ranked_options.map((opt, idx) => {
          const isTop = opt.option_id === top_choice.option_id;
          const { warehouseName, driverName, vehicleType } = lookupNames(featureVector, opt.warehouse_id, opt.driver_id);
          return (
            <div key={opt.option_id} className={`routing-option ${isTop ? 'top-choice' : ''}`}>
              <div className="routing-option-header">
                <div className="routing-option-meta">
                  <div className="routing-option-id">{opt.option_id}</div>
                  <div className="routing-option-names">
                    {warehouseName} · {driverName}
                    {vehicleType && <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}> ({vehicleType})</span>}
                  </div>
                </div>
                {isTop && <div className="routing-option-badge">TOP CHOICE</div>}
              </div>

              <div className="composite-score">
                <span className="composite-score-value">{opt.composite_score.toFixed(3)}</span>
                <span className="composite-score-label">COMPOSITE</span>
              </div>

              <div className="score-decomp">
                {[
                  { label: `TIME ×${w1}`, val: opt.timeliness_score, cls: 'timeliness', weighted: opt.timeliness_score * w1 },
                  { label: `COST ×${w2}`, val: opt.cost_efficiency_score, cls: 'cost', weighted: opt.cost_efficiency_score * w2 },
                  { label: `PROX ×${w3}`, val: opt.warehouse_proximity_score, cls: 'proximity', weighted: opt.warehouse_proximity_score * w3 },
                ].map(item => (
                  <div key={item.label} className="score-row">
                    <div className="score-row-label">{item.label}</div>
                    <div className="score-bar-track">
                      <div
                        className={`score-bar-fill ${item.cls}`}
                        style={{ width: `${item.val * 100}%` }}
                      />
                    </div>
                    <div className="score-row-value">{item.weighted.toFixed(3)}</div>
                  </div>
                ))}
                <div className="score-row">
                  <div className="score-row-label" style={{ color: 'var(--red)' }}>ZONE RISK</div>
                  <div className="score-bar-track">
                    <div
                      className="score-bar-fill risk"
                      style={{ width: `${opt.zone_risk_penalty * 100}%` }}
                    />
                  </div>
                  <div className="score-row-value" style={{ color: 'var(--red)' }}>
                    −{opt.zone_risk_penalty.toFixed(3)}
                  </div>
                </div>
              </div>

              <div className="routing-option-footer">
                <div className="routing-meta-item">
                  <div className="routing-meta-label">Est. Cost</div>
                  <div className="routing-meta-value">£{opt.estimated_cost_gbp.toFixed(2)}</div>
                </div>
                <div className="routing-meta-item">
                  <div className="routing-meta-label">Est. Duration</div>
                  <div className="routing-meta-value">{opt.estimated_duration_hours.toFixed(1)}h</div>
                </div>
                {idx === 0 && (
                  <div className="routing-meta-item" style={{ marginLeft: 'auto' }}>
                    <div className="routing-meta-label">Rank</div>
                    <div className="routing-meta-value" style={{ color: 'var(--blue)' }}>#{idx + 1}</div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AgreementIndicator({ reasonerText, reasonerConclusion }) {
  const state = getAgreementState(reasonerText, reasonerConclusion);
  const words = AGREEMENT_TEXT[state] ?? 'TRACKING';

  return (
    <div className="agreement-strip">
      <div className={`agreement-badge state-${state}`}>
        <div className="agreement-title">AGREE-{'\n'}MENT</div>
        <div className="agreement-dot" />
        <div className="agreement-word">{words}</div>
      </div>
    </div>
  );
}

function ReasonerPanel({ reasonerText, reasonerConclusion, isStreaming }) {
  const bodyRef = useRef(null);

  const conclusionStart = reasonerText.indexOf('<conclusion>');
  const displayText = conclusionStart >= 0
    ? reasonerText.slice(0, conclusionStart).trimEnd()
    : reasonerText;

  const paragraphs = displayText.split(/\n\n+/).filter(Boolean);

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [displayText]);

  const conclusionDecision = reasonerConclusion?.decision;

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-agent">
          <div className="panel-agent-name reasoner">Reasoner</div>
          <div className="panel-agent-role">Deliberative Voice</div>
        </div>
        {isStreaming && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div className="phase1-spinner" style={{ borderTopColor: 'var(--purple)' }} />
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Streaming</span>
          </div>
        )}
      </div>
      <div className="panel-body" ref={bodyRef}>
        {paragraphs.length === 0 && isStreaming && (
          <div className="reasoner-waiting">
            <div className="phase1-spinner" style={{ borderTopColor: 'var(--purple)' }} />
            Initiating chain of thought…
          </div>
        )}
        <div className="reasoner-text">
          {paragraphs.map((para, i) => (
            <p key={i}>
              {para}
              {isStreaming && i === paragraphs.length - 1 && (
                <span className="reasoner-cursor" />
              )}
            </p>
          ))}
        </div>

        {conclusionDecision && (
          <div className={`conclusion-chip ${conclusionDecision}`}>
            {conclusionDecision === 'confirm'  && '✓ CONFIRMED'}
            {conclusionDecision === 'qualify'  && '⚠ QUALIFIED'}
            {conclusionDecision === 'override' && '✕ OVERRIDE'}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Phase2_Deliberation({
  optimizerOutput,
  featureVector,
  reasonerText,
  reasonerConclusion,
  isStreaming,
}) {
  return (
    <div className="phase2-container">
      <OptimizerPanel optimizerOutput={optimizerOutput} featureVector={featureVector} />
      <AgreementIndicator reasonerText={reasonerText} reasonerConclusion={reasonerConclusion} />
      <ReasonerPanel
        reasonerText={reasonerText}
        reasonerConclusion={reasonerConclusion}
        isStreaming={isStreaming}
      />
    </div>
  );
}
