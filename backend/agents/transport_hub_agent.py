"""
交通枢纽 Agent
负责协调大交通和小交通，生成完整的交通方案。
"""
from typing import Any, Dict, List, Optional

from models.trip_models import Coordinates, TripRequest
from services.provider_clients import AMapClient


class TransportHubAgent:
    def __init__(self, amap_client: Optional[AMapClient] = None):
        self.name = "交通枢纽规划员"
        self.amap = amap_client or AMapClient()

    def plan(self, trip: TripRequest) -> Dict[str, Any]:
        """
        生成完整交通方案，包括大交通和小交通。

        返回结构：
        {
            "outbound": {
                "main_transport": [...],  # 大交通候选
                "local_access": {...},    # 起点到交通枢纽的小交通
            },
            "return": {
                "main_transport": [...],
                "local_access": {...},
            },
            "hubs": {...},  # 交通枢纽信息
        }
        """
        # 1. 查询交通枢纽
        hubs = self._query_hubs(trip.destination)

        # 2. 查询大交通候选
        intercity = self.amap.intercity_transport_candidates(
            departure_city=trip.departure,
            destination_city=trip.destination,
            modes=trip.transport_modes,
            departure_time=trip.departure_time,
            return_time=trip.return_time,
        )

        # 3. 查询小交通（起点到枢纽、枢纽到目的地）
        outbound_local = self._plan_local_transport(
            trip.departure,
            trip.departure_coords,
            hubs.get("departure_hub", {}),
            "出发",
        )
        return_local = self._plan_local_transport(
            trip.destination,
            hubs.get("destination_hub", {}).get("coords", Coordinates()),
            trip.departure_coords,
            "返回",
        )

        return {
            "outbound": {
                "main_transport": intercity.get("outbound", []),
                "local_access": outbound_local,
            },
            "return": {
                "main_transport": intercity.get("return", []),
                "local_access": return_local,
            },
            "hubs": hubs,
        }

    def _query_hubs(self, city: str) -> Dict[str, Any]:
        """查询城市交通枢纽"""
        hubs = self.amap.transit_hubs(city)
        primary_hub = hubs[0] if hubs else None
        normalized_hub = self._normalize_hub(primary_hub, city)
        return {
            "departure_hub": normalized_hub,
            "destination_hub": normalized_hub,
            "all_hubs": [self._normalize_hub(hub, city) for hub in hubs],
        }

    def _plan_local_transport(
        self,
        location_name: str,
        location_coords: Coordinates,
        hub_coords: Coordinates,
        direction: str,
    ) -> Dict[str, Any]:
        """
        规划小交通路线。
        返回从 location 到 hub 的路线建议。
        """
        location_coords = self._normalize_coords(location_coords)
        hub_coords = self._normalize_coords(hub_coords)

        if not location_coords.lat or not location_coords.lng or not hub_coords.lat or not hub_coords.lng:
            return {
                "modes": ["打车", "地铁", "步行"],
                "primary": {
                    "mode": "打车",
                    "duration_min": 54,
                    "cost": 38,
                    "description": f"{location_name} → 交通枢纽（打车）",
                },
            }

        origin = f"{location_coords.lng},{location_coords.lat}"
        destination = f"{hub_coords.lng},{hub_coords.lat}"

        route = self.amap.route_plan(origin, destination)

        distance_m = route.get("distance_m") or 0
        duration_s = route.get("duration_s") or 0
        duration_min = int(duration_s / 60)
        taxi_cost = route.get("taxi_cost") or 0

        return {
            "modes": ["打车", "地铁", "步行"],
            "primary": {
                "mode": "打车",
                "duration_min": duration_min,
                "cost": int(taxi_cost) if taxi_cost else 38,
                "description": f"{location_name} → 交通枢纽（打车 {duration_min} 分钟）",
                "distance_m": distance_m,
            },
            "alternatives": [
                {
                    "mode": "地铁",
                    "duration_min": int(duration_min * 1.5),
                    "cost": 5,
                    "description": f"{location_name} → 交通枢纽（地铁）",
                },
                {
                    "mode": "步行",
                    "duration_min": int(duration_min * 3),
                    "cost": 0,
                    "description": f"{location_name} → 交通枢纽（步行）",
                },
            ],
        }

    def _normalize_coords(self, value: Any) -> Coordinates:
        if isinstance(value, Coordinates):
            return value
        if isinstance(value, dict):
            return Coordinates(
                lat=value.get("lat"),
                lng=value.get("lng"),
            )
        return Coordinates()

    def _normalize_hub(self, hub: Optional[Dict[str, Any]], city: str) -> Dict[str, Any]:
        if not isinstance(hub, dict):
            return {"name": f"{city}交通枢纽", "coords": Coordinates().to_dict()}

        coords = self._normalize_coords(
            hub.get("coords") or {
                "lat": hub.get("lat"),
                "lng": hub.get("lng"),
            }
        )

        normalized_hub = dict(hub)
        normalized_hub["coords"] = coords.to_dict()
        return normalized_hub