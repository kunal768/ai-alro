import { useState, useRef, useCallback } from 'react';
import { MOCK_DATA } from '../mockData.js';
import { parseSSEBuffer } from '../utils/sseParser.js';
import { fetchRoadGeometry } from '../utils/routeGeometry.js';

const DEMO_URL   = (id) => `/api/reasoner/demo/${id}`;
const ENRICH_URL = '/api/intake/enrich';
const SCORE_URL  = '/api/optimizer/score';
const REASON_URL = '/api/reasoner/reason';
const SIGNAL_STAGGER_MS = 350;
const SIGNAL_COUNT = 8;

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function explainGap(option, top) {
  if (!top || option.optionId === top.optionId) return '';
  const fields = [
    {
      delta: (top.timelinessScore ?? 0) - (option.timelinessScore ?? 0),
      msg: (d) => `Lower timeliness — pickup ETA costs ${d.toFixed(2)} more score vs the chosen route.`,
    },
    {
      delta: (option.zoneRiskPenalty ?? 0) - (top.zoneRiskPenalty ?? 0),
      msg: () => `Higher zone risk penalty (${(option.zoneRiskPenalty ?? 0).toFixed(2)} vs ${(top.zoneRiskPenalty ?? 0).toFixed(2)}) on this destination.`,
    },
    {
      delta: (top.driverProximityScore ?? 0) - (option.driverProximityScore ?? 0),
      msg: (d) => `Driver is farther from the warehouse — ~${(d * 40).toFixed(0)} km additional pickup distance.`,
    },
    {
      delta: (top.proximityScore ?? 0) - (option.proximityScore ?? 0),
      msg: (d) => `Warehouse is ~${(d * 60).toFixed(0)} km farther from the destination.`,
    },
    {
      delta: (top.costEfficiency ?? 0) - (option.costEfficiency ?? 0),
      msg: () => `Lower cost efficiency (${(option.costEfficiency ?? 0).toFixed(2)} vs ${(top.costEfficiency ?? 0).toFixed(2)}).`,
    },
  ];
  const worst = fields.filter(f => f.delta > 0).sort((a, b) => b.delta - a.delta)[0];
  return worst ? worst.msg(worst.delta) : 'Comparable score to the chosen route.';
}

function buildMapRoutes(fv, opt) {
  const warehouseMap = {};
  const driverMap = {};
  (fv.warehouse_options ?? []).forEach(w => { warehouseMap[w.warehouse_id] = w; });
  (fv.available_drivers ?? []).forEach(d => { driverMap[d.driver_id] = d; });

  const routes = (opt.ranked_options ?? []).map((o, idx) => {
    const wh  = warehouseMap[o.warehouse_id] ?? {};
    const drv = driverMap[o.driver_id] ?? {};
    return {
      optionId:        o.option_id,
      warehouseId:     o.warehouse_id,
      driverId:        o.driver_id,
      warehouseName:   wh.name,
      driverName:      drv.name,
      warehouseLat:    wh.lat ?? 0,
      warehouseLon:    wh.lon ?? 0,
      driverLat:       drv.current_lat ?? 0,
      driverLon:       drv.current_lon ?? 0,
      destLat:         fv.destination_lat,
      destLon:         fv.destination_lon,
      rank:            idx + 1,
      score:           o.composite_score,
      etaHours:        o.estimated_duration_hours,
      cost:            o.estimated_cost_gbp,
      timelinessScore:     o.timeliness_score,
      costEfficiency:      o.cost_efficiency_score,
      proximityScore:      o.warehouse_proximity_score,
      driverProximityScore: o.driver_proximity_score ?? 0,
      zoneRiskPenalty:     o.zone_risk_penalty,
    };
  });

  const top = routes[0];
  if (top) routes.forEach(r => { r.lesser_reason = explainGap(r, top); });

  const topOpt = opt.top_choice ?? opt.ranked_options?.[0];
  const topWh  = warehouseMap[topOpt?.warehouse_id] ?? {};
  const topDrv = driverMap[topOpt?.driver_id] ?? {};

  return {
    routes,
    topRoute: topOpt ? {
      optionId:     topOpt.option_id,
      warehouseId:  topOpt.warehouse_id,
      driverId:     topOpt.driver_id,
      warehouseName: topWh.name,
      driverName:   topDrv.name,
      warehouseLat: topWh.lat ?? 0,
      warehouseLon: topWh.lon ?? 0,
      driverLat:    topDrv.current_lat ?? 0,
      driverLon:    topDrv.current_lon ?? 0,
      destLat:      fv.destination_lat,
      destLon:      fv.destination_lon,
      etaHours:     topOpt.estimated_duration_hours,
      cost:         topOpt.estimated_cost_gbp,
      score:        topOpt.composite_score,
    } : null,
  };
}

