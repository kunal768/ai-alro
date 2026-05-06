const DEFAULT_ORS_BASE_URL = 'https://api.openrouteservice.org';
const DEFAULT_PROFILE = 'driving-car';
const REQUEST_TIMEOUT_MS = 6000;

const routeCache = new Map();
const inflightCache = new Map();

function toKey(from, to, profile) {
  return `${profile}:${from.lat.toFixed(6)},${from.lon.toFixed(6)}>${to.lat.toFixed(6)},${to.lon.toFixed(6)}`;
}

function straightLine(from, to) {
  return [
    [from.lat, from.lon],
    [to.lat, to.lon],
  ];
}

function getEnv() {
  const apiKey = import.meta.env.VITE_ORS_API_KEY ?? '';
  const baseUrl = import.meta.env.VITE_ORS_BASE_URL ?? DEFAULT_ORS_BASE_URL;
  const profile = import.meta.env.VITE_ORS_PROFILE ?? DEFAULT_PROFILE;
  return { apiKey, baseUrl, profile };
}

function withTimeout(signal, timeoutMs) {
  const timeoutController = new AbortController();
  const timer = setTimeout(() => timeoutController.abort(), timeoutMs);
  const merged = signal
    ? AbortSignal.any([signal, timeoutController.signal])
    : timeoutController.signal;
  return {
    signal: merged,
    clear: () => clearTimeout(timer),
  };
}

async function fetchGeoJsonRoute(from, to, env, signal) {
  const url = `${env.baseUrl}/v2/directions/${env.profile}/geojson`;
  const body = {
    coordinates: [
      [from.lon, from.lat],
      [to.lon, to.lat],
    ],
  };
  const request = withTimeout(signal, REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: env.apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: request.signal,
    });
    if (!res.ok) throw new Error(`ORS ${res.status}`);
    const json = await res.json();
    const coords = json?.features?.[0]?.geometry?.coordinates;
    if (!Array.isArray(coords) || coords.length < 2) throw new Error('invalid geometry');
    return coords.map(([lon, lat]) => [lat, lon]);
  } finally {
    request.clear();
  }
}

export async function fetchRoadGeometry(from, to, options = {}) {
  const env = getEnv();
  const profile = options.profile ?? env.profile;
  const key = toKey(from, to, profile);

  if (routeCache.has(key)) return routeCache.get(key);
  if (inflightCache.has(key)) return inflightCache.get(key);

  const fallback = straightLine(from, to);
  if (!env.apiKey) {
    routeCache.set(key, fallback);
    return fallback;
  }

  const task = fetchGeoJsonRoute(from, to, { ...env, profile }, options.signal)
    .catch(() => fallback)
    .then((coords) => {
      routeCache.set(key, coords);
      inflightCache.delete(key);
      return coords;
    });

  inflightCache.set(key, task);
  return task;
}

export function clearRoadGeometryCache() {
  routeCache.clear();
  inflightCache.clear();
}
