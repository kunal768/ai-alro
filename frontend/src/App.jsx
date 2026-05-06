import { useCallback, useEffect, useMemo, useState } from 'react';
import { useDeliberation } from './hooks/useDeliberation.js';
import Header from './components/Header.jsx';
import PhaseTrack from './components/PhaseTrack.jsx';
import DegradedBanner from './components/DegradedBanner.jsx';
import RouteMap from './components/RouteMap.jsx';
import ScenarioSelector from './components/ScenarioSelector.jsx';
import Phase1_Signals from './components/Phase1_Signals.jsx';
import { OptimizerPanel, ReasonerPanel, AgreementIndicator } from './components/Phase2_Deliberation.jsx';
import Phase3_Resolution from './components/Phase3_Resolution.jsx';

const LEFT_MIN = 320;
const LEFT_MAX = 620;
const LEFT_DEFAULT = 440;

const RIGHT_MIN = 320;
const RIGHT_MAX = 620;
const RIGHT_DEFAULT = 420;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function loadWidth(key, fallback, min, max) {
  if (typeof window === 'undefined') return fallback;
  const stored = Number(window.localStorage.getItem(key));
  if (!Number.isFinite(stored)) return fallback;
  return clamp(stored, min, max);
}

function widthToScale(width, baseline) {
  return clamp(width / baseline, 0.88, 1.18);
}

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
  const showResolution = phase === 'resolution' && resolution;
  const [leftWidth, setLeftWidth] = useState(() => loadWidth('ui.leftSidebarWidth', LEFT_DEFAULT, LEFT_MIN, LEFT_MAX));
  const [rightWidth, setRightWidth] = useState(() => loadWidth('ui.rightSidebarWidth', RIGHT_DEFAULT, RIGHT_MIN, RIGHT_MAX));
  const [dragState, setDragState] = useState(null);

  const leftScale = useMemo(() => widthToScale(leftWidth, LEFT_DEFAULT), [leftWidth]);
  const rightScale = useMemo(() => widthToScale(rightWidth, RIGHT_DEFAULT), [rightWidth]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('ui.leftSidebarWidth', String(Math.round(leftWidth)));
  }, [leftWidth]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('ui.rightSidebarWidth', String(Math.round(rightWidth)));
  }, [rightWidth]);

  useEffect(() => {
    if (!dragState) return;
    const onPointerMove = (event) => {
      if (dragState.side === 'left') {
        setLeftWidth(clamp(dragState.startWidth + (event.clientX - dragState.startX), LEFT_MIN, LEFT_MAX));
      } else {
        setRightWidth(clamp(dragState.startWidth - (event.clientX - dragState.startX), RIGHT_MIN, RIGHT_MAX));
      }
    };
    const onPointerUp = () => setDragState(null);

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };
  }, [dragState]);

  const startResize = useCallback((side, event) => {
    event.preventDefault();
    setDragState({
      side,
      startX: event.clientX,
      startWidth: side === 'left' ? leftWidth : rightWidth,
    });
  }, [leftWidth, rightWidth]);

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
          <div
            className={`app-sidebar left-sidebar ${showSidebars ? 'sidebar-visible' : ''}`}
            style={{
              width: leftWidth,
              minWidth: leftWidth,
              maxWidth: leftWidth,
              '--panel-scale': leftScale,
            }}
          >
            {signals && (
              <div className="sidebar-section">
                <div className="sidebar-section-title">Intake + Enrichment</div>
                <Phase1_Signals
                  featureVector={signals}
                  signalRevealCount={signalRevealCount}
                  phase={phase}
                />
              </div>
            )}
            {showOptimizer && (
              <div className="sidebar-section">
                <div className="sidebar-section-title">Route Scoring</div>
                <OptimizerPanel
                  optimizerOutput={optimizerOutput}
                  featureVector={signals}
                />
              </div>
            )}
          </div>
          {showSidebars && (
            <div
              className={`sidebar-resize-handle left ${dragState?.side === 'left' ? 'active' : ''}`}
              onPointerDown={(event) => startResize('left', event)}
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize left panel"
            />
          )}

          {/* Transparent map center — scenario selector overlaid here */}
          <div className="app-map-center">
            {phase === 'select' && (
              <div className="scenario-overlay">
                <ScenarioSelector onSelect={startDeliberation} />
              </div>
            )}
          </div>
          {showSidebars && (
            <div
              className={`sidebar-resize-handle right ${dragState?.side === 'right' ? 'active' : ''}`}
              onPointerDown={(event) => startResize('right', event)}
              role="separator"
              aria-orientation="vertical"
              aria-label="Resize right panel"
            />
          )}

          {/* Right sidebar */}
          <div
            className={`app-sidebar right-sidebar ${showSidebars ? 'sidebar-visible' : ''}`}
            style={{
              width: rightWidth,
              minWidth: rightWidth,
              maxWidth: rightWidth,
              '--panel-scale': rightScale,
            }}
          >
            {(phase === 'deliberation' || phase === 'resolution') && (
              <div className="sidebar-section">
                <div className="sidebar-section-title">Decision Health</div>
                <AgreementIndicator
                  reasonerText={reasonerText}
                  reasonerConclusion={reasonerConclusion}
                />
              </div>
            )}
            {(showReasoner || phase === 'deliberation' || phase === 'resolution') && (
              <div className="sidebar-section reasoner-section-wrap">
                <div className="sidebar-section-title">Reasoning</div>
                <ReasonerPanel
                  reasonerText={reasonerText}
                  reasonerConclusion={reasonerConclusion}
                  isStreaming={isStreaming}
                />
              </div>
            )}
            {showResolution && (
              <div className="sidebar-section resolution-section-wrap">
                <div className="sidebar-section-title">Final Recommendation</div>
                <Phase3_Resolution
                  resolution={resolution}
                  featureVector={signals}
                  optimizerOutput={optimizerOutput}
                  reasonerConclusion={reasonerConclusion}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