// Fallback: construct a finalRoute-shaped object directly from known fv+opt when
// candidateRoutes lookup misses (race condition in manual order flow).
function buildFinalRouteFromData(optionId, fv, opt) {
  if (!optionId || !fv || !opt) return null;
  const warehouseMap = {};
  const driverMap = {};
  (fv.warehouse_options ?? []).forEach(w => { warehouseMap[w.warehouse_id] = w; });
  (fv.available_drivers ?? []).forEach(d => { driverMap[d.driver_id] = d; });
  const option = (opt.ranked_options ?? []).find(o => o.option_id === optionId)
    ?? opt.ranked_options?.[0];
  if (!option) return null;
  const wh  = warehouseMap[option.warehouse_id] ?? {};
  const drv = driverMap[option.driver_id] ?? {};
  return {
    optionId:     option.option_id,
    warehouseId:  option.warehouse_id,
    driverId:     option.driver_id,
    warehouseName: wh.name,
    driverName:   drv.name,
    warehouseLat: wh.lat ?? 0,
    warehouseLon: wh.lon ?? 0,
    driverLat:    drv.current_lat ?? 0,
    driverLon:    drv.current_lon ?? 0,
    destLat:      fv.destination_lat,
    destLon:      fv.destination_lon,
    etaHours:     option.estimated_duration_hours,
    cost:         option.estimated_cost_gbp,
    score:        option.composite_score,
  };
}

async function hydrateRoutesWithRoadGeometry(routes) {
  const enriched = await Promise.all(routes.map(async (route) => {
    const [pathCoords, legACoords] = await Promise.all([
      fetchRoadGeometry(
        { lat: route.warehouseLat, lon: route.warehouseLon },
        { lat: route.destLat,      lon: route.destLon }
      ),
      (route.driverLat && route.driverLon)
        ? fetchRoadGeometry(
            { lat: route.driverLat,    lon: route.driverLon },
            { lat: route.warehouseLat, lon: route.warehouseLon }
          )
        : Promise.resolve(null),
    ]);
    return { ...route, pathCoords, legACoords };
  }));
  return enriched;
}

// Fetch both legs for the final route in parallel.
async function hydrateFinalRouteLegs(route) {
  const [legBCoords, legACoords] = await Promise.all([
    fetchRoadGeometry(
      { lat: route.warehouseLat, lon: route.warehouseLon },
      { lat: route.destLat,      lon: route.destLon }
    ),
    (route.driverLat && route.driverLon)
      ? fetchRoadGeometry(
          { lat: route.driverLat,    lon: route.driverLon },
          { lat: route.warehouseLat, lon: route.warehouseLon }
        )
      : Promise.resolve(null),
  ]);
  return { ...route, legBCoords, legACoords, pathCoords: legBCoords };
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

async function streamReasonerSSE(featureVector, optimizerOutput, abortSignal, callbacks) {
  const { onToken, onConclusion, onResolution, onError } = callbacks;
  try {
    const res = await fetch(REASON_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ feature_vector: featureVector, optimizer_output: optimizerOutput }),
      signal: abortSignal,
    });
    if (!res.ok) return 'error';
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
          case 'token':      onToken(data.text ?? ''); break;
          case 'conclusion': onConclusion(data); break;
          case 'resolution': onResolution(data); break;
          case 'error':      onError(data); break;
          case 'done':       return 'done';
        }
      }
    }
    return 'done';
  } catch {
    if (abortSignal.aborted) return 'aborted';
    return 'error';
  }
}

