import { useState, useRef, useCallback } from 'react';
import { MOCK_DATA } from '../mockData.js';
import { parseSSEBuffer } from '../utils/sseParser.js';
import { fetchRoadGeometry } from '../utils/routeGeometry.js';

const DEMO_URL = (id) => `/api/reasoner/demo/${id}`;
const SIGNAL_STAGGER_MS = 350;
const SIGNAL_COUNT = 8;

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function buildMapRoutes(fv, opt) {
  const warehouseMap = {};
  const driverMap = {};
  (fv.warehouse_options ?? []).forEach(w => { warehouseMap[w.warehouse_id] = w; });
  (fv.available_drivers ?? []).forEach(d => { driverMap[d.driver_id] = d; });

  const routes = (opt.ranked_options ?? []).map((o, idx) => {
    const wh = warehouseMap[o.warehouse_id] ?? {};
    const drv = driverMap[o.driver_id] ?? {};
    return {
      optionId: o.option_id,
      warehouseId: o.warehouse_id,
      driverId: o.driver_id,
      warehouseName: wh.name,
      driverName: drv.name,
      warehouseLat: wh.lat ?? 0,
      warehouseLon: wh.lon ?? 0,
      destLat: fv.destination_lat,
      destLon: fv.destination_lon,
      rank: idx + 1,
      score: o.composite_score,
      etaHours: o.estimated_duration_hours,
      cost: o.estimated_cost_gbp,
    };
  });

  const topOpt = opt.top_choice ?? opt.ranked_options?.[0];
  const topWh = warehouseMap[topOpt?.warehouse_id] ?? {};
  const topDrv = driverMap[topOpt?.driver_id] ?? {};

  return {
    routes,
    topRoute: topOpt ? {
      optionId: topOpt.option_id,
      warehouseId: topOpt.warehouse_id,
      driverId: topOpt.driver_id,
      warehouseName: topWh.name,
      driverName: topDrv.name,
      warehouseLat: topWh.lat ?? 0,
      warehouseLon: topWh.lon ?? 0,
      destLat: fv.destination_lat,
      destLon: fv.destination_lon,
      etaHours: topOpt.estimated_duration_hours,
      cost: topOpt.estimated_cost_gbp,
      score: topOpt.composite_score,
    } : null,
  };
}

async function hydrateRoutesWithRoadGeometry(routes) {
  const enriched = await Promise.all(routes.map(async (route) => {
    const pathCoords = await fetchRoadGeometry(
      { lat: route.warehouseLat, lon: route.warehouseLon },
      { lat: route.destLat, lon: route.destLon }
    );
    return { ...route, pathCoords };
  }));
  return enriched;
}

async function streamDemo(scenarioId, abortSignal, callbacks) {
  const { onScenarioData, onToken, onConclusion, onResolution, onError } = callbacks;

  try {
    const res = await fetch(DEMO_URL(scenarioId), {
      headers: { Accept: 'text/event-stream' },
      signal: abortSignal,
    });

    if (!res.ok) throw new Error('non-ok');

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      if (abortSignal.aborted) { reader.cancel(); return 'aborted'; }
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const { parsed, remainder } = parseSSEBuffer(buffer);
      buffer = remainder;

      for (const evt of parsed) {
        if (abortSignal.aborted) return 'aborted';
        let data;
        try { data = JSON.parse(evt.data); } catch { continue; }

        switch (evt.type) {
          case 'scenario_data': onScenarioData(data); break;
          case 'token':         onToken(data.text ?? ''); break;
          case 'conclusion':    onConclusion(data); break;
          case 'resolution':    onResolution(data); break;
          case 'error':         onError(data); break;
          case 'done':          return 'done';
        }
      }
    }
    return 'done';
  } catch {
    if (abortSignal.aborted) return 'aborted';
    return 'fallback';
  }
}

async function simulateMockStream(scenarioId, abortSignal, callbacks) {
  const { reasonerStream } = MOCK_DATA[scenarioId];
  const { onToken, onConclusion, onResolution } = callbacks;

  const tokens = reasonerStream.text.match(/\S+|\n+/g) ?? [];

  for (let i = 0; i < tokens.length; i++) {
    if (abortSignal.aborted) return;
    const token = tokens[i];
    const isNewline = /^\n+$/.test(token);
    onToken(isNewline ? token : token + ' ');
    await delay(isNewline ? 180 : 35 + Math.random() * 25);
  }

  await delay(350);
  if (abortSignal.aborted) return;
  onConclusion(reasonerStream.conclusion);

  await delay(450);
  if (abortSignal.aborted) return;
  onResolution(reasonerStream.resolution);
}

