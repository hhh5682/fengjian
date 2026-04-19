#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
load_dotenv(Path(__file__).resolve().parent / ".env")

from agents.orchestrator_agent import OrchestratorAgent
from models.trip_models import TripRequest

trip_data = {
    "departure": "深圳",
    "destination": "桂林",
    "departureTime": "2026-04-20T10:00:00",
    "returnTime": "2026-04-22T18:00:00",
    "departureCoords": {"lat": 22.5, "lng": 114.0},
    "destinationCoords": {"lat": 25.3, "lng": 110.3},
    "transportModes": ["高铁"],
    "interests": ["风景"],
    "foodPreferences": ["本地特色"],
    "budget": 3000,
    "adults": 1
}

trip_request = TripRequest.from_dict(trip_data)
orchestrator = OrchestratorAgent()
result = orchestrator.plan(trip_request)

if result.get("code") == 0:
    data = result.get("data", {})
    local_transports = data.get("local_transports", [])
    print(f"[OK] Planning success")
    print(f"[OK] Local transports: {len(local_transports)}")
    for i, lt in enumerate(local_transports):
        from_name = lt.get('from_location', {}).get('name', '?')
        to_name = lt.get('to_location', {}).get('name', '?')
        routes_count = len(lt.get('routes', []))
        print(f"  [{i}] {from_name} -> {to_name} ({routes_count} routes)")
        if routes_count > 0:
            for j, route in enumerate(lt.get('routes', [])):
                print(f"      Route {j}: {route.get('type')} - {route.get('distance_m')}m, {route.get('duration_s')}s")
else:
    print(f"[FAIL] {result.get('message')}")