// Shared helper: build finalRoute from a resolved option + schedule leg hydration.
function applyResolution(data, candidateRoutes, fallbackFv, fallbackOpt, signal, setMapState) {
  const decision = data.state === 'convergence' ? 'confirm' :
                   data.state === 'qualification' ? 'qualify' : 'override';

  let captured = null;
  setMapState(prev => {
    let src = prev.candidateRoutes?.find(r => r.optionId === data.final_option_id);
    if (!src) src = buildFinalRouteFromData(data.final_option_id, fallbackFv, fallbackOpt);
    if (!src) return prev;

    const finalRoute = {
      optionId:     src.optionId,
      warehouseId:  src.warehouseId,
      driverId:     src.driverId,
      warehouseName: src.warehouseName,
      driverName:   src.driverName,
      warehouseLat: src.warehouseLat,
      warehouseLon: src.warehouseLon,
      driverLat:    src.driverLat ?? 0,
      driverLon:    src.driverLon ?? 0,
      destLat:      src.destLat,
      destLon:      src.destLon,
      etaHours:     src.etaHours,
      cost:         src.cost,
      score:        src.score,
      legBCoords:   src.legBCoords ?? src.pathCoords,
      legACoords:   src.legACoords,
      pathCoords:   src.legBCoords ?? src.pathCoords,
      reason:       data.explanation ?? null,
      decision,
    };
    captured = finalRoute;
    return { ...prev, finalRoute };
  });

  // Async: fetch two-leg geometry
  if (captured) {
    hydrateFinalRouteLegs(captured).then(hydratedRoute => {
      if (signal.aborted) return;
      setMapState(state => ({
        ...state,
        finalRoute: state.finalRoute?.optionId === hydratedRoute.optionId
          ? hydratedRoute : state.finalRoute,
      }));
    });
  }
}

