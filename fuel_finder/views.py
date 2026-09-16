from django.shortcuts import render

# Create your views here.
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import find_optimal_fuel_stops, get_route_details


class CalculateFuelRouteView(APIView):
    def post(self, request):
        start_coords = request.data.get("start")  # Format: [longitude, latitude]
        end_coords = request.data.get("finish")  # Format: [longitude, latitude]

        if not start_coords or not end_coords:
            return Response(
                {"error": "Both 'start' and 'finish' coordinates are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key = getattr(settings, "ORS_API_KEY", None)
        if not api_key:
            return Response(
                {"error": "OpenRouteService API key is missing in settings."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # 1. Single call to Routing API
            total_distance, route_coords = get_route_details(
                start_coords, end_coords, api_key
            )

            # 2. Fuel stops and cost logic
            fuel_stops, total_cost = find_optimal_fuel_stops(
                route_coords, total_distance
            )

            # 3. Structured Output
            return Response(
                {
                    "total_distance_miles": round(total_distance, 2),
                    "total_fuel_cost_usd": total_cost,
                    "fuel_stops_count": len(fuel_stops),
                    "optimal_fuel_stops": fuel_stops,
                    "route_map_geometry": route_coords,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )