# trips/utils/eld_generator.py
from datetime import timedelta, date
from ..models import ELDLog  # ✅ import the model

def generate_eld_logs_for_trip(trip):
    """
    Generate simplified FMCSA-compliant ELD logs and save them to DB.
    """
    total_hours = trip.route_duration_seconds / 3600.0 if trip.route_duration_seconds else 0
    total_miles = trip.route_distance_miles or 0
    avg_speed = total_miles / total_hours if total_hours > 0 else 55.0

    logs = []
    remaining_hours = total_hours
    remaining_miles = total_miles
    current_date = date.today()
    total_on_duty = 0.0

    while remaining_hours > 0:
        driving_today = min(11, remaining_hours)
        on_duty_today = 3
        total_duty_today = driving_today + on_duty_today
        off_duty_today = 10
        sleeper_today = 0

        miles_today = driving_today * avg_speed
        remaining_hours -= driving_today
        remaining_miles -= miles_today
        total_on_duty += total_duty_today

        # create and save ELDLog instance
        log = ELDLog.objects.create(
            trip=trip,
            date=current_date,
            miles_today=round(miles_today, 2),
            driving_hours=round(driving_today, 2),
            on_duty_hours=round(on_duty_today, 2),
            off_duty_hours=round(off_duty_today, 2),
            sleeper_hours=round(sleeper_today, 2),
            grid={},  # placeholder for grid data
        )
        logs.append(log)

        # handle 70-hour/8-day reset
        if total_on_duty >= 70:
            total_on_duty = 0
            current_date += timedelta(days=2)
        else:
            current_date += timedelta(days=1)

    return logs
