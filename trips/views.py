import os, requests, math
from django.conf import settings
from rest_framework.decorators import action
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Trip, ELDLog
from .serializers import TripSerializer,ELDLogSerializer
from .utils.eld_generator import generate_eld_logs_for_trip


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests, math

from .models import Trip
from .serializers import TripSerializer, ELDLogSerializer


class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    # Always return a fresh queryset to avoid stale data
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Trip.objects.all()
        return Trip.objects.filter(driver=user)

    # Assign current user as driver when creating
    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)

    # ----------------------------------------------------
    # PLAN ROUTE ACTION
    # ----------------------------------------------------
    @action(detail=True, methods=['post'])
    def plan_route(self, request, pk=None):
        trip = self.get_object()
        api_key = getattr(settings, "ORS_API_KEY", None)
        if not api_key:
            return Response(
                {"error": "ORS_API_KEY not set in environment."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        def geocode(place):
            g_url = "https://api.openrouteservice.org/geocode/search"
            try:
                r = requests.get(g_url, params={"api_key": api_key, "text": place})
                data = r.json()
                if "features" not in data or not data["features"]:
                    raise ValueError(f"No geocoding results for '{place}'")
                return data["features"][0]["geometry"]["coordinates"]  # [lon, lat]
            except Exception as e:
                raise ValueError(f"Geocoding failed for '{place}': {str(e)}")

        # Geocode pickup and dropoff
        try:
            pickup = geocode(trip.pickup_location)
            dropoff = geocode(trip.dropoff_location)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Request route
        url = "https://api.openrouteservice.org/v2/directions/driving-hgv"
        payload = {"coordinates": [pickup, dropoff]}
        headers = {"Authorization": api_key, "Content-Type": "application/json"}

        try:
            resp = requests.post(url, json=payload, headers=headers)
            data = resp.json()
            if resp.status_code != 200:
                return Response(
                    {"error": "Routing failed", "details": data},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "features" in data and data["features"]:
                route = data["features"][0]
                summary = route["properties"]["summary"]
                geometry = route["geometry"]
            elif "routes" in data and data["routes"]:
                route = data["routes"][0]
                summary = route["summary"]
                geometry = route["geometry"]
            else:
                return Response(
                    {"error": "No route returned", "details": data},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            distance_m = summary.get("distance", 0)
            duration_s = summary.get("duration", 0)

        except Exception as e:
            return Response({"error": f"Route processing failed: {e}"}, status=500)

        # Compute rest & fuel stops
        fuel_interval = 1609.34 * trip.fuel_stop_every_miles
        num_fuels = math.floor(distance_m / fuel_interval)
        fuel_stops = [
            f"Fuel Stop {i + 1} at mile {(i + 1) * trip.fuel_stop_every_miles}"
            for i in range(num_fuels)
        ]

        hrs = duration_s / 3600.0
        num_rests = math.floor(hrs / 8)
        rest_stops = [f"Rest Stop {i + 1} at hour {(i + 1) * 8}" for i in range(num_rests)]

        # Normalize geometry
        if isinstance(geometry, dict) and "coordinates" in geometry:
            coords = geometry["coordinates"]
        elif isinstance(geometry, str):
            coords = geometry
        else:
            coords = []

        # Save trip updates
        trip.route_distance_miles = round(distance_m / 1609.34, 2)
        trip.route_duration_seconds = int(duration_s)
        trip.route_polyline = coords
        trip.save()

        return Response(
            {
                "trip_id": trip.id,
                "distance_miles": trip.route_distance_miles,
                "duration_hours": round(hrs, 2),
                "fuel_stops": fuel_stops,
                "rest_stops": rest_stops,
            },
            status=status.HTTP_200_OK,
        )

    # -----------------------
    # GENERATE LOGS ACTION
    # -----------------------
    @action(detail=True, methods=["post"])
    def generate_logs(self, request, pk=None):
        trip = self.get_object()

        # safety checks
        if not trip.route_distance_miles or not trip.route_duration_seconds:
            return Response(
                {"error": "Trip route not planned yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # generate and save logs
            logs = generate_eld_logs_for_trip(trip)

            # serialize the logs for frontend
            serializer = ELDLogSerializer(logs, many=True)
            return Response(
                {
                    "message": f"{len(logs)} ELD logs generated successfully.",
                    "logs": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": f"Log generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # -----------------------
    # GET LOGS FOR A TRIP
    # -----------------------
    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        """
        Return all ELD logs for this trip.
        """
        trip = self.get_object()
        logs = trip.logs.order_by("date")
        serializer = ELDLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ELDLogViewSet(viewsets.ModelViewSet):
    queryset = ELDLog.objects.all()
    serializer_class = ELDLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return self.queryset if user.is_staff else self.queryset.filter(trip__driver=user)