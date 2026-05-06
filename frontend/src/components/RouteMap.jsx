import { useEffect, useRef, useState, Fragment } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-polylinedecorator';
import { formatWarehouse, formatDriver } from '../utils/formatters.js';

const BAY_AREA_CENTER = [37.7749, -122.4194];
const DEFAULT_ZOOM = 10;

const WAREHOUSES = [
  { id: 'WH-SF01',  name: 'SF Mission Fulfillment',       lat: 37.7599, lon: -122.4148 },
  { id: 'WH-OAK01', name: 'Oakland Harbor Distribution',  lat: 37.8044, lon: -122.2712 },
  { id: 'WH-SJ01',  name: 'San Jose Tech Corridor Depot', lat: 37.3382, lon: -121.8863 },
  { id: 'WH-SSF01', name: 'South SF Peninsula Hub',       lat: 37.6527, lon: -122.4477 },
  { id: 'WH-MRN01', name: 'Marin County Logistics',       lat: 37.9735, lon: -122.5311 },
];

const INITIAL_DRIVERS = [
  { id: 'DRV-001', name: 'Marcus Johnson',   lat: 37.7920, lon: -122.3985, vehicle_type: 'van',       available: true  },
  { id: 'DRV-002', name: 'Aisha Patel',      lat: 37.7588, lon: -122.4148, vehicle_type: 'van',       available: true  },
  { id: 'DRV-003', name: 'Carlos Rodriguez', lat: 37.3395, lon: -121.8910, vehicle_type: 'truck',     available: true  },
  { id: 'DRV-004', name: 'Mei Chen',         lat: 37.7855, lon: -122.4000, vehicle_type: 'motorbike', available: true  },
  { id: 'DRV-005', name: 'Jordan Williams',  lat: 37.9740, lon: -122.5315, vehicle_type: 'van',       available: true  },
  { id: 'DRV-006', name: 'Priya Sharma',     lat: 37.8040, lon: -122.2720, vehicle_type: 'truck',     available: false },
  { id: 'DRV-007', name: 'Diego Morales',    lat: 37.6688, lon: -122.0808, vehicle_type: 'van',       available: true  },
  { id: 'DRV-008', name: 'Yuki Tanaka',      lat: 37.8030, lon: -122.2410, vehicle_type: 'motorbike', available: true  },
  { id: 'DRV-009', name: 'Amara Okonkwo',    lat: 37.8305, lon: -122.2441, vehicle_type: 'van',       available: true  },
  { id: 'DRV-010', name: 'Tyler Nguyen',     lat: 37.6527, lon: -122.4477, vehicle_type: 'truck',     available: false },
  { id: 'DRV-011', name: 'Sofia Espinoza',   lat: 37.7599, lon: -122.4150, vehicle_type: 'van',       available: false },
  { id: 'DRV-012', name: 'Reza Ahmadi',      lat: 37.7880, lon: -122.4074, vehicle_type: 'motorbike', available: true  },
];

// ── Custom DivIcons ────────────────────────────────────────────────────────────

function makeWarehouseIcon() {
  return L.divIcon({
    className: '',
    html: `<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" aria-label="Warehouse">
      <polygon points="10,1 19,7 19,19 1,19 1,7" fill="#7c3aed" stroke="#a78bfa" stroke-width="1.5"/>
      <rect x="7" y="12" width="6" height="7" fill="#a78bfa"/>
      <polygon points="10,3 17,7.5 3,7.5" fill="#a78bfa"/>
    </svg>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    tooltipAnchor: [0, -10],
  });
}

function makeDriverIcon(available) {
  const fill   = available ? '#059669' : '#d97706';
  const stroke = available ? '#34d399' : '#fbbf24';
  return L.divIcon({
    className: '',
    html: `<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" aria-label="Driver">
      <circle cx="8" cy="8" r="7" fill="${fill}" stroke="${stroke}" stroke-width="1.5"/>
      <circle cx="8" cy="6" r="2.5" fill="white"/>
      <path d="M3.5,14 Q8,10 12.5,14" fill="white" stroke="none"/>
    </svg>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    tooltipAnchor: [0, -8],
  });
}

function makeDestinationIcon() {
  return L.divIcon({
    className: '',
    html: `<svg width="22" height="28" viewBox="0 0 22 28" xmlns="http://www.w3.org/2000/svg" aria-label="Destination">
      <path d="M11,0 C4.9,0 0,4.9 0,11 C0,19.3 11,28 11,28 C11,28 22,19.3 22,11 C22,4.9 17.1,0 11,0 Z" fill="#ef4444" stroke="#f87171" stroke-width="1"/>
      <circle cx="11" cy="11" r="4.5" fill="white"/>
      <circle cx="11" cy="11" r="2" fill="#ef4444"/>
    </svg>`,
    iconSize: [22, 28],
    iconAnchor: [11, 28],
    tooltipAnchor: [0, -28],
  });
}