export function useDeliberation() {
  const [phase, setPhase] = useState('select');
  const [activeScenario, setActiveScenario] = useState(null);
  const [signals, setSignals] = useState(null);
  const [signalRevealCount, setSignalRevealCount] = useState(0);
  const [optimizerOutput, setOptimizerOutput] = useState(null);
  const [reasonerText, setReasonerText] = useState('');
  const [reasonerConclusion, setReasonerConclusion] = useState(null);
  const [resolution, setResolution] = useState(null);
  const [errorState, setErrorState] = useState(null);
  const [isDegraded, setIsDegraded] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [mapState, setMapState] = useState({ drivers: [], candidateRoutes: [] });
  const abortRef = useRef(null);

  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    setPhase('select');
    setActiveScenario(null);
    setSignals(null);
    setSignalRevealCount(0);
    setOptimizerOutput(null);
    setReasonerText('');
    setReasonerConclusion(null);
    setResolution(null);
    setErrorState(null);
    setIsDegraded(false);
    setIsStreaming(false);
    setMapState({ drivers: [], candidateRoutes: [] });
  }, []);

  const startDeliberation = useCallback(async (scenario) => {
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const { signal } = controller;

    setActiveScenario(scenario);
    setPhase('intake');
    setSignals(null);
    setSignalRevealCount(0);
    setOptimizerOutput(null);
    setReasonerText('');
    setReasonerConclusion(null);
    setResolution(null);
    setErrorState(null);
    setIsDegraded(false);
    setIsStreaming(false);
    setMapState({ drivers: [], candidateRoutes: [] });

    const mockFv  = MOCK_DATA[scenario.id].featureVector;
    const mockOpt = MOCK_DATA[scenario.id].optimizerOutput;

    // animPromise resolves when Phase 1 animation finishes; we await it before
    // transitioning to Phase 2 so the user always sees the full signal reveal.
    let resolveAnim;
    const animPromise = new Promise(res => { resolveAnim = res; });
    let animStarted = false;

    async function runAnimation(fv) {
      animStarted = true;
      setSignals(fv);

      // Add destination and drivers to map
      setMapState(prev => ({
        ...prev,
        destination: {
          lat: fv.destination_lat,
          lon: fv.destination_lon,
          zone: fv.destination_zone_id,
        },
        drivers: (fv.available_drivers ?? []).map(d => ({
          id: d.driver_id,
          name: d.name,
          lat: d.current_lat,
          lon: d.current_lon,
          vehicle_type: d.vehicle_type,
        })),
      }));

      for (let i = 1; i <= SIGNAL_COUNT; i++) {
        if (signal.aborted) { resolveAnim(); return; }
        await delay(SIGNAL_STAGGER_MS);
        setSignalRevealCount(i);
      }
      await delay(1200);
      resolveAnim();
    }

    // streamDonePromise resolves when the SSE stream (or mock fallback) ends.
    let streamDoneResolve;
    const streamDonePromise = new Promise(res => { streamDoneResolve = res; });

    const streamCallbacks = {
      onScenarioData: (data) => {
        const opt = data.optimizer_output ?? mockOpt;
        const fv = data.feature_vector ?? mockFv;
        setOptimizerOutput(opt);
        runAnimation(fv);

        const { routes, topRoute } = buildMapRoutes(fv, opt);
        setMapState(prev => ({
          ...prev,
          candidateRoutes: [...(prev.candidateRoutes ?? []), ...routes],
          selectedRoute: topRoute ?? prev.selectedRoute,
        }));

        hydrateRoutesWithRoadGeometry(routes).then((roadRoutes) => {
          if (signal.aborted) return;
          const byId = new Map(roadRoutes.map(route => [route.optionId, route]));
          setMapState(prev => ({
            ...prev,
            candidateRoutes: (prev.candidateRoutes ?? []).map(route => byId.get(route.optionId) ?? route),
            selectedRoute: prev.selectedRoute ? (byId.get(prev.selectedRoute.optionId) ?? prev.selectedRoute) : prev.selectedRoute,
            finalRoute: prev.finalRoute ? {
              ...prev.finalRoute,
              pathCoords: byId.get(prev.finalRoute.optionId)?.pathCoords ?? prev.finalRoute.pathCoords,
            } : prev.finalRoute,
          }));
        });
      },
      onToken:      (text) => setReasonerText(prev => prev + text),
      onConclusion: (data) => setReasonerConclusion(data),
      onResolution: (data) => {
        setResolution(data);
        let missingGeometryRoute = null;
        // Set final route on map — find warehouse from candidateRoutes
        setMapState(prev => {
          const finalOpt = prev.candidateRoutes?.find(r => r.optionId === data.final_option_id);
          if (finalOpt && !finalOpt.pathCoords) {
            missingGeometryRoute = finalOpt;
          }
          return {
            ...prev,
            finalRoute: finalOpt ? {
              optionId: finalOpt.optionId,
              warehouseId: finalOpt.warehouseId,
              driverId: finalOpt.driverId,
              warehouseName: finalOpt.warehouseName,
              driverName: finalOpt.driverName,
              warehouseLat: finalOpt.warehouseLat,
              warehouseLon: finalOpt.warehouseLon,
              destLat: finalOpt.destLat,
              destLon: finalOpt.destLon,
              etaHours: finalOpt.etaHours,
              cost: finalOpt.cost,
              score: finalOpt.score,
              pathCoords: finalOpt.pathCoords,
              reason: data.explanation ?? null,
              decision: data.state === 'convergence' ? 'confirm' :
                        data.state === 'qualification' ? 'qualify' : 'override',
            } : prev.finalRoute,
          };
        });

        // If final option geometry has not been hydrated yet, fetch it now.
        if (missingGeometryRoute) {
          fetchRoadGeometry(
            { lat: missingGeometryRoute.warehouseLat, lon: missingGeometryRoute.warehouseLon },
            { lat: missingGeometryRoute.destLat, lon: missingGeometryRoute.destLon }
          ).then((pathCoords) => {
            if (signal.aborted) return;
            setMapState(state => ({
              ...state,
              candidateRoutes: (state.candidateRoutes ?? []).map(route => (
                route.optionId === missingGeometryRoute.optionId ? { ...route, pathCoords } : route
              )),
              selectedRoute: state.selectedRoute?.optionId === missingGeometryRoute.optionId
                ? { ...state.selectedRoute, pathCoords }
                : state.selectedRoute,
              finalRoute: state.finalRoute?.optionId === missingGeometryRoute.optionId
                ? { ...state.finalRoute, pathCoords }
                : state.finalRoute,
            }));
          });
        }
      },
      onError:      (data) => { setErrorState(data); setIsDegraded(true); },
    };

    // Kick off the SSE stream concurrently with the animation.
    streamDemo(scenario.id, signal, streamCallbacks).then(result => {
      if (result === 'aborted') { streamDoneResolve('aborted'); return; }

      if (result === 'fallback') {
        // Backend unavailable — flag degraded state and fall back to mock data.
        setIsDegraded(true);
        setErrorState({ message: 'Reasoner Agent unavailable. Proceeding on Optimizer output alone — no chain of thought available.' });
        if (!animStarted) {
          setOptimizerOutput(mockOpt);
          runAnimation(mockFv);

          // Also build candidate routes for mock fallback
          const { routes, topRoute } = buildMapRoutes(mockFv, mockOpt);
          setMapState(prev => ({
            ...prev,
            candidateRoutes: [...(prev.candidateRoutes ?? []), ...routes],
            selectedRoute: topRoute ?? prev.selectedRoute,
          }));

          hydrateRoutesWithRoadGeometry(routes).then((roadRoutes) => {
            if (signal.aborted) return;
            const byId = new Map(roadRoutes.map(route => [route.optionId, route]));
            setMapState(prev => ({
              ...prev,
              candidateRoutes: (prev.candidateRoutes ?? []).map(route => byId.get(route.optionId) ?? route),
              selectedRoute: prev.selectedRoute ? (byId.get(prev.selectedRoute.optionId) ?? prev.selectedRoute) : prev.selectedRoute,
              finalRoute: prev.finalRoute ? {
                ...prev.finalRoute,
                pathCoords: byId.get(prev.finalRoute.optionId)?.pathCoords ?? prev.finalRoute.pathCoords,
              } : prev.finalRoute,
            }));
          });
        }
        simulateMockStream(scenario.id, signal, streamCallbacks)
          .then(() => streamDoneResolve('done'));
      } else {
        streamDoneResolve(result);
      }
    });

    // Phase 1 → Phase 2: wait for the signal-reveal animation to complete.
    await animPromise;
    if (signal.aborted) return;

    setPhase('deliberation');
    setIsStreaming(true);

    // Phase 2 → Phase 3: wait for the reasoning stream to finish.
    const streamResult = await streamDonePromise;
    if (streamResult === 'aborted' || signal.aborted) return;

    setIsStreaming(false);
    await delay(450);
    if (signal.aborted) return;
    setPhase('resolution');
  }, []);

  return {
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
  };
}
