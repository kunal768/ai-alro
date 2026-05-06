function lookupOption(featureVector, optionId) {
  if (!featureVector || !optionId) return null;
  const [warehouseId, driverId] = optionId.split('::');
  const wh = featureVector.warehouse_options?.find(w => w.warehouse_id === warehouseId);
  const drv = featureVector.available_drivers?.find(d => d.driver_id === driverId);
  return { wh, drv };
}

function AgentRow({ label, agentClass, choice, isMatch }) {
  return (
    <div className="resolution-agent-row">
      <div className={`resolution-agent-name ${agentClass}`}>{label}</div>
      <div className="resolution-agent-line" />
      <div className="resolution-agent-choice">
        <span className="mono" style={{ fontSize: 12 }}>{choice}</span>
        <div className={`resolution-agent-tick ${isMatch ? 'match' : 'differ'}`}>
          {isMatch ? '✓' : '✕'}
        </div>
      </div>
    </div>
  );
}

function ConvergenceCard({ resolution, featureVector, optimizerOutput }) {
  const finalOpt = lookupOption(featureVector, resolution.final_option_id);
  const routingOpt = optimizerOutput?.ranked_options?.find(o => o.option_id === resolution.final_option_id);

  return (
    <div className="resolution-card convergence">
      <div className="resolution-decision-block">
        <div className="resolution-decision-label">Final Route</div>
        <div className="resolution-decision-id mono">{resolution.final_option_id}</div>
        <div className="resolution-decision-meta">
          {finalOpt?.wh && <span>{finalOpt.wh.name}</span>}
          {finalOpt?.drv && <span>{finalOpt.drv.name} ({finalOpt.drv.vehicle_type})</span>}
          {routingOpt && (
            <>
              <span className="mono">${routingOpt.estimated_cost_gbp.toFixed(2)}</span>
              <span className="mono">~{routingOpt.estimated_duration_hours.toFixed(1)}h</span>
            </>
          )}
        </div>
      </div>

      <div className="resolution-agents-block">
        <AgentRow label="OPTIMIZER" agentClass="optimizer" choice={resolution.optimizer_choice} isMatch={true} />
        <AgentRow label="REASONER"  agentClass="reasoner"  choice={resolution.reasoner_choice}  isMatch={true} />
      </div>

      <div className="resolution-explanation">
        {resolution.explanation || 'Both checks agree this route is the safest and fastest balance.'}
      </div>
    </div>
  );
}

function QualificationCard({ resolution, featureVector, optimizerOutput, reasonerConclusion }) {
  const finalOpt = lookupOption(featureVector, resolution.final_option_id);
  const routingOpt = optimizerOutput?.ranked_options?.find(o => o.option_id === resolution.final_option_id);
  const flags = reasonerConclusion?.flags ?? [];

  return (
    <div className="resolution-card qualification">
      <div className="resolution-decision-block">
        <div className="resolution-decision-label">Final Route - Confirmed with Conditions</div>
        <div className="resolution-decision-id mono">{resolution.final_option_id}</div>
        <div className="resolution-decision-meta">
          {finalOpt?.wh && <span>{finalOpt.wh.name}</span>}
          {finalOpt?.drv && <span>{finalOpt.drv.name} ({finalOpt.drv.vehicle_type})</span>}
          {routingOpt && (
            <>
              <span className="mono">${routingOpt.estimated_cost_gbp.toFixed(2)}</span>
              <span className="mono">~{routingOpt.estimated_duration_hours.toFixed(1)}h</span>
            </>
          )}
        </div>
      </div>

      <div className="resolution-agents-block">
        <AgentRow label="OPTIMIZER" agentClass="optimizer" choice={resolution.optimizer_choice} isMatch={true} />
        <AgentRow label="REASONER"  agentClass="reasoner"  choice={resolution.reasoner_choice}  isMatch={true} />
      </div>

      {flags.length > 0 && (
        <div className="flags-block">
          <div className="flags-header">⚑ Watch Items</div>
          {flags.map((flag, i) => (
            <div key={i} className="flag-item">
              <div className="flag-bullet">!</div>
              <span>{flag}</span>
            </div>
          ))}
        </div>
      )}

      <div className="resolution-explanation">
        {resolution.explanation || 'This route is approved, but the flagged items need monitoring during execution.'}
      </div>
    </div>
  );
}