// Create once at module level — icons are stateless
const WAREHOUSE_ICON    = makeWarehouseIcon();
const DESTINATION_ICON  = makeDestinationIcon();
const DRIVER_ICON_ON    = makeDriverIcon(true);
const DRIVER_ICON_OFF   = makeDriverIcon(false);

// ── Rank colour palette ────────────────────────────────────────────────────────

const RANK_PALETTE = ['#4b7fe0', '#22d3ee', '#f59e0b', '#ec4899'];
const rankColor = (rank) => RANK_PALETTE[(rank - 1) % RANK_PALETTE.length];

// ── Directional arrow decorator ────────────────────────────────────────────────

function ArrowDecorator({ positions, color, opacity = 1 }) {
  const map = useMap();
  useEffect(() => {
    if (!positions || positions.length < 2) return;
    if (!L.polylineDecorator || !L.Symbol?.arrowHead) return;
    const dec = L.polylineDecorator(positions, {
      patterns: [{
        offset: '50%',
        repeat: 0,
        symbol: L.Symbol.arrowHead({
          pixelSize: 10,
          polygon: false,
          pathOptions: { stroke: true, color, weight: 2, opacity },
        }),
      }],
    });
    dec.addTo(map);
    return () => { try { dec.remove(); } catch {} };
  }, [positions, color, opacity, map]);
  return null;
}

// ── Map behaviour components ───────────────────────────────────────────────────

