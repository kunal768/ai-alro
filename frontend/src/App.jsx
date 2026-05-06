import { useDeliberation } from './hooks/useDeliberation.js';
import Header from './components/Header.jsx';
import PhaseTrack from './components/PhaseTrack.jsx';
import DegradedBanner from './components/DegradedBanner.jsx';
import RouteMap from './components/RouteMap.jsx';
import ScenarioSelector from './components/ScenarioSelector.jsx';
import Phase1_Signals from './components/Phase1_Signals.jsx';
import { OptimizerPanel, ReasonerPanel, AgreementIndicator } from './components/Phase2_Deliberation.jsx';
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
    errorState,
    isDegraded,
    isStreaming,
    mapState,
    startDeliberation,
    reset,
  } = useDeliberation();

  const showSidebars = phase !== 'select';
  const showOptimizer = optimizerOutput !== null;
  const showReasoner = reasonerText !== '' || isStreaming;
  const showBottomBar = phase === 'deliberation' || phase === 'resolution';

  return (
    <div className="app-shell">
      {/* Fixed map background — always mounted */}
      <div className="map-background">
        <RouteMap mapState={mapState} />
      </div>

      {/* Fixed layout overlay */}
      <div className="app-layout">
        {/* Top bar: header + phase track */}
        <div className="app-top-bar">
          <Header activeScenario={activeScenario} phase={phase} onReset={reset} />
          {phase !== 'select' && <PhaseTrack phase={phase} />}
          {isDegraded && (phase === 'deliberation' || phase === 'resolution') && (
            <DegradedBanner errorState={errorState} />
          )}
        </div>

        {/* Middle row: left sidebar | map center | right sidebar */}
        <div className="app-content-row">
          {/* Left sidebar */}
          <div className={`app-sidebar left-sidebar ${showSidebars ? 'sidebar-visible' : ''}`}>
            {phase === 'intake' && signals && (
              <Phase1_Signals featureVector={signals} signalRevealCount={signalRevealCount} />
            )}
            {showOptimizer && (
              <OptimizerPanel
                optimizerOutput={optimizerOutput}
                featureVector={signals}
              />
            )}
          </div>

          {/* Transparent map center — scenario selector overlaid here */}
          <div className="app-map-center">
            {phase === 'select' && (
              <div className="scenario-overlay">
                <ScenarioSelector onSelect={startDeliberation} />
              </div>
            )}
          </div>

          {/* Right sidebar */}
          <div className={`app-sidebar right-sidebar ${showSidebars ? 'sidebar-visible' : ''}`}>
            {(showReasoner || phase === 'deliberation' || phase === 'resolution') && (
              <ReasonerPanel
                reasonerText={reasonerText}
                reasonerConclusion={reasonerConclusion}
                isStreaming={isStreaming}
              />
            )}
          </div>
        </div>

        {/* Bottom bar: agreement + conclusion + resolution */}
        {showBottomBar && (
          <div className="app-bottom-bar">
            <div className="bottom-bar-inner">
              <div className="bottom-bar-agreement">
                <AgreementIndicator
                  reasonerText={reasonerText}
                  reasonerConclusion={reasonerConclusion}
                />
              </div>
              <div className="bottom-bar-resolution">
                {resolution && (
                  <Phase3_Resolution
                    resolution={resolution}
                    featureVector={signals}
                    optimizerOutput={optimizerOutput}
                    reasonerConclusion={reasonerConclusion}
                  />
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
