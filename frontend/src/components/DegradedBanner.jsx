export default function DegradedBanner({ errorState }) {
  const message = errorState?.message
    ?? 'Reasoner Agent is offline. Decision defaults to Optimizer recommendation without deliberation.';

  return (
    <div className="degraded-banner">
      <span className="degraded-banner-icon">&#9888;</span>
      <div className="degraded-banner-body">
        <strong>Reasoning Layer Unavailable</strong>
        <p>{message}</p>
      </div>
    </div>
  );
}
