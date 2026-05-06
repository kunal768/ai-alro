import { useRef, useState } from 'react';
import { SCENARIOS } from '../scenarios.js';

// Maps weight ranges to a representative kg value passed to the backend
const WEIGHT_RANGES = [
  { label: '0 – 10 lbs  (light package)', kg: 4 },
  { label: '10 – 25 lbs (small box)',     kg: 16 },
  { label: '25 – 50 lbs (medium box)',    kg: 34 },
  { label: '50 – 100 lbs (large box)',    kg: 68 },
  { label: '100+ lbs (freight)',          kg: 91 },
];

// Nominatim bounded search — restricts suggestions to Bay Area
const BAY_AREA_VIEWBOX = '-122.9,38.3,-121.4,36.9'; // lon_min,lat_max,lon_max,lat_min
const BAY_AREA_BOUNDS  = { latMin: 36.9, latMax: 38.3, lonMin: -122.9, lonMax: -121.4 };

const BAY_AREA_PRESETS = [
  { label: 'Union Square, SF',  lat: 37.788,  lon: -122.4074 },
  { label: 'Oakland Downtown',  lat: 37.8044, lon: -122.2712 },
  { label: 'San Jose Downtown', lat: 37.3382, lon: -121.8863 },
  { label: 'Palo Alto',         lat: 37.4419, lon: -122.143  },
  { label: 'Berkeley',          lat: 37.8716, lon: -122.272  },
  { label: 'Hayward',           lat: 37.6688, lon: -122.0808 },
];

let _manualCounter = 1;

function isInBayArea(lat, lon) {
  return lat >= BAY_AREA_BOUNDS.latMin && lat <= BAY_AREA_BOUNDS.latMax &&
         lon >= BAY_AREA_BOUNDS.lonMin && lon <= BAY_AREA_BOUNDS.lonMax;
}

