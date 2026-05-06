import { useState, useRef, useCallback } from 'react';
import { MOCK_DATA } from '../mockData.js';
import { parseSSEBuffer } from '../utils/sseParser.js';

const DEMO_URL = (id) => `/api/reasoner/demo/${id}`;
const SIGNAL_STAGGER_MS = 200;
const SIGNAL_COUNT = 8;

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
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
    await delay(isNewline ? 120 : 28 + Math.random() * 20);
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
      for (let i = 1; i <= SIGNAL_COUNT; i++) {
        if (signal.aborted) { resolveAnim(); return; }
        await delay(SIGNAL_STAGGER_MS);
        setSignalRevealCount(i);
      }
      await delay(700);
      resolveAnim();
    }

    // streamDonePromise resolves when the SSE stream (or mock fallback) ends.
    let streamDoneResolve;
    const streamDonePromise = new Promise(res => { streamDoneResolve = res; });

    const streamCallbacks = {
      onScenarioData: (data) => {
        setOptimizerOutput(data.optimizer_output ?? mockOpt);
        runAnimation(data.feature_vector ?? mockFv); // fire-and-forget alongside stream
      },
      onToken:      (text) => setReasonerText(prev => prev + text),
      onConclusion: (data) => setReasonerConclusion(data),
      onResolution: (data) => setResolution(data),
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
    startDeliberation,
    reset,
  };
}
