"""
补充型多 Agent：
- 景点 Agent
- 住宿 Agent
- 餐饮 Agent
- 价格汇总 Agent
- 卡片 Agent
"""
from typing import Any, Dict, List, Optional, Tuple

from models.trip_models import PriceSummary, TimelineBlock, TripRequest
from services.provider_clients import MeituanClient


class AttractionPlanningAgent:
    def __init__(self, meituan_client: Optional[MeituanClient] = None):
        self.name = "景点规划员"
        self.meituan = meituan_client or MeituanClient()

    def plan(self, trip: TripRequest) -> List[Dict[str, Any]]:
        attractions = self.meituan.search_attractions(
            city=trip.destination,
            interests=trip.interests,
            page_size=6,
        )
        results: List[Dict[str, Any]] = []
        for index, item in enumerate(attractions):
            day = 1 if index < 2 else 2
            slot = "morning" if index % 2 == 0 else "afternoon"
            results.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "address": item["address"],
                    "ticket_price": item["price"],
                    "rating": item["rating"],
                    "open_time": item["open_time"],
                    "duration_text": item["duration_text"],
                    "tags": item.get("tags", []),
                    "day": day,
                    "time_slot": slot,
                    "recommended_time": "09:30" if slot == "morning" else "14:00",
                    "source": item.get("source", "meituan_fallback"),
                }
            )
        return results


class HotelPlanningAgent:
    def __init__(self, meituan_client: Optional[MeituanClient] = None):
        self.name = "住宿规划员"
        self.meituan = meituan_client or MeituanClient()

    def plan(self, trip: TripRequest, anchor: Optional[str] = None) -> Dict[str, Any]:
        hotel_anchor = anchor or trip.hotel_anchor or f"{trip.destination}推荐住宿区域"
        hotels = self.meituan.search_hotels(
            city=trip.destination,
            anchor=hotel_anchor,
            page_size=5,
        )
        
        # 确保 hotels 是列表
        if not isinstance(hotels, list):
            hotels = []
        
        average_price = round(sum(item.get("price", 0) for item in hotels) / len(hotels), 2) if hotels else 0
        return {
            "anchor": hotel_anchor,
            "average_price": average_price,
            "selected_hotel": hotels[0] if hotels else None,
            "options": hotels,
            "change_location_enabled": True,
        }


class FoodPlanningAgent:
    def __init__(self, meituan_client: Optional[MeituanClient] = None):
        self.name = "餐饮规划员"
        self.meituan = meituan_client or MeituanClient()

    def plan(self, trip: TripRequest, area: str = "") -> List[Dict[str, Any]]:
        foods = self.meituan.search_foods(
            city=trip.destination,
            area=area or trip.hotel_anchor or f"{trip.destination}景点周边",
            preferences=trip.food_preferences,
            page_size=6,
        )
        schedule: List[Dict[str, Any]] = []
        meal_slot_map = [
            ("早餐", "08:30"),
            ("午餐", "12:30"),
            ("晚餐", "18:30"),
        ]
        for index, item in enumerate(foods[:3]):
            meal_type, meal_time = meal_slot_map[index]
            schedule.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "address": item["address"],
                    "price": item["price"],
                    "rating": item["rating"],
                    "meal_type": meal_type,
                    "meal_time": meal_time,
                    "tags": item.get("tags", []),
                    "source": item.get("source", "meituan_fallback"),
                }
            )
        return schedule


