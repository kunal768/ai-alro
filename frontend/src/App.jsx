import { useDeliberation } from './hooks/useDeliberation.js';
import Header from './components/Header.jsx';
import PhaseTrack from './components/PhaseTrack.jsx';
import ScenarioSelector from './components/ScenarioSelector.jsx';
import Phase1_Signals from './components/Phase1_Signals.jsx';
import Phase2_Deliberation from './components/Phase2_Deliberation.jsx';
import Phase3_Resolution from './components/Phase3_Resolution.jsx';

export default function App() {
  const {
    phase,
    activeScenario,
    signals,
    signalRevealCount,
    optimizerOutput,
    reasonerText,
    reasonerConclusion,
    resolution,
    isStreaming,
    startDeliberation,
    reset,
  } = useDeliberation();

  return (
    <div className="app-shell">
      <Header activeScenario={activeScenario} phase={phase} onReset={reset} />

      {phase !== 'select' && <PhaseTrack phase={phase} />}

      <div className="main-content">
        {phase === 'select' && (
          <ScenarioSelector onSelect={startDeliberation} />
        )}

        {(phase === 'intake') && (
          <Phase1_Signals
            featureVector={signals}
            signalRevealCount={signalRevealCount}
          />
        )}

        {phase === 'deliberation' && optimizerOutput && (
          <Phase2_Deliberation
            optimizerOutput={optimizerOutput}
            featureVector={signals}
            reasonerText={reasonerText}
            reasonerConclusion={reasonerConclusion}
            isStreaming={isStreaming}
          />
        )}

        {phase === 'resolution' && (
          <Phase3_Resolution
            resolution={resolution}
            featureVector={signals}
            optimizerOutput={optimizerOutput}
            reasonerConclusion={reasonerConclusion}
          />
        )}
      </div>
    </div>
  );
}
