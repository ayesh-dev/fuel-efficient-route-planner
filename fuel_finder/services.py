import math
import requests
from django.conf import settings
from .models import FuelStation

# Earth radius in miles
EARTH_RADIUS_MILES = 3958.8


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate straight-line distance between two coordinates in miles."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_MILES * c


def get_route_details(start_coords, end_coords, api_key):
    """
    Calls OpenRouteService API once to get total distance and route geometry.
    start_coords & end_coords format: [longitude, latitude]
    """
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }
    body = {"coordinates": [start_coords, end_coords]}

    response = requests.post(url, json=body, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Routing API error: {response.status_code} - {response.text}"
        )

    data = response.json()
    feature = data["features"][0]

    # Convert meters to miles
    distance_meters = feature["properties"]["summary"]["distance"]
    total_distance_miles = distance_meters * 0.000621371

    # Coordinates array: [[lon, lat], [lon, lat], ...]
    route_coordinates = feature["geometry"]["coordinates"]

    return total_distance_miles, route_coordinates


def find_optimal_fuel_stops(route_coordinates, total_distance):
    """
    Logic to find cheap fuel stations along the route every ~400-450 miles.
    Vehicle Range: 500 miles. MPG: 10 miles/gallon.
    """
    max_range = 500.0
    safe_search_range = 420.0  # Search before hitting 500 miles empty

    fuel_stops = []
    total_fuel_cost = 0.0

    # Load all stations from DB into memory for fast searching
    all_stations = list(FuelStation.objects.filter(latitude__isnull=False, longitude__isnull=False))

    if not all_stations:
        # Fallback if geocoding isn't populated on models yet
        all_stations = list(FuelStation.objects.all())

    # If trip is under 500 miles and no mid-refuel needed, calculate single fuel-up cost based on avg or start station
    if total_distance <= max_range:
        # Get cheapest station near start
        cheapest_near_start = sorted(all_stations, key=lambda s: s.price)[0]
        gallons_needed = total_distance / 10.0
        cost = gallons_needed * float(cheapest_near_start.price)

        return [
            {
                "name": cheapest_near_start.name,
                "address": cheapest_near_start.address,
                "city": cheapest_near_start.city,
                "state": cheapest_near_start.state,
                "price_per_gallon": float(cheapest_near_start.price),
            }
        ], round(cost, 2)

    # Multi-stop logic for routes > 500 miles
    accumulated_dist = 0.0
    current_fuel_dist = 0.0

    for i in range(1, len(route_coordinates)):
        prev_pt = route_coordinates[i - 1]
        curr_pt = route_coordinates[i]

        segment_dist = haversine_distance(
            prev_pt[1], prev_pt[0], curr_pt[1], curr_pt[0]
        )
        accumulated_dist += segment_dist
        current_fuel_dist += segment_dist

        # Time to refuel before reaching 500 miles
        if current_fuel_dist >= safe_search_range:
            current_lat, current_lon = curr_pt[1], curr_pt[0]

            # Find candidates within 50 miles radius of current point on route
            nearby_stations = [
                s for s in all_stations
                if s.latitude and s.longitude and haversine_distance(current_lat, current_lon, s.latitude, s.longitude) <= 50
            ]

            if nearby_stations:
                # Pick cheapest nearby station
                best_station = min(nearby_stations, key=lambda s: s.price)
            else:
                # Fallback to absolute cheapest if none in 50 mile radius
                best_station = min(all_stations, key=lambda s: s.price)

            gallons = current_fuel_dist / 10.0
            total_fuel_cost += gallons * float(best_station.price)

            fuel_stops.append(
                {
                    "name": best_station.name,
                    "address": best_station.address,
                    "city": best_station.city,
                    "state": best_station.state,
                    "price_per_gallon": float(best_station.price),
                }
            )

            current_fuel_dist = 0.0  # Tank refueled

    # Final segment fuel cost
    if current_fuel_dist > 0:
        cheapest_final = sorted(all_stations, key=lambda s: s.price)[0]
        gallons = current_fuel_dist / 10.0
        total_fuel_cost += gallons * float(cheapest_final.price)

    return fuel_stops, round(total_fuel_cost, 2)