import { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const BAY_AREA_CENTER = [37.7749, -122.4194];
const DEFAULT_ZOOM = 10;

// All 5 Bay Area warehouses — always rendered
const WAREHOUSES = [
  { id: 'WH-SF01',  name: 'SF Mission Fulfillment',       lat: 37.7599, lon: -122.4148 },
  { id: 'WH-OAK01', name: 'Oakland Harbor Distribution',  lat: 37.8044, lon: -122.2712 },
  { id: 'WH-SJ01',  name: 'San Jose Tech Corridor Depot', lat: 37.3382, lon: -121.8863 },
  { id: 'WH-SSF01', name: 'South SF Peninsula Hub',       lat: 37.6527, lon: -122.4477 },
  { id: 'WH-MRN01', name: 'Marin County Logistics',       lat: 37.9735, lon: -122.5311 },
];

// All 12 Bay Area seed data drivers — shown before any scenario starts
const INITIAL_DRIVERS = [
  { id: 'DRV-001', name: 'Marcus Johnson',   lat: 37.7920, lon: -122.3985, vehicle_type: 'van',       available: true },
  { id: 'DRV-002', name: 'Aisha Patel',      lat: 37.7588, lon: -122.4148, vehicle_type: 'van',       available: true },
  { id: 'DRV-003', name: 'Carlos Rodriguez', lat: 37.3395, lon: -121.8910, vehicle_type: 'truck',     available: true },
  { id: 'DRV-004', name: 'Mei Chen',         lat: 37.7855, lon: -122.4000, vehicle_type: 'motorbike', available: true },
  { id: 'DRV-005', name: 'Jordan Williams',  lat: 37.9740, lon: -122.5315, vehicle_type: 'van',       available: true },
  { id: 'DRV-006', name: 'Priya Sharma',     lat: 37.8040, lon: -122.2720, vehicle_type: 'truck',     available: false },
  { id: 'DRV-007', name: 'Diego Morales',    lat: 37.6688, lon: -122.0808, vehicle_type: 'van',       available: true },
  { id: 'DRV-008', name: 'Yuki Tanaka',      lat: 37.8030, lon: -122.2410, vehicle_type: 'motorbike', available: true },
  { id: 'DRV-009', name: 'Amara Okonkwo',    lat: 37.8305, lon: -122.2441, vehicle_type: 'van',       available: true },
  { id: 'DRV-010', name: 'Tyler Nguyen',     lat: 37.6527, lon: -122.4477, vehicle_type: 'truck',     available: false },
  { id: 'DRV-011', name: 'Sofia Espinoza',   lat: 37.7599, lon: -122.4150, vehicle_type: 'van',       available: false },
  { id: 'DRV-012', name: 'Reza Ahmadi',      lat: 37.7880, lon: -122.4074, vehicle_type: 'motorbike', available: true },
];

function MapBounds({ mapState }) {
  const map = useMap();
  useEffect(() => {
    if (mapState?.destination) {
      map.flyTo([mapState.destination.lat, mapState.destination.lon], 11, { duration: 1.2 });
    }
  }, [mapState?.destination, map]);
  return null;
}

export default function RouteMap({ mapState }) {
  const dest = mapState?.destination;
  const drivers = mapState?.drivers ?? [];
  const candidateRoutes = mapState?.candidateRoutes ?? [];
  const selectedRoute = mapState?.selectedRoute;
  const finalRoute = mapState?.finalRoute;

  // Show all 12 seed drivers when no scenario has started yet
  const displayDrivers = (drivers.length > 0) ? drivers : INITIAL_DRIVERS;

  return (
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
      <MapBounds mapState={mapState} />

      {/* Warehouses — always visible */}
      {WAREHOUSES.map(wh => (
        <CircleMarker
          key={wh.id}
          center={[wh.lat, wh.lon]}
          radius={7}
          pathOptions={{ color: '#a78bfa', fillColor: '#7c3aed', fillOpacity: 0.85, weight: 2 }}
        >
          <Tooltip direction="top" offset={[0, -8]} opacity={0.9}>
            <span style={{ fontSize: 11, fontWeight: 600 }}>{wh.id}</span><br />
            <span style={{ fontSize: 10 }}>{wh.name}</span>
          </Tooltip>
        </CircleMarker>
      ))}

      {/* Drivers/dashers — shows INITIAL_DRIVERS before scenario, scenario drivers after */}
      {displayDrivers.map(drv => (
        <CircleMarker
          key={drv.id}
          center={[drv.lat, drv.lon]}
          radius={drv.available !== false ? 5 : 4}
          pathOptions={{
            color: drv.available !== false ? '#34d399' : '#fbbf24',
            fillColor: drv.available !== false ? '#059669' : '#d97706',
            fillOpacity: drv.available !== false ? 0.8 : 0.5,
            weight: 1.5,
          }}
        >
          <Tooltip direction="top" offset={[0, -6]} opacity={0.9}>
            <span style={{ fontSize: 10 }}>
              {drv.name} ({drv.vehicle_type})
              {drv.available === false ? ' — on delivery' : ''}
            </span>
          </Tooltip>
        </CircleMarker>
      ))}

      {/* Destination */}
      {dest && (
        <CircleMarker
          center={[dest.lat, dest.lon]}
          radius={9}
          pathOptions={{ color: '#f87171', fillColor: '#ef4444', fillOpacity: 0.9, weight: 2.5 }}
        >
          <Tooltip direction="top" offset={[0, -10]} opacity={0.9} permanent={false}>
            <span style={{ fontSize: 11, fontWeight: 700 }}>Destination</span><br />
            <span style={{ fontSize: 10 }}>{dest.zone}</span>
          </Tooltip>
        </CircleMarker>
      )}

      {/* Candidate routes (additive, grey dashes) */}
      {candidateRoutes.map((route) => (
        <Polyline
          key={route.optionId}
          positions={[[route.warehouseLat, route.warehouseLon], [route.destLat, route.destLon]]}
          pathOptions={{
            color: '#4b5563',
            weight: route.rank === 1 ? 2.5 : 1.5,
            dashArray: '6 4',
            opacity: 0.7,
          }}
        >
          <Tooltip sticky opacity={0.9}>
            <span style={{ fontSize: 10 }}>Rank {route.rank}: {route.optionId}</span><br />
            <span style={{ fontSize: 10 }}>Score: {route.score?.toFixed(3)}</span>
          </Tooltip>
        </Polyline>
      ))}

      {/* Selected route (top choice — highlighted blue) */}
      {selectedRoute && (
        <Polyline
          positions={[[selectedRoute.warehouseLat, selectedRoute.warehouseLon], [selectedRoute.destLat, selectedRoute.destLon]]}
          pathOptions={{ color: '#4b7fe0', weight: 3.5, opacity: 0.9 }}
        />
      )}

      {/* Final route (resolution — bright green/amber/red) */}
      {finalRoute && (
        <Polyline
          positions={[[finalRoute.warehouseLat, finalRoute.warehouseLon], [finalRoute.destLat, finalRoute.destLon]]}
          pathOptions={{
            color: finalRoute.decision === 'confirm' ? '#34d399' :
                   finalRoute.decision === 'qualify' ? '#fbbf24' : '#f87171',
            weight: 5,
            opacity: 1.0,
          }}
        />
      )}
    </MapContainer>
  );
}
