from rest_framework import serializers
from .models import Trip, ELDLog
import json


class ELDLogSerializer(serializers.ModelSerializer):
    grid_plot_data = serializers.SerializerMethodField()

    class Meta:
        model = ELDLog
        fields = [
            "id",
            "trip",
            "date",
            "miles_today",
            "driving_hours",
            "on_duty_hours",
            "off_duty_hours",
            "sleeper_hours",
            "grid",
            "grid_plot_data",
        ]

    def get_grid_plot_data(self, obj):
        """
        Build structured plot data for ELD grid visualization.
        Handles double-encoded JSON, merges sleeper/off_duty,
        and tolerates non-continuous hour segments.
        """
        grid = getattr(obj, "grid", None)

        if not grid:
            # Fallback: build simplified grid from hours summary
            total_hours = {
                "driving": obj.driving_hours or 0,
                "on_duty": obj.on_duty_hours or 0,
                "off_duty": (obj.off_duty_hours or 0) + (obj.sleeper_hours or 0),
            }

            plot_data = []
            current_hour = 0
            for status, hours in total_hours.items():
                if hours <= 0:
                    continue
                end_hour = min(24, current_hour + int(hours))
                for h in range(current_hour, end_hour):
                    plot_data.append({"hour": h, "status": status})
                current_hour = end_hour
            return plot_data

        # Step 1: Parse top-level JSON if stored as a string
        if isinstance(grid, str):
            try:
                grid = json.loads(grid)
            except json.JSONDecodeError:
                return []

        plot_data = []
        for segment in grid:
            # Step 2: Handle double-encoded entries (JSON strings inside list)
            if isinstance(segment, str):
                try:
                    segment = json.loads(segment)
                except json.JSONDecodeError:
                    continue

            if not isinstance(segment, dict):
                continue

            start = int(segment.get("start", 0))
            end = int(segment.get("end", start))
            status = segment.get("status", "off_duty").lower()

            # Normalize status
            if status in ["off_duty", "sleeper"]:
                status = "off_duty"
            elif status not in ["driving", "on_duty"]:
                status = "off_duty"

            # Add points for each hour in range
            for hour in range(start, end):
                if 0 <= hour < 24:
                    plot_data.append({"hour": hour, "status": status})

        # Step 3: Deduplicate hour-status pairs
        unique = []
        seen = set()
        for p in plot_data:
            key = (p["hour"], p["status"])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique

class TripSerializer(serializers.ModelSerializer):
    logs = ELDLogSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = "__all__"
        read_only_fields = ["driver", "created_at"]
