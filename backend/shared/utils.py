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
    ("central_sf",   37.785, 37.810, -122.425, -122.385),
    ("soma_mission", 37.745, 37.785, -122.440, -122.380),
    ("east_bay",     37.780, 37.890, -122.300, -122.190),
    ("south_bay",    37.300, 37.420, -122.060, -121.800),
    ("peninsula",    37.500, 37.690, -122.520, -122.350),
    ("north_bay",    37.900, 38.110, -122.640, -122.380),
    ("outer_east",   37.500, 37.780, -122.190, -121.900),
    ("outer_south",  36.900, 37.300, -122.100, -121.500),
    ("outer_west",   37.470, 37.650, -122.590, -122.520),
]

# Centroids for nearest-neighbour fallback when a point misses all bounding boxes.
_ZONE_CENTROIDS: dict[str, tuple[float, float]] = {
    "central_sf":   (37.795, -122.404),
    "soma_mission": (37.768, -122.414),
    "east_bay":     (37.834, -122.245),
    "south_bay":    (37.360, -121.928),
    "peninsula":    (37.594, -122.435),
    "north_bay":    (38.005, -122.510),
    "outer_east":   (37.640, -122.045),
    "outer_south":  (37.100, -121.800),
    "outer_west":   (37.560, -122.555),
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
        "central_sf":   18.0,
        "soma_mission": 22.0,
        "east_bay":     28.0,
        "south_bay":    32.0,
        "peninsula":    26.0,
        "north_bay":    35.0,
        "outer_east":   40.0,
        "outer_south":  45.0,
        "outer_west":   38.0,
    }
    return speeds.get(zone_id, 30.0)
