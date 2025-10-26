
# 🚛 ELD Trip Planner & Log System — API Reference

This document describes all available endpoints for the **Django + React full-stack assessment backend**.

---

## 🔐 AUTHENTICATION (JWT)

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/api/token/` | `POST` | Obtain access & refresh tokens |
| `/api/token/refresh/` | `POST` | Refresh access token |

### Example — Obtain Token
```bash
curl -X POST https://your-domain.com/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "driver1", "password": "password123"}'
```
Response:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJh...",
  "access": "eyJ0eXAiOiJKV1QiLCJh..."
}
```

Use the access token for all authorized endpoints:
```
Authorization: Bearer <access_token>
```

---

## 👤 USERS

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/api/users/` | `GET` | List all users (admin only) |
| `/api/users/{id}/` | `GET` | Retrieve current user info |

Example:
```bash
curl -X GET https://your-domain.com/api/users/1/ \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "id": 1,
  "username": "driver1",
  "email": "driver1@example.com",
  "is_driver": true,
  "cdl_number": "D123456",
  "home_terminal": "Dallas, TX",
  "time_zone": "America/Chicago"
}
```

---

## 🚚 TRIPS

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/api/trips/` | `GET` | List trips (own only if driver) |
| `/api/trips/` | `POST` | Create a new trip |
| `/api/trips/{id}/` | `GET` | Retrieve trip details |
| `/api/trips/{id}/` | `PATCH` | Update route data |
| `/api/trips/{id}/` | `DELETE` | Delete a trip |
| `/api/trips/{id}/plan_route/` | `POST` | Auto-plan route via OpenRouteService |
| `/api/trips/{id}/generate_logs/` | `POST` | Generate ELD daily logs |

### Create Trip
```bash
curl -X POST https://your-domain.com/api/trips/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_location": "Dallas, TX",
    "pickup_location": "Chicago, IL",
    "dropoff_location": "Atlanta, GA",
    "current_cycle_used_hours": 12
  }'
```

### Plan Route
```bash
curl -X POST https://your-domain.com/api/trips/1/plan_route/ \
  -H "Authorization: Bearer <token>"
```
Response:
```json
{
  "trip_id": 1,
  "distance_miles": 949.73,
  "duration_hours": 14.2,
  "fuel_stops": ["Fuel Stop 1 at mile 1000"],
  "rest_stops": ["Rest Stop 1 at hour 8"]
}
```

### Generate Logs
```bash
curl -X POST https://your-domain.com/api/trips/1/generate_logs/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-10-25"}'
```
Response:
```json
{
  "id": 12,
  "trip": 1,
  "date": "2025-10-25",
  "grid": [
    {"start": "2025-10-25T06:00:00", "end": "2025-10-25T20:12:00", "status": "DRIVING"},
    {"start": "2025-10-25T20:12:00", "end": "2025-10-26T06:00:00", "status": "OFF_DUTY"}
  ],
  "miles_today": 949.73,
  "driving_hours": 14.2,
  "on_duty_hours": 16.2,
  "sleeper_hours": 0.0,
  "off_duty_hours": 9.8
}
```

---

## 📄 ELD LOGS

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/api/logs/` | `GET` | List all logs (own only if driver) |
| `/api/logs/{id}/` | `GET` | Retrieve log details |
| `/api/logs/{id}/` | `DELETE` | Delete log |

Example:
```bash
curl -X GET https://your-domain.com/api/logs/ \
  -H "Authorization: Bearer <token>"
```

Response:
```json
[
  {"id": 12, "trip": 1, "date": "2025-10-25", "driving_hours": 14.2},
  {"id": 13, "trip": 2, "date": "2025-10-26", "driving_hours": 10.5}
]
```

---

## ⚙️ HEADERS (for all authorized requests)
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## ✅ Summary

| Resource | Endpoint | Methods | Auth |
|-----------|-----------|----------|------|
| Auth | `/api/token/` | POST | No |
| Auth | `/api/token/refresh/` | POST | No |
| Users | `/api/users/` | GET | Yes |
| Trips | `/api/trips/` | GET, POST | Yes |
| Trip Detail | `/api/trips/{id}/` | GET, PATCH, DELETE | Yes |
| Trip Route | `/api/trips/{id}/plan_route/` | POST | Yes |
| Trip Logs | `/api/trips/{id}/generate_logs/` | POST | Yes |
| Logs | `/api/logs/` | GET | Yes |
| Log Detail | `/api/logs/{id}/` | GET, DELETE | Yes |

---

© 2025 — Full‑Stack Developer Coding Assessment — ELD Route Planner API
