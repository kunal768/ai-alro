"""Tests for shared/utils.py — haversine, zone classification, and road speed."""
import math
import pytest

from shared.utils import (
    haversine,
    classify_zone,
    validate_bay_area,
    estimate_road_speed_kmh,
)


# ── haversine ──────────────────────────────────────────────────────────────────

class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine(37.7749, -122.4194, 37.7749, -122.4194) == pytest.approx(0.0)

    def test_known_distance_sf_to_oakland(self):
        # SF City Hall → Oakland City Hall: ~13 km airline
        dist = haversine(37.7793, -122.4193, 37.8044, -122.2712)
        assert 11.0 < dist < 15.0

    def test_known_distance_sf_to_sj(self):
        # SF → San Jose: ~66 km airline
        dist = haversine(37.7749, -122.4194, 37.3382, -121.8863)
        assert 60.0 < dist < 70.0

    def test_symmetry(self):
        d1 = haversine(37.7749, -122.4194, 37.8044, -122.2712)
        d2 = haversine(37.8044, -122.2712, 37.7749, -122.4194)
        assert d1 == pytest.approx(d2)

    def test_returns_km_not_miles(self):
        # 1 degree of latitude ≈ 111 km
        dist = haversine(0.0, 0.0, 1.0, 0.0)
        assert 110.0 < dist < 112.0

    def test_longitude_distance_at_equator(self):
        # 1 degree of longitude at equator ≈ 111 km
        dist = haversine(0.0, 0.0, 0.0, 1.0)
        assert 110.0 < dist < 112.0

    def test_large_distance(self):
        # SF → London: ~8600 km
        dist = haversine(37.7749, -122.4194, 51.5074, -0.1278)
        assert 8500.0 < dist < 8800.0

    def test_returns_float(self):
        result = haversine(37.7749, -122.4194, 37.8044, -122.2712)
        assert isinstance(result, float)


# ── validate_bay_area ──────────────────────────────────────────────────────────

class TestValidateBayArea:
    def test_valid_sf_coordinates(self):
        ok, msg = validate_bay_area(37.7749, -122.4194)
        assert ok is True
        assert msg is None

    def test_valid_oakland_coordinates(self):
        ok, msg = validate_bay_area(37.8044, -122.2712)
        assert ok is True
        assert msg is None

    def test_valid_san_jose_coordinates(self):
        ok, msg = validate_bay_area(37.3382, -121.8863)
        assert ok is True
        assert msg is None

    def test_outside_north(self):
        ok, msg = validate_bay_area(39.0, -122.0)
        assert ok is False
        assert msg is not None
        assert "outside" in msg.lower()

    def test_outside_south(self):
        ok, msg = validate_bay_area(36.0, -121.0)
        assert ok is False
        assert msg is not None

    def test_outside_east(self):
        ok, msg = validate_bay_area(37.7749, -120.0)
        assert ok is False
        assert msg is not None

    def test_outside_west(self):
        ok, msg = validate_bay_area(37.7749, -123.5)
        assert ok is False
        assert msg is not None

    def test_error_message_contains_coordinates(self):
        lat, lon = 40.0, -74.0  # New York
        ok, msg = validate_bay_area(lat, lon)
        assert ok is False
        assert str(lat)[:4] in msg

    def test_boundary_lat_min(self):
        ok, _ = validate_bay_area(36.9, -122.0)
        assert ok is True

    def test_boundary_lat_max(self):
        ok, _ = validate_bay_area(38.3, -122.0)
        assert ok is True

    def test_boundary_lon_min(self):
        ok, _ = validate_bay_area(37.5, -122.9)
        assert ok is True

    def test_boundary_lon_max(self):
        ok, _ = validate_bay_area(37.5, -121.4)
        assert ok is True


# ── classify_zone ──────────────────────────────────────────────────────────────

class TestClassifyZone:
    def test_financial_district_is_central_sf(self):
        # 37.794, -122.397 — Financial District SF
        zone = classify_zone(37.794, -122.397)
        assert zone == "central_sf"

    def test_mission_district_is_soma_mission(self):
        # 37.763, -122.419 — Mission District
        zone = classify_zone(37.763, -122.419)
        assert zone == "soma_mission"

    def test_oakland_is_east_bay(self):
        # 37.834, -122.245 — Oakland
        zone = classify_zone(37.834, -122.245)
        assert zone == "east_bay"

    def test_san_jose_is_south_bay(self):
        # 37.360, -121.928 — San Jose
        zone = classify_zone(37.360, -121.928)
        assert zone == "south_bay"

    def test_daly_city_is_peninsula(self):
        # 37.594, -122.435 — Daly City / Peninsula
        zone = classify_zone(37.594, -122.435)
        assert zone == "peninsula"

    def test_novato_is_north_bay(self):
        # 38.005, -122.510 — Novato
        zone = classify_zone(38.005, -122.510)
        assert zone == "north_bay"

    def test_hayward_is_outer_east(self):
        # 37.640, -122.045 — Hayward
        zone = classify_zone(37.640, -122.045)
        assert zone == "outer_east"

    def test_returns_string(self):
        zone = classify_zone(37.794, -122.397)
        assert isinstance(zone, str)

    def test_fallback_returns_nearest_centroid(self):
        # Way outside all bounding boxes but inside Bay Area bounds → nearest centroid
        zone = classify_zone(38.25, -122.85)
        assert isinstance(zone, str)
        assert len(zone) > 0

    def test_all_zones_accessible(self):
        # Verify that centroid of each known zone maps back to that zone
        centroids = {
            "central_sf":   (37.795, -122.404),
            "soma_mission": (37.768, -122.414),
            "east_bay":     (37.834, -122.245),
            "south_bay":    (37.360, -121.928),
            "north_bay":    (38.005, -122.510),
            "outer_east":   (37.640, -122.045),
        }
        for expected_zone, (lat, lon) in centroids.items():
            result = classify_zone(lat, lon)
            assert result == expected_zone, f"{expected_zone}: expected {expected_zone}, got {result}"


# ── estimate_road_speed_kmh ────────────────────────────────────────────────────

class TestEstimateRoadSpeedKmh:
    def test_central_sf_slowest(self):
        assert estimate_road_speed_kmh("central_sf") == 18.0

    def test_outer_south_fastest(self):
        assert estimate_road_speed_kmh("outer_south") == 45.0

    def test_all_known_zones_return_positive(self):
        zones = [
            "central_sf", "soma_mission", "east_bay", "south_bay",
            "peninsula", "north_bay", "outer_east", "outer_south", "outer_west",
        ]
        for z in zones:
            speed = estimate_road_speed_kmh(z)
            assert speed > 0, f"Zone {z!r} returned non-positive speed"

    def test_unknown_zone_returns_default(self):
        speed = estimate_road_speed_kmh("nonexistent_zone")
        assert speed == 30.0

    def test_returns_float(self):
        assert isinstance(estimate_road_speed_kmh("east_bay"), float)

    def test_congested_urban_slower_than_suburban(self):
        assert estimate_road_speed_kmh("central_sf") < estimate_road_speed_kmh("north_bay")
        assert estimate_road_speed_kmh("soma_mission") < estimate_road_speed_kmh("outer_east")
