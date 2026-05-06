"""Shared utilities: geospatial helpers and zone classification."""
import math


# ── Haversine distance ─────────────────────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Zone classification ────────────────────────────────────────────────────────

# Bounding boxes ordered innermost → outermost to resolve overlaps via first-match.
# Each tuple: (zone_id, lat_min, lat_max, lon_min, lon_max)
_ZONE_BOUNDS: list[tuple] = [
    ("central",     51.490, 51.530, -0.180, -0.050),
    ("east",        51.480, 51.545, -0.060,  0.100),
    ("north",       51.530, 51.620, -0.200,  0.050),
    ("south",       51.430, 51.490, -0.180,  0.050),
    ("west",        51.470, 51.545, -0.400, -0.180),
    ("outer_east",  51.430, 51.580,  0.100,  0.420),
    ("outer_south", 51.300, 51.435, -0.250,  0.100),
    ("outer_west",  51.430, 51.580, -0.600, -0.400),
    ("outer_north", 51.600, 51.750, -0.400,  0.050),
]

# Centroids for nearest-neighbour fallback when a point misses all bounding boxes.
_ZONE_CENTROIDS: dict[str, tuple[float, float]] = {
    "central":     (51.511, -0.118),
    "north":       (51.576, -0.085),
    "east":        (51.515,  0.020),
    "south":       (51.461, -0.085),
    "west":        (51.505, -0.280),
    "outer_east":  (51.510,  0.240),
    "outer_south": (51.365, -0.080),
    "outer_west":  (51.490, -0.500),
    "outer_north": (51.660, -0.180),
}


def classify_zone(lat: float, lon: float) -> str:
    """Return the zone_id for a given lat/lon coordinate.

    Uses bounding-box lookup first; falls back to nearest centroid for
    coordinates that fall outside all defined boxes (e.g. far outer suburbs).
    """
    for zone_id, lat_min, lat_max, lon_min, lon_max in _ZONE_BOUNDS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return zone_id

    # Fallback: nearest centroid
    nearest = min(
        _ZONE_CENTROIDS.items(),
        key=lambda item: haversine(lat, lon, item[1][0], item[1][1]),
    )
    return nearest[0]


def estimate_road_speed_kmh(zone_id: str) -> float:
    """Return a realistic average road speed for a zone (accounts for congestion)."""
    speeds = {
        "central":     22.0,
        "east":        28.0,
        "north":       30.0,
        "south":       28.0,
        "west":        26.0,
        "outer_east":  45.0,
        "outer_south": 40.0,
        "outer_west":  42.0,
        "outer_north": 38.0,
    }
    return speeds.get(zone_id, 30.0)