class PricingSummaryAgent:
    def __init__(self):
        self.name = "预算汇总员"

    def summarize(
        self,
        transport_hub_plan: Dict[str, Any],
        hotel_plan: Dict[str, Any],
        attraction_plan: List[Dict[str, Any]],
        food_plan: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        pricing = PriceSummary()

        outbound_main = transport_hub_plan.get("outbound", {}).get("main_transport", [])
        return_main = transport_hub_plan.get("return", {}).get("main_transport", [])
        outbound_local = transport_hub_plan.get("outbound", {}).get("local_access", {}).get("primary", {})
        return_local = transport_hub_plan.get("return", {}).get("local_access", {}).get("primary", {})

        if outbound_main:
            pricing.transport += float(outbound_main[0].get("price") or 0)
        if return_main:
            pricing.transport += float(return_main[0].get("price") or 0)
        pricing.transport += float(outbound_local.get("cost") or 0)
        pricing.transport += float(return_local.get("cost") or 0)

        selected_hotel = hotel_plan.get("selected_hotel") or {}
        pricing.hotel += float(selected_hotel.get("price") or hotel_plan.get("average_price") or 0)

        for attraction in attraction_plan:
            pricing.attraction += float(attraction.get("ticket_price") or 0)

        for food in food_plan:
            pricing.food += float(food.get("price") or 0)

        return pricing.to_dict()


class CardAgent:
    def __init__(self):
        self.name = "卡片设计员"

    def build_cards(
        self,
        trip: TripRequest,
        transport_hub_plan: Dict[str, Any],
        hotel_plan: Dict[str, Any],
        attraction_plan: List[Dict[str, Any]],
        food_plan: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "transport": self._build_transport_cards(transport_hub_plan),
            "localTransport": self._build_local_transport_cards(transport_hub_plan),
            "hotel": self._build_hotel_cards(hotel_plan),
            "attraction": self._build_attraction_cards(attraction_plan),
            "food": self._build_food_cards(food_plan),
        }

    def build_timeline(
        self,
        trip: TripRequest,
        transport_hub_plan: Dict[str, Any],
        hotel_plan: Dict[str, Any],
        attraction_plan: List[Dict[str, Any]],
        food_plan: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        blocks: List[TimelineBlock] = []

        outbound_local = transport_hub_plan.get("outbound", {}).get("local_access", {}).get("primary", {})
        outbound_main = transport_hub_plan.get("outbound", {}).get("main_transport", [])
        selected_hotel = hotel_plan.get("selected_hotel") or None
        allocated_attractions = self._allocate_attraction_times(attraction_plan)

        if outbound_local:
            blocks.append(
                TimelineBlock(
                    id="timeline_local_outbound",
                    day=1,
                    block_type="transport_local",
                    title=outbound_local.get("description", "前往交通枢纽"),
                    subtitle=outbound_local.get("mode", ""),
                    start_time="",
                    end_time="",
                    price=float(outbound_local.get("cost") or 0),
                    location=trip.departure,
                    card_type="local_transport",
                    selected=True,
                    fields=outbound_local,
                )
            )

        if outbound_main:
            item = outbound_main[0]
            blocks.append(
                TimelineBlock(
                    id=item["id"],
                    day=1,
                    block_type="transport_main",
                    title=f'{item["departure_station"]} — {item["arrival_station"]}',
                    subtitle=item["code"],
                    start_time=item["departure_time"],
                    end_time=item["arrival_time"],
                    price=float(item["price"] or 0),
                    location=item["arrival_station"],
                    card_type="main_transport",
                    selected=True,
                    alternatives=[option["id"] for option in outbound_main[1:]],
                    fields=item,
                )
            )

        if selected_hotel:
            blocks.append(
                TimelineBlock(
                    id=selected_hotel["id"],
                    day=1,
                    block_type="hotel",
                    title=selected_hotel["name"],
                    subtitle=hotel_plan.get("anchor", ""),
                    start_time="办理入住",
                    end_time="",
                    price=float(selected_hotel.get("price") or 0),
                    location=selected_hotel.get("address", ""),
                    card_type="hotel",
                    selected=True,
                    alternatives=[item["id"] for item in hotel_plan.get("options", [])[1:]],
                    fields=selected_hotel,
                )
            )

        for item in allocated_attractions:
            blocks.append(
                TimelineBlock(
                    id=item["id"],
                    day=int(item.get("day") or 1),
                    block_type="attraction",
                    title=item["name"],
                    subtitle=item.get("address", ""),
                    start_time=item.get("recommended_time", ""),
                    end_time=item.get("end_time", ""),
                    price=float(item.get("ticket_price") or 0),
                    location=item.get("address", ""),
                    card_type="attraction",
                    selected=True,
                    fields=item,
                )
            )

        for item in food_plan:
            meal_day = int(item.get("day") or 1)
            blocks.append(
                TimelineBlock(
                    id=item["id"],
                    day=meal_day,
                    block_type="food",
                    title=item["name"],
                    subtitle=item.get("meal_type", ""),
                    start_time=item.get("meal_time", ""),
                    end_time="",
                    price=float(item.get("price") or 0),
                    location=item.get("address", ""),
                    card_type="food",
                    selected=True,
                    fields=item,
                )
            )

        return [block.to_dict() for block in self._sort_timeline_blocks(blocks)]

    def _build_local_transport_cards(self, transport_hub_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        cards: List[Dict[str, Any]] = []
        for direction_key, day_label in [("outbound", "出行"), ("return", "返程")]:
            local_access = transport_hub_plan.get(direction_key, {}).get("local_access", {})
            primary = local_access.get("primary")
            if not primary:
                continue

            cards.append(
                {
                    "id": f"{direction_key}_local_card",
                    "cardType": "local_transport",
                    "sectionLabel": day_label,
                    "transportIcon": self._map_local_transport_icon(primary.get("mode", "")),
                    "transportType": primary.get("mode", ""),
                    "time": f'{primary.get("duration_min", 0)} 分钟',
                    "location0": primary.get("description", "").split(" → ")[0] if " → " in primary.get("description", "") else "",
                    "location1": "交通枢纽",
                    "estimatedCost": primary.get("cost", 0),
                    "alternatives": local_access.get("alternatives", []),
                    "map": {
                        "provider": "amap",
                        "polyline": "",
                    },
                }
            )
        return cards

    def _build_transport_cards(self, transport_hub_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        cards: List[Dict[str, Any]] = []
        for bucket in ["outbound", "return"]:
            for item in transport_hub_plan.get(bucket, {}).get("main_transport", []):
                cards.append(
                    {
                        "id": item["id"],
                        "cardType": "main_transport",
                        "routeText": f'{item["departure_station"]}——{item["arrival_station"]}',
                        "departureTime": item["departure_time"],
                        "arrivalTime": item["arrival_time"],
                        "durationText": item["duration_text"],
                        "transportType": item["mode"],
                        "codeText": item["code"],
                        "price": item["price"],
                        "seatAction": item.get("seat_action", "查看"),
                    }
                )
        return cards

    def _build_hotel_cards(self, hotel_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        cards: List[Dict[str, Any]] = []
        selected_hotel = hotel_plan.get("selected_hotel")
        if selected_hotel:
            cards.append(
                {
                    "id": selected_hotel["id"],
                    "cardType": "hotel",
                    "anchorText": hotel_plan.get("anchor", ""),
                    "changeAnchorAction": "更换住宿地点",
                    "hotelName": selected_hotel["name"],
                    "hotelAddress": selected_hotel["address"],
                    "price": selected_hotel["price"],
                    "actionText": "办理入住",
                    "image": selected_hotel.get("image", ""),
                    "reason": selected_hotel.get("reason", ""),
                }
            )

        for option in hotel_plan.get("options", [])[1:]:
            cards.append(
                {
                    "id": option["id"],
                    "cardType": "hotel_option",
                    "anchorText": hotel_plan.get("anchor", ""),
                    "changeAnchorAction": "更换住宿地点",
                    "hotelName": option["name"],
                    "hotelAddress": option["address"],
                    "price": option["price"],
                    "actionText": "办理入住",
                    "image": option.get("image", ""),
                    "reason": option.get("reason", ""),
                }
            )
        return cards

    def _build_attraction_cards(self, attraction_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "id": item["id"],
                "cardType": "attraction",
                "title": item["name"],
                "address": item["address"],
                "price": item["ticket_price"],
                "rating": item["rating"],
                "openTime": item["open_time"],
                "durationText": item["duration_text"],
                "day": item["day"],
                "time": item["recommended_time"],
                "tags": item.get("tags", []),
            }
            for item in attraction_plan
        ]

    def _build_food_cards(self, food_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "id": item["id"],
                "cardType": "food",
                "title": item["name"],
                "address": item["address"],
                "price": item["price"],
                "rating": item["rating"],
                "mealType": item["meal_type"],
                "mealTime": item["meal_time"],
                "tags": item.get("tags", []),
            }
            for item in food_plan
        ]

    def _map_local_transport_icon(self, mode: str) -> str:
        mapping = {
            "打车": "car",
            "步行": "walk",
            "地铁": "metro",
            "骑行": "bike",
            "公交": "bus",
        }
        return mapping.get(mode, "car")

    def _allocate_attraction_times(self, attraction_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        allocated = [dict(item) for item in attraction_plan]
        day_slot_groups: Dict[Tuple[int, str], List[Dict[str, Any]]] = {}

        for item in allocated:
            day = int(item.get("day") or 1)
            slot = item.get("time_slot") or self._infer_slot_from_time(item.get("recommended_time", ""))
            if slot not in ("morning", "afternoon"):
                slot = "morning"
            item["time_slot"] = slot
            day_slot_groups.setdefault((day, slot), []).append(item)

        for (day, slot), items in day_slot_groups.items():
            start_minutes, end_minutes = (570, 750) if slot == "morning" else (840, 1080)
            segment_count = max(1, len(items))
            segment_span = (end_minutes - start_minutes) // segment_count

            for index, item in enumerate(items):
                item_start = start_minutes + (index * segment_span)
                item_end = end_minutes if index == segment_count - 1 else start_minutes + ((index + 1) * segment_span)
                item["day"] = day
                item["recommended_time"] = self._format_minutes(item_start)
                item["end_time"] = self._format_minutes(item_end)

        return allocated

    def _infer_slot_from_time(self, value: str) -> str:
        if not value or ":" not in value:
            return "morning"
        hour = int(value.split(":")[0])
        if hour < 12:
            return "morning"
        return "afternoon"

    def _format_minutes(self, total_minutes: int) -> str:
        hour = max(0, total_minutes // 60)
        minute = max(0, total_minutes % 60)
        return f"{hour:02d}:{minute:02d}"

    def _sort_timeline_blocks(self, blocks: List[TimelineBlock]) -> List[TimelineBlock]:
        def block_sort_key(block: TimelineBlock):
            start = block.start_time or ""
            if start == "办理入住":
                return (block.day, 23 * 60)
            if ":" in start:
                hour, minute = start.split(":")
                return (block.day, int(hour) * 60 + int(minute))
            return (block.day, 9999)

        return sorted(blocks, key=block_sort_key)