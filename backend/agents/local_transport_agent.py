"""
Local Transport Agent
负责规划行程中的本地交通路线，包括：
1. 初始小交通：从用户起始点到大交通起始点
2. 项目间小交通：行程中相邻卡片之间的路线
"""
from typing import List, Dict, Any, Optional
from services.provider_clients import AMapClient


class LocalTransportAgent:
    def __init__(self, amap_client: Optional[AMapClient] = None):
        self.name = "小交通规划员"
        self.amap_client = amap_client or AMapClient()

    def plan_initial_transport(
        self,
        user_location: str,
        user_coords: Dict[str, float],
        transport_hub_location: str,
        transport_hub_coords: Dict[str, float],
    ) -> Optional[Dict[str, Any]]:
        """
        规划初始小交通：从用户起始点到大交通起始点
        
        返回格式：
        {
            "from_location": {"name": "...", "type": "user", "coords": {...}},
            "to_location": {"name": "...", "type": "transport_hub", "coords": {...}},
            "routes": [...]
        }
        """
        if not user_coords or not transport_hub_coords:
            print(f"[LocalTransportAgent] initial transport skipped: missing coords user={user_coords} hub={transport_hub_coords}")
            return None

        origin = f"{user_coords.get('lng')},{user_coords.get('lat')}"
        destination = f"{transport_hub_coords.get('lng')},{transport_hub_coords.get('lat')}"

        print(f"[LocalTransportAgent] initial transport planning: {user_location}({origin}) -> {transport_hub_location}({destination})")
        routes = self._get_multi_mode_routes(origin, destination)
        if not routes:
            print("[LocalTransportAgent] initial transport failed: no valid amap routes")
            return None

        return {
            "from_location": {
                "name": user_location,
                "type": "user",
                "coords": user_coords,
                "coordinates": [user_coords.get("lng"), user_coords.get("lat")],
            },
            "to_location": {
                "name": transport_hub_location,
                "type": "transport_hub",
                "coords": transport_hub_coords,
                "coordinates": [transport_hub_coords.get("lng"), transport_hub_coords.get("lat")],
            },
            "routes": routes,
            "selected_index": 0,
        }

    def plan_between_items(
        self,
        from_item: Dict[str, Any],
        to_item: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        规划项目间小交通
        
        from_item / to_item 格式：
        {
            "name": "酒店名称",
            "type": "hotel|food|attraction",
            "coords": {"lat": 25.3, "lng": 110.3}
        }
        
        返回格式同 plan_initial_transport
        """
        from_coords = from_item.get("coords")
        to_coords = to_item.get("coords")

        if not from_coords or not to_coords:
            print(f"[LocalTransportAgent] between items skipped: missing coords from={from_item} to={to_item}")
            return None

        origin = f"{from_coords.get('lng')},{from_coords.get('lat')}"
        destination = f"{to_coords.get('lng')},{to_coords.get('lat')}"

        print(
            f"[LocalTransportAgent] between items planning: "
            f"{from_item.get('name', '出发地')}({origin}) -> {to_item.get('name', '目的地')}({destination})"
        )
        routes = self._get_multi_mode_routes(origin, destination)
        if not routes:
            print("[LocalTransportAgent] between items failed: no valid amap routes")
            return None

        return {
            "from_location": {
                "name": from_item.get("name", "出发地"),
                "type": from_item.get("type", "location"),
                "coords": from_coords,
                "coordinates": [from_coords.get("lng"), from_coords.get("lat")],
            },
            "to_location": {
                "name": to_item.get("name", "目的地"),
                "type": to_item.get("type", "location"),
                "coords": to_coords,
                "coordinates": [to_coords.get("lng"), to_coords.get("lat")],
            },
            "routes": routes,
            "selected_index": 0,
        }

    def _get_multi_mode_routes(self, origin: str, destination: str) -> List[Dict[str, Any]]:
        """
        获取多种交通方式的路线
        支持：驾车、公交、步行
        如果高德API不可用，返回演示数据
        """
        routes = []

        # 驾车路线
        print(f"[LocalTransportAgent] amap request mode=driving origin={origin} destination={destination}")
        driving_route = self.amap_client.route_plan(origin, destination, mode="driving")
        print(f"[LocalTransportAgent] amap response mode=driving data={driving_route}")
        if driving_route and driving_route.get("distance_m"):
            routes.append(driving_route)
        else:
            # 高德不可用，使用演示数据
            print("[LocalTransportAgent] amap unavailable, using demo driving route")
            routes.append(self._demo_driving_route())

        # 公交路线
        print(f"[LocalTransportAgent] amap request mode=transit origin={origin} destination={destination}")
        transit_route = self.amap_client.route_plan(origin, destination, mode="transit")
        print(f"[LocalTransportAgent] amap response mode=transit data={transit_route}")
        if transit_route and transit_route.get("distance_m"):
            routes.append(transit_route)
        else:
            # 高德不可用，使用演示数据
            print("[LocalTransportAgent] amap unavailable, using demo transit route")
            routes.append(self._demo_transit_route())

        # 步行路线
        print(f"[LocalTransportAgent] amap request mode=walking origin={origin} destination={destination}")
        walking_route = self.amap_client.route_plan(origin, destination, mode="walking")
        print(f"[LocalTransportAgent] amap response mode=walking data={walking_route}")
        if walking_route and walking_route.get("distance_m"):
            routes.append(walking_route)
        else:
            # 高德不可用，使用演示数据
            print("[LocalTransportAgent] amap unavailable, using demo walking route")
            routes.append(self._demo_walking_route())

        print(f"[LocalTransportAgent] valid routes count={len(routes)}")
        return routes

    def _demo_driving_route(self) -> Dict[str, Any]:
        """演示驾车路线"""
        return {
            "type": "driving",
            "distance_m": 8500.0,
            "duration_s": 1200.0,
            "taxi_cost": 28.0,
            "steps": [
                {"instruction": "向东行驶", "distance": 2000, "duration": 300, "polyline": ""},
                {"instruction": "向南转向", "distance": 3500, "duration": 500, "polyline": ""},
                {"instruction": "向西行驶", "distance": 3000, "duration": 400, "polyline": ""},
            ],
            "polyline": "",
        }

    def _demo_transit_route(self) -> Dict[str, Any]:
        """演示公交路线"""
        return {
            "type": "transit",
            "distance_m": 9200.0,
            "duration_s": 1800.0,
            "taxi_cost": None,
            "steps": [
                {"instruction": "步行至公交站", "distance": 500, "duration": 300, "polyline": ""},
                {"instruction": "乘坐公交 2 号线", "distance": 8000, "duration": 1200, "polyline": ""},
                {"instruction": "步行至目的地", "distance": 700, "duration": 300, "polyline": ""},
            ],
            "polyline": "",
        }

    def _demo_walking_route(self) -> Dict[str, Any]:
        """演示步行路线"""
        return {
            "type": "walking",
            "distance_m": 2800.0,
            "duration_s": 2100.0,
            "taxi_cost": None,
            "steps": [
                {"instruction": "向东北方向行走", "distance": 1400, "duration": 1050, "polyline": ""},
                {"instruction": "向南方向行走", "distance": 1400, "duration": 1050, "polyline": ""},
            ],
            "polyline": "",
        }