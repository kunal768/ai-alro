import { useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';

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

export function OptimizerPanel({ optimizerOutput, featureVector }) {
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
                  <div className="routing-meta-value">${opt.estimated_cost_gbp.toFixed(2)}</div>
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

export function AgreementIndicator({ reasonerText, reasonerConclusion }) {
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

const IMPACT_SECTIONS = [
  { id: 'whyRoute', label: 'Why This Route', patterns: [/signal/i, /dominant/i, /contribution/i] },
  { id: 'borderline', label: 'Borderline Check', patterns: [/borderline/i, /gap/i, /rank/i] },
  { id: 'fairness', label: 'Fairness Check', patterns: [/fairness/i, /geographic/i, /underserved/i, /complaint/i] },
  { id: 'riskFlags', label: 'Risk Flags', patterns: [/risk/i, /flag/i, /blind spot/i, /deadline/i] },
  { id: 'finalCall', label: 'Final Call', patterns: [/conclusion/i, /decision/i, /confirm/i, /override/i, /qualify/i] },
];

function simplifyLanguage(text) {
  return text
    .replace(/\bcomposite score\b/gi, 'overall score')
    .replace(/\bweighted contribution\b/gi, 'impact')
    .replace(/\bzone risk penalty\b/gi, 'area risk cost')
    .replace(/\bplausible real-world variation\b/gi, 'real-world change')
    .replace(/\bstructural blind spots\b/gi, 'missing factors')
    .replace(/\bgeographic fairness\b/gi, 'area fairness')
    .replace(/\btime window feasibility\b/gi, 'on-time feasibility')
    .replace(/\bredlining by proxy\b/gi, 'unfair area bias')
    .replace(/\s+/g, ' ')
    .trim();
}

function getSingleImpactSentence(text) {
  const cleaned = simplifyLanguage(text);
  if (!cleaned) return 'No summary available.';

  // If the model already provided a summary sentence, prefer it.
  const provided = cleaned.match(/(?:summary|impact|tl;dr)\s*:\s*([^.!?]+[.!?])/i);
  if (provided?.[1]) return provided[1].trim();

  const sentences = cleaned
    .split(/(?<=[.!?])\s+/)
    .map(s => s.trim())
    .filter(Boolean);
  if (sentences.length === 0) return `${cleaned.replace(/[.!?]+$/, '')}.`;
  if (sentences.length === 1) return sentences[0];

  const impactWords = [
    'risk', 'delay', 'deadline', 'fairness', 'bias', 'recommended',
    'best', 'override', 'confirm', 'qualify', 'confidence', 'tradeoff',
  ];
  const scoreSentence = (sentence) => {
    const lower = sentence.toLowerCase();
    const impactScore = impactWords.reduce((acc, word) => acc + (lower.includes(word) ? 2 : 0), 0);
    const numberPenalty = (sentence.match(/\d/g) || []).length > 5 ? -2 : 0;
    const lengthScore = sentence.length >= 45 && sentence.length <= 170 ? 2 : 0;
    return impactScore + numberPenalty + lengthScore;
  };

  const picked = [...sentences].sort((a, b) => scoreSentence(b) - scoreSentence(a))[0];
  return /[.!?]$/.test(picked) ? picked : `${picked}.`;
}

function pickImpactHeading(rawHeading) {
  const heading = rawHeading ?? '';
  const match = IMPACT_SECTIONS.find(section =>
    section.patterns.some(pattern => pattern.test(heading))
  );
  return match?.label ?? 'Reasoning Detail';
}

function parseReasoningSections(rawText) {
  const lines = rawText.split('\n');
  const sections = [];
  let current = null;

  for (const line of lines) {
    const headingMatch = line.match(/^##\s+(.+)$/);
    if (headingMatch) {
      if (current) sections.push(current);
      current = { heading: headingMatch[1].trim(), bodyLines: [] };
    } else {
      if (!current) current = { heading: 'Reasoning', bodyLines: [] };
      current.bodyLines.push(line);
    }
  }
  if (current) sections.push(current);

  return sections
    .map((section, index) => {
      const body = section.bodyLines.join('\n').trim();
      return {
        key: `${section.heading}-${index}`,
        displayHeading: pickImpactHeading(section.heading),
        originalHeading: section.heading,
        body,
        summary: getSingleImpactSentence(body || section.heading),
      };
    })
    .filter(section => section.body.length > 0 || section.originalHeading.length > 0);
}

export function ReasonerPanel({ reasonerText, reasonerConclusion, isStreaming }) {
  const bodyRef = useRef(null);
  const [openSections, setOpenSections] = useState({});

  // Strip the <conclusion> XML block before rendering
  const conclusionStart = reasonerText.indexOf('<conclusion>');
  const displayText = conclusionStart >= 0
    ? reasonerText.slice(0, conclusionStart).trimEnd()
    : reasonerText;

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [displayText]);

  const parsedSections = useMemo(() => parseReasoningSections(displayText), [displayText]);

  const conclusionDecision = reasonerConclusion?.decision;
  const finalCallSummary = reasonerConclusion
    ? simplifyLanguage(
      `${reasonerConclusion.decision} · Recommended ${reasonerConclusion.recommended_option}. ${reasonerConclusion.override_reason && reasonerConclusion.override_reason !== 'NONE'
        ? reasonerConclusion.override_reason
        : ''}`
    )
    : null;

  const toggleSection = (key) => {
    setOpenSections(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="panel reasoner-panel-full">
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

      <div className="panel-body reasoner-md-body" ref={bodyRef}>
        {displayText.length === 0 && isStreaming && (
          <div className="reasoner-waiting">
            <div className="phase1-spinner" style={{ borderTopColor: 'var(--purple)' }} />
            Initiating chain of thought…
          </div>
        )}

        {displayText.length > 0 && (
          <div className="reasoner-markdown reasoner-accordion">
            {parsedSections.map((section) => {
              const isOpen = !!openSections[section.key];
              return (
                <div key={section.key} className="reasoner-accordion-item">
                  <button
                    type="button"
                    className="reasoner-accordion-header"
                    onClick={() => toggleSection(section.key)}
                    title={section.originalHeading}
                  >
                    <span className="reasoner-accordion-chevron">{isOpen ? '▾' : '▸'}</span>
                    <span className="reasoner-accordion-title">{section.displayHeading}</span>
                    <span className="reasoner-accordion-preview">{section.summary}</span>
                  </button>
                  {isOpen && (
                    <div className="reasoner-accordion-body">
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="rmd-p">{children}</p>,
                          ul: ({ children }) => <ul className="rmd-ul">{children}</ul>,
                          ol: ({ children }) => <ol className="rmd-ol">{children}</ol>,
                          li: ({ children }) => <li className="rmd-li">{children}</li>,
                          strong: ({ children }) => <strong className="rmd-strong">{children}</strong>,
                          em: ({ children }) => <em className="rmd-em">{children}</em>,
                          code: ({ children }) => <code className="rmd-code">{children}</code>,
                        }}
                      >
                        {simplifyLanguage(section.body)}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              );
            })}
            {finalCallSummary && (
              <div className="reasoner-final-call">
                <div className="reasoner-final-call-title">Final Call</div>
                <div className="reasoner-final-call-body">{finalCallSummary}</div>
              </div>
            )}
            {isStreaming && <span className="reasoner-cursor" />}
          </div>
        )}

        {conclusionDecision && (
          <div className={`conclusion-chip ${conclusionDecision}`} style={{ marginTop: 12 }}>
            {conclusionDecision === 'confirm'  && '✓ CONFIRMED'}
            {conclusionDecision === 'qualify'  && '⚠ QUALIFIED'}
            {conclusionDecision === 'override' && '✕ OVERRIDE'}
          </div>
        )}

        {reasonerConclusion?.flags?.length > 0 && (
          <div className="reasoner-flags">
            {reasonerConclusion.flags.map((flag, i) => (
              <div key={i} className="reasoner-flag-item">
                <span className="reasoner-flag-bullet">!</span>
                <span>{flag}</span>
              </div>
            ))}
          </div>
        )}

        {reasonerConclusion?.override_reason && (
          <div className="reasoner-override-reason">
            <div className="reasoner-override-label">Override Reason</div>
            <div className="reasoner-override-text">{reasonerConclusion.override_reason}</div>
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
