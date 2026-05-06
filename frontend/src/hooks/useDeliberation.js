import { useState, useRef, useCallback } from 'react';
import { MOCK_DATA } from '../mockData.js';
import { parseSSEBuffer } from '../utils/sseParser.js';

const INTAKE_URL = 'http://localhost:8002/enrich';
const OPTIMIZER_URL = 'http://localhost:8003/score';
const REASONER_URL = 'http://localhost:8004/reason';

const SIGNAL_STAGGER_MS = 200;
const SIGNAL_COUNT = 8;

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchIntake(order, signal) {
  try {
    const res = await fetch(INTAKE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
      signal,
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.feature_vector ?? null;
  } catch {
    return null;
  }
}

async function fetchOptimizer(featureVector, signal) {
  try {
    const res = await fetch(OPTIMIZER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feature_vector: featureVector }),
      signal,
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.optimizer_output ?? null;
  } catch {
    return null;
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
    await delay(isNewline ? 120 : 28 + Math.random() * 20);
  }

  await delay(350);
  if (abortSignal.aborted) return;
  onConclusion(reasonerStream.conclusion);

  await delay(450);
  if (abortSignal.aborted) return;
  onResolution(reasonerStream.resolution);
}

async function streamReasoner(featureVector, optimizerOutput, scenarioId, abortSignal, callbacks) {
  const { onToken, onConclusion, onResolution, onError } = callbacks;

  try {
    const res = await fetch(REASONER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify({ feature_vector: featureVector, optimizer_output: optimizerOutput }),
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
          case 'token':
            onToken(data.text ?? '');
            break;
          case 'conclusion':
            onConclusion(data);
            break;
          case 'resolution':
            onResolution(data);
            break;
          case 'error':
            onError(data);
            break;
          case 'done':
            return 'done';
        }
      }
    }
    return 'done';
  } catch {
    if (abortSignal.aborted) return 'aborted';
    await simulateMockStream(scenarioId, abortSignal, callbacks);
    return 'done';
  }
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

    const mockFv = MOCK_DATA[scenario.id].featureVector;
    const mockOpt = MOCK_DATA[scenario.id].optimizerOutput;

    const liveFeatureVector = await fetchIntake(scenario.order, signal);
    if (signal.aborted) return;
    const featureVector = liveFeatureVector ?? mockFv;

    setSignals(featureVector);

    for (let i = 1; i <= SIGNAL_COUNT; i++) {
      if (signal.aborted) return;
      await delay(SIGNAL_STAGGER_MS);
      setSignalRevealCount(i);
    }

    await delay(700);
    if (signal.aborted) return;

    const liveOptimizer = await fetchOptimizer(featureVector, signal);
    if (signal.aborted) return;

    const optimizerData = (liveOptimizer && liveOptimizer.ranked_options?.length) ? liveOptimizer : mockOpt;
    setOptimizerOutput(optimizerData);
    setPhase('deliberation');
    setIsStreaming(true);

    const callbacks = {
      onToken: (text) => setReasonerText(prev => prev + text),
      onConclusion: (data) => setReasonerConclusion(data),
      onResolution: (data) => setResolution(data),
      onError: (data) => { setErrorState(data); setIsDegraded(true); },
    };

    const result = await streamReasoner(featureVector, optimizerData, scenario.id, signal, callbacks);
    if (result === 'aborted') return;

    setIsStreaming(false);
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
    startDeliberation,
    reset,
  };
}
