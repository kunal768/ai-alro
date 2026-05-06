const STEPS = [
  { key: 'intake',       label: 'Signal Population' },
  { key: 'deliberation', label: 'Parallel Deliberation' },
  { key: 'resolution',   label: 'Resolution' },
];

const ORDER = ['select', 'intake', 'deliberation', 'resolution'];

export default function PhaseTrack({ phase }) {
  const currentIndex = ORDER.indexOf(phase);

  return (
    <nav className="phase-track" aria-label="Deliberation phases">
      <div className="phase-track-inner">
        {STEPS.map((step, i) => {
          const stepIndex = i + 1;
          const isDone   = currentIndex > stepIndex;
          const isActive = currentIndex === stepIndex;
          const cls = isDone ? 'done' : isActive ? 'active' : '';

          return (
            <div key={step.key} style={{ display: 'flex', alignItems: 'center' }}>
              <div className={`phase-step ${cls}`}>
                <div className="phase-step-num">
                  {isDone ? '✓' : i + 1}
                </div>
                <span className="phase-step-label">{step.label}</span>
              </div>
              {i < STEPS.length - 1 && <div className="phase-connector" />}
            </div>
          );
        })}
      </div>
    </nav>
  );
}