async function geocodeAddress(query) {
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5&viewbox=${BAY_AREA_VIEWBOX}&bounded=1&addressdetails=0`;
  const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
  if (!res.ok) return [];
  const data = await res.json();
  return data.map(r => ({
    label: r.display_name,
    lat: parseFloat(r.lat),
    lon: parseFloat(r.lon),
  }));
}

function AddressSearch({ value, onChange, onSelect, isSearching, suggestions }) {
  return (
    <div className="address-search-wrap">
      <input
        className="manual-field-input"
        type="text"
        placeholder="e.g. 123 Market St, San Francisco"
        value={value}
        onChange={onChange}
        autoComplete="off"
      />
      {isSearching && <div className="address-search-spinner" />}
      {suggestions.length > 0 && (
        <ul className="address-suggestions">
          {suggestions.map((s, i) => (
            <li
              key={i}
              className="address-suggestion-item"
              onMouseDown={() => onSelect(s)}
            >
              {s.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ManualOrderForm({ onSubmit }) {
  const [addressText, setAddressText]       = useState('');
  const [suggestions, setSuggestions]       = useState([]);
  const [isSearching, setIsSearching]       = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [orderId, setOrderId]               = useState('');
  const [priority, setPriority]             = useState('standard');
  const [orderValue, setOrderValue]         = useState('500');
  const [weightRange, setWeightRange]       = useState(0); // index into WEIGHT_RANGES
  const [error, setError]                   = useState('');
  const debounceRef = useRef(null);

  function handleAddressChange(e) {
    const val = e.target.value;
    setAddressText(val);
    setSelectedLocation(null);
    setError('');
    clearTimeout(debounceRef.current);
    if (val.trim().length < 3) { setSuggestions([]); return; }
    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try { setSuggestions(await geocodeAddress(val)); }
      catch { setSuggestions([]); }
      finally { setIsSearching(false); }
    }, 300);
  }

  function selectSuggestion(s) {
    setAddressText(s.label);
    setSelectedLocation(s);
    setSuggestions([]);
    setError('');
  }

  function applyPreset(p) {
    setAddressText(p.label);
    setSelectedLocation({ lat: p.lat, lon: p.lon, label: p.label });
    setSuggestions([]);
    setError('');
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!selectedLocation) {
      setError('Please select an address from the dropdown suggestions, or click a quick-pick preset.');
      return;
    }
    if (!isInBayArea(selectedLocation.lat, selectedLocation.lon)) {
      setError('That address is outside the Bay Area service region. Please choose a Bay Area location.');
      return;
    }
    setError('');
    const id = orderId.trim() || `ORD-MANUAL-${String(_manualCounter++).padStart(3, '0')}`;
    onSubmit({
      order_id: id,
      destination_lat: selectedLocation.lat,
      destination_lon: selectedLocation.lon,
      priority,
      order_value: parseFloat(orderValue) || 500,
      weight_kg: WEIGHT_RANGES[weightRange].kg,
      time_window_hours: 12,
      cargo_type: 'general',
    });
  }

  return (
    <form className="manual-order-form" onSubmit={handleSubmit}>
      <div className="manual-order-presets">
        <div className="manual-preset-label">Quick pick:</div>
        <div className="manual-preset-buttons">
          {BAY_AREA_PRESETS.map(p => (
            <button key={p.label} type="button" className="manual-preset-btn" onClick={() => applyPreset(p)}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="manual-order-fields">
        <div className="manual-field-row" style={{ gridColumn: '1 / -1' }}>
          <label className="manual-field-label">
            Delivery Address <span className="manual-field-optional">(Bay Area only)</span>
          </label>
          <AddressSearch
            value={addressText}
            onChange={handleAddressChange}
            onSelect={selectSuggestion}
            isSearching={isSearching}
            suggestions={suggestions}
          />
          {selectedLocation && (
            <div className="address-selected-badge">
              ✓ {selectedLocation.lat.toFixed(4)}, {selectedLocation.lon.toFixed(4)}
            </div>
          )}
        </div>

        <div className="manual-field-row">
          <label className="manual-field-label">Package Weight</label>
          <select
            className="manual-field-input"
            value={weightRange}
            onChange={e => setWeightRange(Number(e.target.value))}
          >
            {WEIGHT_RANGES.map((r, i) => (
              <option key={i} value={i}>{r.label}</option>
            ))}
          </select>
        </div>

        <div className="manual-field-row">
          <label className="manual-field-label">Priority</label>
          <select
            className="manual-field-input"
            value={priority}
            onChange={e => setPriority(e.target.value)}
          >
            <option value="standard">Standard</option>
            <option value="urgent">Urgent</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div className="manual-field-row">
          <label className="manual-field-label">Order Value ($)</label>
          <input
            className="manual-field-input"
            type="number"
            min="0"
            step="10"
            value={orderValue}
            onChange={e => setOrderValue(e.target.value)}
          />
        </div>

        <div className="manual-field-row">
          <label className="manual-field-label">Order ID <span className="manual-field-optional">(optional)</span></label>
          <input
            className="manual-field-input"
            type="text"
            placeholder="Auto-generated if blank"
            value={orderId}
            onChange={e => setOrderId(e.target.value)}
          />
        </div>
      </div>

      {error && <div className="manual-order-error">{error}</div>}

      <button type="submit" className="manual-order-submit">
        Run deliberation
        <span className="scenario-card-arrow">→</span>
      </button>
    </form>
  );
}

export default function ScenarioSelector({ onSelect, onManualOrder }) {
  const [tab, setTab] = useState('scenarios');

  return (
    <div className="scenario-selector">
      <div className="scenario-selector-tabs">
        <button type="button" className={`scenario-tab ${tab === 'scenarios' ? 'active' : ''}`} onClick={() => setTab('scenarios')}>
          Demo Scenarios
        </button>
        <button type="button" className={`scenario-tab ${tab === 'manual' ? 'active' : ''}`} onClick={() => setTab('manual')}>
          Manual Order
        </button>
      </div>

      {tab === 'scenarios' && (
        <>
          <div className="scenario-selector-heading">Select a demonstration scenario</div>
          <div className="scenario-cards">
            {SCENARIOS.map(scenario => (
              <button key={scenario.id} className="scenario-card" onClick={() => onSelect(scenario)} type="button">
                <div className="scenario-card-header">
                  <span className="scenario-card-label">{scenario.label}</span>
                  <span className="scenario-card-badge" style={{ color: scenario.badgeColor, borderColor: scenario.badgeColor }}>
                    {scenario.badgeLabel}
                  </span>
                </div>
                <div className="scenario-card-title">{scenario.title}</div>
                <div className="scenario-card-desc">{scenario.description}</div>
                <div className="scenario-card-footer">
                  Run deliberation
                  <span className="scenario-card-arrow">→</span>
                </div>
              </button>
            ))}
          </div>
        </>
      )}

      {tab === 'manual' && (
        <>
          <div className="scenario-selector-heading">Enter a Bay Area delivery destination</div>
          <ManualOrderForm onSubmit={onManualOrder} />
        </>
      )}
    </div>
  );
}