function MapController({ mapState }) {
  const map = useMap();
  const prevDestRef    = useRef(null);
  const prevFinalRef   = useRef(null);
  const prevPreviewRef = useRef(undefined); // undefined sentinel so null triggers first run

  // Fly to destination when it first appears
  useEffect(() => {
    const dest = mapState?.destination;
    if (!dest) return;
    if (prevDestRef.current === dest) return;
    prevDestRef.current = dest;
    map.flyTo([dest.lat, dest.lon], 11, { duration: 1.2 });
  }, [mapState?.destination, map]);

  // Fit bounds to full final route (both legs) whenever it first resolves
  useEffect(() => {
    const fr = mapState?.finalRoute;
    if (!fr) return;
    if (prevFinalRef.current === fr) return;
    prevFinalRef.current = fr;

    const pts = [];
    if (fr.legACoords?.length) pts.push(...fr.legACoords);
    if (fr.legBCoords?.length) pts.push(...fr.legBCoords);
    if (pts.length === 0) {
      if (fr.driverLat && fr.driverLon) pts.push([fr.driverLat, fr.driverLon]);
      pts.push([fr.warehouseLat, fr.warehouseLon]);
      pts.push([fr.destLat,      fr.destLon]);
    }
    if (pts.length >= 2) {
      map.fitBounds(pts, { padding: [60, 60], maxZoom: 14, animate: true, duration: 1 });
    }
  }, [mapState?.finalRoute, map]);

  // Rezoom to fit whichever route the user selects from the scoring cards
  useEffect(() => {
    const previewRouteId = mapState?.previewRouteId;
    if (prevPreviewRef.current === previewRouteId) return;
    prevPreviewRef.current = previewRouteId;

    const finalRoute = mapState?.finalRoute;
    if (!finalRoute) return; // not in resolution yet

    const pts = [];

    if (!previewRouteId || previewRouteId === finalRoute.optionId) {
      // No selection, or best route explicitly selected — fit to final route
      if (finalRoute.legACoords?.length) pts.push(...finalRoute.legACoords);
      if (finalRoute.legBCoords?.length) pts.push(...finalRoute.legBCoords);
      if (pts.length === 0) {
        if (finalRoute.driverLat && finalRoute.driverLon) pts.push([finalRoute.driverLat, finalRoute.driverLon]);
        pts.push([finalRoute.warehouseLat, finalRoute.warehouseLon]);
        pts.push([finalRoute.destLat,      finalRoute.destLon]);
      }
    } else {
      // Alternate selected — fit to that route's geometry
      const route = (mapState?.candidateRoutes ?? []).find(r => r.optionId === previewRouteId);
      if (!route) return;
      if (route.legACoords?.length) pts.push(...route.legACoords);
      if (route.pathCoords?.length) pts.push(...route.pathCoords);
      if (pts.length === 0) {
        if (route.driverLat && route.driverLon) pts.push([route.driverLat, route.driverLon]);
        pts.push([route.warehouseLat, route.warehouseLon]);
        pts.push([route.destLat,      route.destLon]);
      }
    }

    if (pts.length >= 2) {
      map.fitBounds(pts, { padding: [60, 60], maxZoom: 14, animate: true, duration: 1 });
    }
  }, [mapState?.previewRouteId, mapState?.finalRoute, mapState?.candidateRoutes, map]);

  return null;
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function RouteMap({ mapState }) {
  const [showFinalDetails, setShowFinalDetails] = useState(false);
  const [expandFinalDetails, setExpandFinalDetails] = useState(false);

  const dest            = mapState?.destination;
  const drivers         = mapState?.drivers ?? [];
  const candidateRoutes = mapState?.candidateRoutes ?? [];
  const finalRoute      = mapState?.finalRoute;
  const isResolved      = !!finalRoute;

  // Route selected via scoring-card click (null = best route / default)
  const previewRoute = isResolved && mapState?.previewRouteId
    ? (candidateRoutes.find(r => r.optionId === mapState.previewRouteId) ?? null)
    : null;

  // When the top/best route is explicitly selected we still show the final route geometry
  const isBestSelected   = !!previewRoute && previewRoute.optionId === finalRoute?.optionId;
  // Show final route when nothing is selected OR the best is explicitly selected
  const showFinalOnMap   = !isResolved || !previewRoute || isBestSelected;
  // Show an alternate overlay when a non-final candidate is selected
  const alternatePreview = previewRoute && !isBestSelected ? previewRoute : null;

  const legBPositions = (route) => (
    route?.legBCoords?.length >= 2 ? route.legBCoords :
    route?.pathCoords?.length  >= 2 ? route.pathCoords :
    [[route.warehouseLat, route.warehouseLon], [route.destLat, route.destLon]]
  );

  const displayDrivers = drivers.length > 0 ? drivers : INITIAL_DRIVERS;

  const decisionColor =
    finalRoute?.decision === 'confirm' ? '#34d399' :
    finalRoute?.decision === 'qualify' ? '#fbbf24' : '#f87171';

  const decisionLabel =
    finalRoute?.decision === 'confirm'  ? 'Confirmed' :
    finalRoute?.decision === 'qualify'  ? 'Confirmed with Conditions' :
    finalRoute?.decision === 'override' ? 'Override Applied' : 'Pending';

  return (
    <div className="route-map-shell">
      <MapContainer
        center={BAY_AREA_CENTER}
        zoom={DEFAULT_ZOOM}
        zoomControl={false}
        attributionControl={false}
        className="route-map"
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
          maxZoom={19}
        />
        <MapController mapState={mapState} />

        {/* Warehouses — pentagon/house shape */}
        {WAREHOUSES.map(wh => (
          <Marker key={wh.id} position={[wh.lat, wh.lon]} icon={WAREHOUSE_ICON}>
            <Tooltip direction="top" offset={[0, -4]} opacity={0.95}>
              <span style={{ fontSize: 11, fontWeight: 600 }}>■ {wh.name}</span><br />
              <span style={{ fontSize: 10, color: '#9ca3af' }}>{wh.id}</span>
            </Tooltip>
          </Marker>
        ))}

        {/* Drivers — circle with person silhouette */}
        {displayDrivers.map(drv => (
          <Marker
            key={drv.id}
            position={[drv.lat, drv.lon]}
            icon={drv.available !== false ? DRIVER_ICON_ON : DRIVER_ICON_OFF}
          >
            <Tooltip direction="top" offset={[0, -4]} opacity={0.95}>
              <span style={{ fontSize: 11, fontWeight: 600 }}>● {drv.name}</span><br />
              <span style={{ fontSize: 10 }}>{drv.vehicle_type}{drv.available === false ? ' — on delivery' : ''}</span>
            </Tooltip>
          </Marker>
        ))}

        {/* Destination — teardrop pin */}
        {dest && (
          <Marker position={[dest.lat, dest.lon]} icon={DESTINATION_ICON}>
            <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
              <span style={{ fontSize: 11, fontWeight: 700 }}>▼ Destination</span><br />
              <span style={{ fontSize: 10 }}>{dest.zone}</span>
            </Tooltip>
          </Marker>
        )}

        {/* Candidate routes — only rendered during deliberation; hidden after resolution */}
        {!isResolved && candidateRoutes.map((route) => {
          const color   = rankColor(route.rank);
          const isTop   = route.rank === 1;
          const bWeight  = isTop ? 3.5 : 2;
          const bOpacity = isTop ? 1.0 : 0.65;
          const aOpacity = isTop ? 0.8 : 0.5;

          return (
            <Fragment key={route.optionId}>
              {/* Leg A: driver → warehouse (dashed) */}
              {route.legACoords?.length >= 2 && (
                <Polyline
                  positions={route.legACoords}
                  pathOptions={{ color, weight: isTop ? 2.5 : 1.5, dashArray: '8 5', opacity: aOpacity, lineCap: 'round' }}
                />
              )}
              {route.legACoords?.length >= 2 && (
                <ArrowDecorator positions={route.legACoords} color={color} opacity={aOpacity} />
              )}
              {/* Leg B: warehouse → destination */}
              <Polyline
                positions={legBPositions(route)}
                pathOptions={{ color, weight: bWeight, dashArray: isTop ? undefined : '6 4', opacity: bOpacity, lineCap: 'round' }}
              >
                <Tooltip sticky opacity={0.9}>
                  <span style={{ fontSize: 10, fontWeight: 600 }}>Rank {route.rank}</span><br />
                  <span style={{ fontSize: 10 }}>{formatWarehouse(route.warehouseId, route.warehouseName)}</span><br />
                  <span style={{ fontSize: 10 }}>{formatDriver(route.driverId, route.driverName)}</span><br />
                  <span style={{ fontSize: 10, color: '#9ca3af' }}>Score: {route.score?.toFixed(3)}</span>
                </Tooltip>
              </Polyline>
              <ArrowDecorator positions={legBPositions(route)} color={color} opacity={bOpacity} />
            </Fragment>
          );
        })}

        {/* Alternate preview — only rendered when a non-final candidate is selected */}
        {alternatePreview && (
          <Fragment key={`preview-${alternatePreview.optionId}`}>
            {alternatePreview.legACoords?.length >= 2 && (
              <Polyline
                positions={alternatePreview.legACoords}
                pathOptions={{ color: rankColor(alternatePreview.rank), weight: 2.5, dashArray: '8 5', opacity: 0.8, lineCap: 'round' }}
              />
            )}
            {alternatePreview.legACoords?.length >= 2 && (
              <ArrowDecorator positions={alternatePreview.legACoords} color={rankColor(alternatePreview.rank)} opacity={0.8} />
            )}
            <Polyline
              positions={legBPositions(alternatePreview)}
              pathOptions={{ color: rankColor(alternatePreview.rank), weight: 4, dashArray: '6 4', opacity: 0.9, lineCap: 'round' }}
            >
              <Tooltip sticky opacity={0.95}>
                <span style={{ fontSize: 10, fontWeight: 600 }}>Rank {alternatePreview.rank} — Alternate</span><br />
                <span style={{ fontSize: 10 }}>{formatWarehouse(alternatePreview.warehouseId, alternatePreview.warehouseName)}</span><br />
                <span style={{ fontSize: 10 }}>{formatDriver(alternatePreview.driverId, alternatePreview.driverName)}</span><br />
                <span style={{ fontSize: 10, color: '#9ca3af' }}>Score: {alternatePreview.score?.toFixed(3)}</span>
              </Tooltip>
            </Polyline>
            <ArrowDecorator positions={legBPositions(alternatePreview)} color={rankColor(alternatePreview.rank)} opacity={0.9} />
          </Fragment>
        )}

        {/* Final route — only shown when no alternate is being previewed */}
        {showFinalOnMap && finalRoute?.legACoords?.length >= 2 && (
          <Polyline
            positions={finalRoute.legACoords}
            pathOptions={{ color: '#22d3ee', weight: 4, dashArray: '8 5', opacity: 0.85, lineCap: 'round' }}
          >
            <Tooltip sticky opacity={0.95}>
              <span style={{ fontSize: 10, fontWeight: 700 }}>Leg A — Driver pickup</span><br />
              <span style={{ fontSize: 10 }}>{formatDriver(finalRoute.driverId, finalRoute.driverName)}</span>
              <span style={{ fontSize: 10 }}> → {formatWarehouse(finalRoute.warehouseId, finalRoute.warehouseName)}</span>
            </Tooltip>
          </Polyline>
        )}
        {showFinalOnMap && finalRoute && (
          <Polyline
            positions={legBPositions(finalRoute)}
            pathOptions={{ color: decisionColor, weight: 7, opacity: 1.0, lineCap: 'round' }}
            eventHandlers={{ click: () => { setShowFinalDetails(true); setExpandFinalDetails(true); } }}
          >
            <Tooltip sticky opacity={0.95}>
              <span style={{ fontSize: 10, fontWeight: 700 }}>Leg B — Delivery</span><br />
              <span style={{ fontSize: 10 }}>{formatWarehouse(finalRoute.warehouseId, finalRoute.warehouseName)}</span>
              <span style={{ fontSize: 10 }}> → Destination</span><br />
              <span style={{ fontSize: 10, color: '#9ca3af' }}>Click for details</span>
            </Tooltip>
          </Polyline>
        )}
      </MapContainer>

      {/* Map legend */}
      <div className="map-legend">
        <div className="map-legend-item"><span style={{ color: '#a78bfa' }}>■</span> Warehouse</div>
        <div className="map-legend-item"><span style={{ color: '#34d399' }}>●</span> Driver (available)</div>
        <div className="map-legend-item"><span style={{ color: '#fbbf24' }}>●</span> Driver (busy)</div>
        <div className="map-legend-item"><span style={{ color: '#ef4444' }}>▼</span> Destination</div>
        {candidateRoutes.length > 0 && !isResolved && (
          <div className="map-legend-item">
            {[1, 2, 3, 4].map(r => (
              <span key={r} style={{ color: rankColor(r), marginRight: 2 }}>■</span>
            ))}
            Candidates (rank 1→4)
          </div>
        )}
        {alternatePreview && (
          <div className="map-legend-item">
            <span style={{ color: rankColor(alternatePreview.rank) }}>╌</span> Rank {alternatePreview.rank} preview
          </div>
        )}
        {showFinalOnMap && finalRoute && <div className="map-legend-item"><span style={{ color: '#22d3ee' }}>╌</span> Pickup leg</div>}
        {showFinalOnMap && finalRoute && <div className="map-legend-item" style={{ color: decisionColor }}>━ Delivery leg</div>}
      </div>

      {/* Stacked detail cards (bottom-right) */}
      <div className="route-cards-stack">
        {alternatePreview && (
          <div className="alternate-route-card visible">
            <div className="final-route-card-header" style={{ borderLeft: `3px solid ${rankColor(alternatePreview.rank)}` }}>
              <span className="final-route-card-title" style={{ color: rankColor(alternatePreview.rank) }}>
                Rank {alternatePreview.rank} — Alternate
              </span>
              <span className="final-route-card-pill" style={{ color: rankColor(alternatePreview.rank) }}>
                {alternatePreview.score?.toFixed(3)}
              </span>
              <span className="final-route-card-chevron" />
            </div>
            <div className="final-route-card-body">
              <div><strong>ETA:</strong> {alternatePreview.etaHours ? `${alternatePreview.etaHours.toFixed(1)}h` : 'N/A'}</div>
              <div><strong>Cost:</strong> {alternatePreview.cost ? `$${alternatePreview.cost.toFixed(2)}` : 'N/A'}</div>
              {alternatePreview.lesser_reason && (
                <div className="final-route-card-reason">
                  <strong>Why not chosen:</strong> {alternatePreview.lesser_reason}
                </div>
              )}
            </div>
          </div>
        )}

        {showFinalOnMap && finalRoute && (
          <div className={`final-route-card ${showFinalDetails ? 'visible' : ''}`}>
            <button
              type="button"
              className="final-route-card-header"
              onClick={() => setExpandFinalDetails(prev => !prev)}
            >
              <span className="final-route-card-title">Final Route</span>
              <span className="final-route-card-pill">{decisionLabel}</span>
              <span className="final-route-card-chevron">{expandFinalDetails ? '▾' : '▸'}</span>
            </button>
            {expandFinalDetails && (
              <div className="final-route-card-body">
                <div className="final-route-leg"><strong>Leg A (pickup):</strong> {formatDriver(finalRoute.driverId, finalRoute.driverName)} → {formatWarehouse(finalRoute.warehouseId, finalRoute.warehouseName)}</div>
                <div className="final-route-leg"><strong>Leg B (delivery):</strong> {formatWarehouse(finalRoute.warehouseId, finalRoute.warehouseName)} → Destination</div>
                <div><strong>ETA:</strong>   {finalRoute.etaHours ? `${finalRoute.etaHours.toFixed(1)}h` : 'N/A'}</div>
                <div><strong>Cost:</strong>  {finalRoute.cost ? `$${finalRoute.cost.toFixed(2)}` : 'N/A'}</div>
                {finalRoute.score && <div><strong>Score:</strong> {finalRoute.score.toFixed(3)}</div>}
                {finalRoute.reason && <div className="final-route-card-reason"><strong>Why:</strong> {finalRoute.reason}</div>}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