function OverrideCard({ resolution, featureVector, optimizerOutput, reasonerConclusion }) {
  const optOpt = lookupOption(featureVector, resolution.optimizer_choice);
  const reaOpt = lookupOption(featureVector, resolution.reasoner_choice);
  const optRouting = optimizerOutput?.ranked_options?.find(o => o.option_id === resolution.optimizer_choice);
  const reaRouting = optimizerOutput?.ranked_options?.find(o => o.option_id === resolution.reasoner_choice);
  const overrideReason = reasonerConclusion?.override_reason;
  const flags = reasonerConclusion?.flags ?? [];

  return (
    <div className="resolution-card override">
      <div className="override-comparison">
        <div className="override-side">
          <div className="override-side-label optimizer">Optimizer Recommendation</div>
          <div className="override-option-id mono">{resolution.optimizer_choice}</div>
          <div className="override-option-detail">
            {optOpt?.wh && <span>{optOpt.wh.name}</span>}
            {optOpt?.drv && <span>{optOpt.drv.name} ({optOpt.drv.vehicle_type})</span>}
            {optRouting && (
              <>
                <span className="mono">${optRouting.estimated_cost_gbp.toFixed(2)}</span>
                <span className="mono">~{optRouting.estimated_duration_hours.toFixed(1)}h · Score {optRouting.composite_score.toFixed(3)}</span>
              </>
            )}
          </div>
        </div>

        <div className="override-side">
          <div className="override-side-label reasoner">Reasoner Recommendation</div>
          <div className="override-option-id mono">{resolution.reasoner_choice}</div>
          <div className="override-option-detail">
            {reaOpt?.wh && <span>{reaOpt.wh.name}</span>}
            {reaOpt?.drv && <span>{reaOpt.drv.name} ({reaOpt.drv.vehicle_type})</span>}
            {reaRouting && (
              <>
                <span className="mono">${reaRouting.estimated_cost_gbp.toFixed(2)}</span>
                <span className="mono">~{reaRouting.estimated_duration_hours.toFixed(1)}h · Score {reaRouting.composite_score.toFixed(3)}</span>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="resolution-decision-block">
        <div className="resolution-decision-label">Final Route - Override Applied</div>
        <div className="resolution-decision-id mono">{resolution.final_option_id}</div>
        <div className="resolution-agents-block" style={{ padding: '12px 0 0', borderTop: 'none' }}>
          <AgentRow label="OPTIMIZER" agentClass="optimizer" choice={resolution.optimizer_choice} isMatch={false} />
          <AgentRow label="REASONER"  agentClass="reasoner"  choice={resolution.reasoner_choice}  isMatch={true} />
        </div>
      </div>

      {flags.length > 0 && (
        <div className="flags-block">
          <div className="flags-header">⚑ Risk Flags</div>
          {flags.map((flag, i) => (
            <div key={i} className="flag-item">
              <div className="flag-bullet">!</div>
              <span>{flag}</span>
            </div>
          ))}
        </div>
      )}

      {overrideReason && (
        <div className="override-reason-block">
          <div className="override-reason-label">Why We Overrode</div>
          <div className="override-reason-text">{overrideReason}</div>
        </div>
      )}
    </div>
  );
}

export default function Phase3_Resolution({
  resolution,
  featureVector,
  optimizerOutput,
  reasonerConclusion,
}) {
  if (!resolution) return null;

  const state = resolution.state;

  const iconMap = { convergence: '✓', qualification: '⚠', override: '✕' };
  const titleMap = { convergence: 'Convergence', qualification: 'Qualification', override: 'Override' };
  const subtitleMap = {
    convergence:   'Both agents agree on the same route.',
    qualification: 'Top route is approved, with conditions to watch.',
    override:      'A safer route replaced the optimizer suggestion.',
  };

  return (
    <div className="phase3-container">
      <div className="resolution-header">
        <div className={`resolution-icon ${state}`}>
          {iconMap[state]}
        </div>
        <div>
          <div className={`resolution-title ${state}`}>{titleMap[state]}</div>
          <div className="resolution-subtitle">{subtitleMap[state]}</div>
        </div>
      </div>

      {state === 'convergence' && (
        <ConvergenceCard
          resolution={resolution}
          featureVector={featureVector}
          optimizerOutput={optimizerOutput}
        />
      )}
      {state === 'qualification' && (
        <QualificationCard
          resolution={resolution}
          featureVector={featureVector}
          optimizerOutput={optimizerOutput}
          reasonerConclusion={reasonerConclusion}
        />
      )}
      {state === 'override' && (
        <OverrideCard
          resolution={resolution}
          featureVector={featureVector}
          optimizerOutput={optimizerOutput}
          reasonerConclusion={reasonerConclusion}
        />
      )}
    </div>
  );
}
