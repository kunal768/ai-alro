import { SCENARIOS } from '../scenarios.js';

export default function ScenarioSelector({ onSelect }) {
  return (
    <div className="scenario-selector">
      <div className="scenario-selector-heading">Select a demonstration scenario</div>
      <div className="scenario-cards">
        {SCENARIOS.map(scenario => (
          <button
            key={scenario.id}
            className="scenario-card"
            onClick={() => onSelect(scenario)}
            type="button"
          >
            <div className="scenario-card-header">
              <span className="scenario-card-label">{scenario.label}</span>
              <span
                className="scenario-card-badge"
                style={{ color: scenario.badgeColor, borderColor: scenario.badgeColor }}
              >
                {scenario.badgeLabel}
              </span>
            </div>
            <div className="scenario-card-title">{scenario.title}</div>
            <div className="scenario-card-desc">{scenario.description}</div>
            <div className="scenario-card-footer">
              Run deliberation
              <span className="scenario-card-arrow">→</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
