import os
import hashlib
from typing import Any, Dict, List, Optional

import requests


class BaseHttpClient:
    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        if not response.text:
            return {}
        return response.json()


class AMapClient(BaseHttpClient):
    """
    高德服务封装
    说明：
    - 这里统一封装 POI 搜索、地理编码、路线规划等能力
    - 后端使用 Web服务 Key（用于坐标查询、POI 查询、服务端路线计算）
    - 某些城际大交通场景高德未必直接返回完整铁路/航班票务数据，因此提供"查询结果 + fallback"结构
    """
    def __init__(self, api_key: Optional[str] = None, security_code: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("AMAP_API_KEY", "")
        self.security_code = security_code or os.getenv("AMAP_SECURITY_CODE", "")
        self.base_url = "https://restapi.amap.com"
        print(f"[AMapClient] initialized with api_key={self.api_key[:10]}... security_code={'set' if self.security_code else 'not set'}")

    def is_ready(self) -> bool:
        return bool(self.api_key)

    def _normalize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, str) and value == "":
                continue
            normalized[key] = value
        return normalized

    def _generate_sig(self, params: Dict[str, Any]) -> str:
        if not self.security_code:
            return ""
        normalized = self._normalize_params(params)
        sorted_params = sorted(
            [(str(key), str(value)) for key, value in normalized.items()],
            key=lambda item: item[0],
        )
        query = "&".join([f"{key}={value}" for key, value in sorted_params])
        raw = f"{query}{self.security_code}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _request_amap_json(self, url: str, params: Dict[str, Any], api_name: str) -> Dict[str, Any]:
        normalized = self._normalize_params(params)

        # 先尝试无签名请求（Web服务 Key 通常需要签名，但先尝试无签名）
        try:
            print(f"[AMapClient] {api_name} request (no sig): url={url}, params={normalized}")
            data = self.get_json(url, params=normalized)
            if str(data.get("status", "")) == "1":
                print(f"[AMapClient] {api_name} request success (no sig)")
                return data
            infocode = data.get('infocode')
            info = data.get('info')
            print(
                f"[AMapClient] {api_name} request failed (no sig): "
                f"info={info} infocode={infocode}"
            )
        except Exception as e:
            print(f"[AMapClient] {api_name} request error (no sig): {e}")

        # 如果无签名失败且有 security_code，再尝试带签名
        if self.security_code:
            signed_params = dict(normalized)
            signed_params["sig"] = self._generate_sig(normalized)
            try:
                print(f"[AMapClient] {api_name} request (with sig): url={url}, params={signed_params}")
                data = self.get_json(url, params=signed_params)
                if str(data.get("status", "")) == "1":
                    print(f"[AMapClient] {api_name} request success (with sig)")
                    return data
                infocode = data.get('infocode')
                info = data.get('info')
                print(
                    f"[AMapClient] {api_name} signed request failed: "
                    f"info={info} infocode={infocode}"
                )
            except Exception as e:
                print(f"[AMapClient] {api_name} signed request error: {e}")

        print(f"[AMapClient] {api_name} all attempts failed, returning empty dict")
        return {}

    def geocode(self, address: str, city: str = "") -> Dict[str, Any]:
        if not self.is_ready() or not address:
            return {"name": address, "location": "", "lat": None, "lng": None}

        params = {
            "key": self.api_key,
            "address": address,
            "city": city,
        }
        data = self._request_amap_json(
            f"{self.base_url}/v3/geocode/geo",
            params=params,
            api_name="geocode",
        )
        geocodes = data.get("geocodes") or []
        if not geocodes:
            return {"name": address, "location": "", "lat": None, "lng": None}

        loc = (geocodes[0].get("location") or "").split(",")
        lng = float(loc[0]) if len(loc) == 2 and loc[0] else None
        lat = float(loc[1]) if len(loc) == 2 and loc[1] else None
        return {
            "name": address,
            "location": geocodes[0].get("location", ""),
            "lat": lat,
            "lng": lng,
            "formatted_address": geocodes[0].get("formatted_address", address),
        }

    def search_poi(self, keywords: str, city: str = "", page_size: int = 10, types: str = "") -> List[Dict[str, Any]]:
        if not self.is_ready():
            return []

        params = {
            "key": self.api_key,
            "keywords": keywords,
            "city": city,
            "offset": page_size,
            "types": types,
            "extensions": "all",
        }
        data = self._request_amap_json(
            f"{self.base_url}/v3/place/text",
            params=params,
            api_name="search_poi",
        )
        pois = data.get("pois") or []
        result: List[Dict[str, Any]] = []
        for poi in pois:
            loc = (poi.get("location") or "").split(",")
            result.append(
                {
                    "id": poi.get("id", ""),
                    "name": poi.get("name", ""),
                    "address": poi.get("address", ""),
                    "city": poi.get("cityname", city),
                    "district": poi.get("adname", ""),
                    "type": poi.get("type", ""),
                    "lat": float(loc[1]) if len(loc) == 2 and loc[1] else None,
                    "lng": float(loc[0]) if len(loc) == 2 and loc[0] else None,
                    "raw": poi,
                }
            )
        return result

    def route_plan(self, origin: str, destination: str, mode: str = "driving", strategy: int = 0, city: str = "") -> Dict[str, Any]:
        """
        origin / destination: 'lng,lat'
        mode: driving | walking | transit
        """
        if not self.is_ready():
            print(f"[AMapClient] route_plan skipped: API not ready (no key)")
            return self._empty_route(mode)
        if not origin or not destination:
            print(f"[AMapClient] route_plan skipped: missing coords origin={origin} destination={destination}")
            return self._empty_route(mode)

        if mode == "walking":
            return self._walking_route(origin, destination)
        if mode == "transit":
            return self._transit_route(origin, destination, city=city)
        return self._driving_route(origin, destination, strategy=strategy)

    def _empty_route(self, mode: str = "driving") -> Dict[str, Any]:
        return {
            "type": mode,
            "distance_m": None,
            "duration_s": None,
            "taxi_cost": None,
            "steps": [],
            "polyline": "",
        }

    def _driving_route(self, origin: str, destination: str, strategy: int = 0) -> Dict[str, Any]:
        print(f"[AMapClient] _driving_route: origin={origin}, destination={destination}")
        try:
            params = {
                "key": self.api_key,
                "origin": origin,
                "destination": destination,
                "strategy": strategy,
                "extensions": "all",
            }
            data = self._request_amap_json(
                f"{self.base_url}/v3/direction/driving",
                params=params,
                api_name="driving_route",
            )
            print(f"[AMapClient] _driving_route response: {data}")
        except Exception as e:
            print(f"[AMapClient] _driving_route error: {e}")
            return self._empty_route("driving")
        
        route = data.get("route") or {}
        paths = route.get("paths") or []
        if not paths:
            print(f"[AMapClient] _driving_route: no paths in response")
            return self._empty_route("driving")

        path = paths[0]
        steps = path.get("steps") or []
        result = {
            "type": "driving",
            "distance_m": float(path.get("distance") or 0),
            "duration_s": float(path.get("duration") or 0),
            "taxi_cost": float(route.get("taxi_cost") or path.get("tolls") or 0),
            "steps": [
                {
                    "instruction": step.get("instruction", ""),
                    "distance": step.get("distance"),
                    "duration": step.get("duration"),
                    "polyline": step.get("polyline", ""),
                }
                for step in steps
            ],
            "polyline": ";".join([step.get("polyline", "") for step in steps if step.get("polyline")]),
        }
        print(f"[AMapClient] _driving_route result: distance={result['distance_m']}, duration={result['duration_s']}")
        return result

    def _walking_route(self, origin: str, destination: str) -> Dict[str, Any]:
        print(f"[AMapClient] _walking_route: origin={origin}, destination={destination}")
        try:
            params = {
                "key": self.api_key,
                "origin": origin,
                "destination": destination,
            }
            data = self._request_amap_json(
                f"{self.base_url}/v3/direction/walking",
                params=params,
                api_name="walking_route",
            )
            print(f"[AMapClient] _walking_route response: {data}")
        except Exception as e:
            print(f"[AMapClient] _walking_route error: {e}")
            return self._empty_route("walking")
        
        route = data.get("route") or {}
        paths = route.get("paths") or []
        if not paths:
            print(f"[AMapClient] _walking_route: no paths in response")
            return self._empty_route("walking")

        path = paths[0]
        steps = path.get("steps") or []
        result = {
            "type": "walking",
            "distance_m": float(path.get("distance") or 0),
            "duration_s": float(path.get("duration") or 0),
            "taxi_cost": None,
            "steps": [
                {
                    "instruction": step.get("instruction", ""),
                    "distance": step.get("distance"),
                    "duration": step.get("duration"),
                    "polyline": step.get("polyline", ""),
                }
                for step in steps
            ],
            "polyline": ";".join([step.get("polyline", "") for step in steps if step.get("polyline")]),
        }
        print(f"[AMapClient] _walking_route result: distance={result['distance_m']}, duration={result['duration_s']}")
        return result

    def _bicycling_route(self, origin: str, destination: str) -> Dict[str, Any]:
        params = {
            "key": self.api_key,
            "origin": origin,
            "destination": destination,
        }
        data = self._request_amap_json(
            f"{self.base_url}/v4/direction/bicycling",
            params=params,
            api_name="bicycling_route",
        )
        data_obj = data.get("data") or {}
        paths = data_obj.get("paths") or []
        if not paths:
            return self._empty_route("bicycling")

        path = paths[0]
        steps = path.get("steps") or []
        return {
            "type": "bicycling",
            "distance_m": float(path.get("distance") or 0),
            "duration_s": float(path.get("duration") or 0),
            "taxi_cost": None,
            "steps": [
                {
                    "instruction": step.get("instruction", ""),
                    "distance": step.get("distance"),
                    "duration": step.get("duration"),
                    "polyline": step.get("polyline", ""),
                }
                for step in steps
            ],
            "polyline": ";".join([step.get("polyline", "") for step in steps if step.get("polyline")]),
        }

    def _transit_route(self, origin: str, destination: str, city: str = "") -> Dict[str, Any]:
        print(f"[AMapClient] _transit_route: origin={origin}, destination={destination}, city={city}")
        try:
            params = {
                "key": self.api_key,
                "origin": origin,
                "destination": destination,
                "city": city,
                "extensions": "all",
                "strategy": 0,
            }
            data = self._request_amap_json(
                f"{self.base_url}/v3/direction/transit/integrated",
                params=params,
                api_name="transit_route",
            )
            print(f"[AMapClient] _transit_route response: {data}")
        except Exception as e:
            print(f"[AMapClient] _transit_route error: {e}")
            return self._empty_route("transit")
        
        route = data.get("route") or {}
        transits = route.get("transits") or []
        if not transits:
            print(f"[AMapClient] _transit_route: no transits in response")
            return self._empty_route("transit")

        transit = transits[0]
        segments = transit.get("segments") or []
        steps: List[Dict[str, Any]] = []
        polylines: List[str] = []

        for segment in segments:
            walking = segment.get("walking") or {}
            walking_steps = walking.get("steps") or []
            for step in walking_steps:
                if step.get("polyline"):
                    polylines.append(step.get("polyline"))
                steps.append(
                    {
                        "instruction": step.get("instruction", ""),
                        "distance": step.get("distance"),
                        "duration": step.get("duration"),
                        "polyline": step.get("polyline", ""),
                    }
                )

            bus = segment.get("bus") or {}
            buslines = bus.get("buslines") or []
            for busline in buslines:
                bus_name = busline.get("name", "公交")
                dep_stop = (busline.get("departure_stop") or {}).get("name", "")
                arr_stop = (busline.get("arrival_stop") or {}).get("name", "")
                polyline = busline.get("polyline", "")
                if polyline:
                    polylines.append(polyline)
                steps.append(
                    {
                        "instruction": f"乘坐{bus_name} {dep_stop}上车 {arr_stop}下车".strip(),
                        "distance": busline.get("distance"),
                        "duration": busline.get("duration"),
                        "polyline": polyline,
                    }
                )

            railway = segment.get("railway") or {}
            if railway:
                trip = railway.get("trip", "")
                dep = (railway.get("departure_stop") or {}).get("name", "")
                arr = (railway.get("arrival_stop") or {}).get("name", "")
                steps.append(
                    {
                        "instruction": f"乘坐{trip} {dep}上车 {arr}下车".strip(),
                        "distance": railway.get("distance"),
                        "duration": railway.get("time"),
                        "polyline": "",
                    }
                )

        return {
            "type": "transit",
            "distance_m": float(transit.get("distance") or 0),
            "duration_s": float(transit.get("duration") or 0),
            "taxi_cost": float(transit.get("cost") or 0) if transit.get("cost") else None,
            "steps": steps,
            "polyline": ";".join([polyline for polyline in polylines if polyline]),
        }

    def transit_hubs(self, city: str, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        查询交通枢纽，供交通枢纽 Agent 使用。
        """
        keywords = keywords or ["火车站", "高铁站", "机场", "客运站", "港口"]
        hubs: List[Dict[str, Any]] = []
        for keyword in keywords:
            hubs.extend(self.search_poi(keyword, city=city, page_size=6))
        dedup: Dict[str, Dict[str, Any]] = {}
        for hub in hubs:
            dedup[hub["name"]] = hub
        return list(dedup.values())

    def intercity_transport_candidates(
        self,
        departure_city: str,
        destination_city: str,
        modes: List[str],
        departure_time: str,
        return_time: str,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        高德在城际票务上并不总能直接满足产品级购票结果，这里先做统一结构封装。
        如果后续接入 12306/航班聚合平台，只需替换此方法内部实现。
        """
        outbound: List[Dict[str, Any]] = []
        inbound: List[Dict[str, Any]] = []

        mode_templates = {
            "高铁": {"duration": "4小时45分", "price": 468, "code_prefix": "G"},
            "飞机": {"duration": "1小时45分", "price": 680, "code_prefix": "MU"},
            "大巴": {"duration": "7小时30分", "price": 260, "code_prefix": "BUS"},
            "顺风车": {"duration": "5小时50分", "price": 420, "code_prefix": "CAR"},
        }

        for index, mode in enumerate(modes):
            tpl = mode_templates.get(mode, {"duration": "5小时00分", "price": 399, "code_prefix": "T"})
            outbound.append(
                {
                    "id": f"out_{mode}_{index}",
                    "mode": mode,
                    "code": f"{tpl['code_prefix']}{1357 + index}",
                    "departure_station": f"{departure_city}交通枢纽",
                    "arrival_station": f"{destination_city}交通枢纽",
                    "departure_time": departure_time[-5:] if len(departure_time) >= 5 else "09:00",
                    "arrival_time": "15:55" if mode != "飞机" else "12:05",
                    "duration_text": tpl["duration"],
                    "price": tpl["price"],
                    "seat_action": "选座" if mode in ["高铁", "飞机"] else "查看",
                    "source": "amap_fallback",
                }
            )
            inbound.append(
                {
                    "id": f"ret_{mode}_{index}",
                    "mode": mode,
                    "code": f"{tpl['code_prefix']}{2468 + index}",
                    "departure_station": f"{destination_city}交通枢纽",
                    "arrival_station": f"{departure_city}交通枢纽",
                    "departure_time": "10:30",
                    "arrival_time": return_time[-5:] if len(return_time) >= 5 else "18:00",
                    "duration_text": tpl["duration"],
                    "price": tpl["price"],
                    "seat_action": "选座" if mode in ["高铁", "飞机"] else "查看",
                    "source": "amap_fallback",
                }
            )

        return {"outbound": outbound, "return": inbound}


class MeituanClient:
    """
    美团服务封装（使用 CLI 客户端）
    """
    def __init__(self, token: Optional[str] = None):
        from services.meituan_cli_client import MeituanCLIClient
        self.cli_client = MeituanCLIClient(token)
        self.token = token or os.getenv(
            "MEITUAN_TOKEN",
            "美团key",
        )

    def is_ready(self) -> bool:
        return self.cli_client.is_ready()

    def search_hotels(self, city: str, anchor: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """使用 CLI 客户端搜索酒店"""
        try:
            return self.cli_client.search_hotels(city, anchor, page_size)
        except Exception:
            return self.cli_client._fallback_hotels(city, anchor, page_size)

    def search_attractions(self, city: str, interests: Optional[List[str]] = None, page_size: int = 6) -> List[Dict[str, Any]]:
        """使用 CLI 客户端搜索景点"""
        try:
            return self.cli_client.search_attractions(city, interests, page_size)
        except Exception:
            return self.cli_client._fallback_attractions(city, interests, page_size)

    def search_foods(self, city: str, area: str = "", preferences: Optional[List[str]] = None, page_size: int = 6) -> List[Dict[str, Any]]:
        """使用 CLI 客户端搜索美食"""
        try:
            return self.cli_client.search_foods(city, area, preferences, page_size)
        except Exception:
            return self.cli_client._fallback_foods(city, area, preferences, page_size)