export function useDeliberation() {
  const [phase, setPhase]                       = useState('select');
  const [activeScenario, setActiveScenario]     = useState(null);
  const [signals, setSignals]                   = useState(null);
  const [signalRevealCount, setSignalRevealCount] = useState(0);
  const [optimizerOutput, setOptimizerOutput]   = useState(null);
  const [reasonerText, setReasonerText]         = useState('');
  const [reasonerConclusion, setReasonerConclusion] = useState(null);
  const [resolution, setResolution]             = useState(null);
  const [errorState, setErrorState]             = useState(null);
  const [isDegraded, setIsDegraded]             = useState(false);
  const [isStreaming, setIsStreaming]            = useState(false);
  const [mapState, setMapState]                 = useState({ drivers: [], candidateRoutes: [] });
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

    // Capture live fv/opt when they arrive via SSE so onResolution can use them
    let capturedFv  = mockFv;
    let capturedOpt = mockOpt;

    let resolveAnim;
    const animPromise = new Promise(res => { resolveAnim = res; });
    let animStarted = false;

    async function runAnimation(fv) {
      animStarted = true;
      setSignals(fv);
      setMapState(prev => ({
        ...prev,
        destination: { lat: fv.destination_lat, lon: fv.destination_lon, zone: fv.destination_zone_id },
        drivers: (fv.available_drivers ?? []).map(d => ({
          id: d.driver_id, name: d.name, lat: d.current_lat, lon: d.current_lon, vehicle_type: d.vehicle_type,
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

    let streamDoneResolve;
    const streamDonePromise = new Promise(res => { streamDoneResolve = res; });

    const streamCallbacks = {
      onScenarioData: (data) => {
        capturedFv  = data.feature_vector ?? mockFv;
        capturedOpt = data.optimizer_output ?? mockOpt;
        setOptimizerOutput(capturedOpt);
        runAnimation(capturedFv);

        const { routes, topRoute } = buildMapRoutes(capturedFv, capturedOpt);
        setMapState(prev => ({
          ...prev,
          candidateRoutes: [...(prev.candidateRoutes ?? []), ...routes],
          selectedRoute: topRoute ?? prev.selectedRoute,
        }));

        hydrateRoutesWithRoadGeometry(routes).then((roadRoutes) => {
          if (signal.aborted) return;
          const byId = new Map(roadRoutes.map(r => [r.optionId, r]));
          setMapState(prev => ({
            ...prev,
            candidateRoutes: (prev.candidateRoutes ?? []).map(r => byId.get(r.optionId) ?? r),
            selectedRoute: prev.selectedRoute ? (byId.get(prev.selectedRoute.optionId) ?? prev.selectedRoute) : prev.selectedRoute,
          }));
        });
      },
      onToken:      (text) => setReasonerText(prev => prev + text),
      onConclusion: (data) => setReasonerConclusion(data),
      onResolution: (data) => {
        setResolution(data);
        applyResolution(data, null, capturedFv, capturedOpt, signal, setMapState);
      },
      onError: (data) => { setErrorState(data); setIsDegraded(true); },
    };

    streamDemo(scenario.id, signal, streamCallbacks).then(result => {
      if (result === 'aborted') { streamDoneResolve('aborted'); return; }
      if (result === 'fallback') {
        setIsDegraded(true);
        setErrorState({ message: 'Reasoner Agent unavailable. Proceeding on Optimizer output alone — no chain of thought available.' });
        if (!animStarted) {
          setOptimizerOutput(mockOpt);
          runAnimation(mockFv);
          const { routes, topRoute } = buildMapRoutes(mockFv, mockOpt);
          setMapState(prev => ({
            ...prev,
            candidateRoutes: [...(prev.candidateRoutes ?? []), ...routes],
            selectedRoute: topRoute ?? prev.selectedRoute,
          }));
          hydrateRoutesWithRoadGeometry(routes).then((roadRoutes) => {
            if (signal.aborted) return;
            const byId = new Map(roadRoutes.map(r => [r.optionId, r]));
            setMapState(prev => ({
              ...prev,
              candidateRoutes: (prev.candidateRoutes ?? []).map(r => byId.get(r.optionId) ?? r),
              selectedRoute: prev.selectedRoute ? (byId.get(prev.selectedRoute.optionId) ?? prev.selectedRoute) : prev.selectedRoute,
            }));
          });
        }
        simulateMockStream(scenario.id, signal, streamCallbacks).then(() => streamDoneResolve('done'));
      } else {
        streamDoneResolve(result);
      }
    });

    await animPromise;
    if (signal.aborted) return;
    setPhase('deliberation');
    setIsStreaming(true);

    const streamResult = await streamDonePromise;
    if (streamResult === 'aborted' || signal.aborted) return;
    setIsStreaming(false);
    await delay(450);
    if (signal.aborted) return;
    setPhase('resolution');
  }, []);

  const startManualOrder = useCallback(async (orderData) => {
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const { signal } = controller;

    setActiveScenario({ id: 'manual', label: 'Manual Order', title: orderData.order_id });
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

    try {
      const enrichRes = await fetch(ENRICH_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData),
        signal,
      });
      if (signal.aborted) return;
      if (!enrichRes.ok) {
        const errData = await enrichRes.json().catch(() => ({}));
        setErrorState({ message: errData.detail || 'Enrichment failed. Check the destination address.' });
        setPhase('select');
        return;
      }
      const enrichData = await enrichRes.json();
      const fv = enrichData.feature_vector;

      const scoreRes = await fetch(SCORE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feature_vector: fv }),
        signal,
      });
      if (signal.aborted) return;
      if (!scoreRes.ok) { setErrorState({ message: 'Optimizer scoring failed.' }); setPhase('select'); return; }
      const scoreData = await scoreRes.json();
      const opt = scoreData.optimizer_output;
      if (!opt) { setErrorState({ message: 'No viable routing options found. Try a different location.' }); setPhase('select'); return; }

      setOptimizerOutput(opt);

      let resolveAnim;
      const animPromise = new Promise(res => { resolveAnim = res; });

      async function runAnimation() {
        setSignals(fv);
        setMapState(prev => ({
          ...prev,
          destination: { lat: fv.destination_lat, lon: fv.destination_lon, zone: fv.destination_zone_id },
          drivers: (fv.available_drivers ?? []).map(d => ({
            id: d.driver_id, name: d.name, lat: d.current_lat, lon: d.current_lon, vehicle_type: d.vehicle_type,
          })),
        }));
        const { routes, topRoute } = buildMapRoutes(fv, opt);
        setMapState(prev => ({
          ...prev,
          candidateRoutes: [...(prev.candidateRoutes ?? []), ...routes],
          selectedRoute: topRoute ?? prev.selectedRoute,
        }));
        hydrateRoutesWithRoadGeometry(routes).then((roadRoutes) => {
          if (signal.aborted) return;
          const byId = new Map(roadRoutes.map(r => [r.optionId, r]));
          setMapState(prev => ({
            ...prev,
            candidateRoutes: (prev.candidateRoutes ?? []).map(r => byId.get(r.optionId) ?? r),
            selectedRoute: prev.selectedRoute ? (byId.get(prev.selectedRoute.optionId) ?? prev.selectedRoute) : prev.selectedRoute,
          }));
        });
        for (let i = 1; i <= SIGNAL_COUNT; i++) {
          if (signal.aborted) { resolveAnim(); return; }
          await delay(SIGNAL_STAGGER_MS);
          setSignalRevealCount(i);
        }
        await delay(1200);
        resolveAnim();
      }

      let streamDoneResolve;
      const streamDonePromise = new Promise(res => { streamDoneResolve = res; });

      const streamCallbacks = {
        onToken:      (text) => setReasonerText(prev => prev + text),
        onConclusion: (data) => setReasonerConclusion(data),
        onResolution: (data) => {
          setResolution(data);
          applyResolution(data, null, fv, opt, signal, setMapState);
        },
        onError: (data) => { setErrorState(data); setIsDegraded(true); },
      };

      runAnimation();
      streamReasonerSSE(fv, opt, signal, streamCallbacks).then(result => {
        if (result === 'aborted') { streamDoneResolve('aborted'); return; }
        if (result === 'error') {
          setIsDegraded(true);
          setErrorState({ message: 'Reasoner Agent unavailable. Proceeding on Optimizer output alone.' });
        }
        streamDoneResolve(result);
      });

      await animPromise;
      if (signal.aborted) return;
      setPhase('deliberation');
      setIsStreaming(true);

      const streamResult = await streamDonePromise;
      if (streamResult === 'aborted' || signal.aborted) return;
      setIsStreaming(false);
      await delay(450);
      if (signal.aborted) return;
      setPhase('resolution');

    } catch (err) {
      if (!signal.aborted) { setErrorState({ message: err.message || 'Manual order failed. Please try again.' }); setPhase('select'); }
    }
  }, []);

  return {
    phase, activeScenario, signals, signalRevealCount, optimizerOutput,
    reasonerText, reasonerConclusion, resolution, errorState, isDegraded,
    isStreaming, mapState, startDeliberation, startManualOrder, reset,
  };
}
