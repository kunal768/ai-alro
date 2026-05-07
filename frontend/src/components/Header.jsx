export default function Header({ activeScenario, phase, onReset, onHome }) {
  const isActive = phase !== 'select';

  return (
    <header className="header">
      <div className="header-inner">
        <button className="header-home-btn" onClick={onHome} type="button" title="Back to home">
          <div className="header-dot" />
          <div>
            <div className="header-title">ALRO</div>
            <div className="header-subtitle">Autonomous Logistics &amp; Routing Optimizer</div>
          </div>
        </button>

        {isActive && activeScenario && (
          <>
            <div className="header-divider" />
            <div className="header-active-scenario">
              <span className="header-active-label">{activeScenario.label}</span>
              <span className="header-active-name">{activeScenario.title}</span>
              <span
                className="header-badge"
                style={{ color: activeScenario.badgeColor }}
              >
                {activeScenario.badgeLabel}
              </span>
            </div>
          </>
        )}

        {isActive && (
          <div className="header-actions">
            <button className="btn-reset" onClick={onReset} type="button">
              <span>↺</span> New scenario
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
