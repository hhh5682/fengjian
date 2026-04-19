"""
主控编排 Agent
负责协调所有子 Agent，生成完整的旅行规划方案。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.attraction_agent import AttractionAgent
from agents.food_agent import FoodAgent
from agents.hotel_agent import HotelAgent
from agents.local_transport_agent import LocalTransportAgent
from agents.transport_agent import TransportAgent
from models.trip_models import (
    AttractionItem,
    MealItem,
    PlannerResult,
    PriceSummary,
    StructuredTripPlan,
    TimelineBlock,
    TripRequest,
)
from services.provider_clients import AMapClient, MeituanClient


class OrchestratorAgent:
    def __init__(
        self,
        amap_client: Optional[AMapClient] = None,
        meituan_client: Optional[MeituanClient] = None,
    ):
        self.name = "主控编排员"
        self.amap = amap_client or AMapClient()
        self.meituan = meituan_client or MeituanClient()

        self.transport_agent = TransportAgent()
        self.attraction_agent = AttractionAgent()
        self.hotel_agent = HotelAgent()
        self.food_agent = FoodAgent()
        self.local_transport_agent = LocalTransportAgent(self.amap)

    def plan(
        self,
        trip_request: TripRequest,
    ) -> Dict[str, Any]:
        """
        生成完整旅行规划。

        流程：
        1. 大交通 Agent 先规划去程/返程
        2. 景点 Agent 基于去程结束时间到返程开始时间规划景点
        3. 餐饮 Agent 从景点中提取午饭/晚饭约束
        4. 住宿 Agent 基于去程结束日期到返程开始日期规划酒店
        5. 按时间字段生成卡片和时间轴
        6. 汇总价格
        """
        try:
            transport_plan_dict = self.transport_agent.plan(
                departure=trip_request.departure,
                destination=trip_request.destination,
                departure_time=trip_request.departure_time,
                return_time=trip_request.return_time,
            )

            outbound = transport_plan_dict.get("outbound")
            return_plan = transport_plan_dict.get("return")
            outbound_selected = outbound.selected_option if outbound else None
            return_selected = return_plan.selected_option if return_plan else None

            if not outbound_selected or not return_selected:
                raise ValueError("大交通规划结果不完整，无法生成后续行程")

            attraction_start_date, attraction_start_time = self._extract_transport_datetime(
                outbound_selected.arrival_time,
                trip_request.departure_time,
            )
            attraction_end_date, attraction_end_time = self._extract_transport_datetime(
                return_selected.departure_time,
                trip_request.return_time,
            )

            attractions = self.attraction_agent.plan(
                destination=trip_request.destination,
                arrival_date=attraction_start_date,
                arrival_time=attraction_start_time,
                departure_date=attraction_end_date,
                departure_time=attraction_end_time,
            )
            hotels = self.hotel_agent.plan(
                destination=trip_request.destination,
                check_in_date=attraction_start_date,
                check_out_date=attraction_end_date,
            )

            foods = self.food_agent.plan(
                attractions=attractions,
                hotels=hotels,
                transport_arrival_anchor=outbound_selected.arrival_station,
            )

            # 规划小交通
            local_transports = self._plan_local_transports(
                trip_request,
                outbound_selected,
                attractions,
                foods,
                hotels,
            )

            structured_plan = StructuredTripPlan(
                transport=transport_plan_dict,
                attractions=attractions,
                foods=foods,
                hotels=hotels,
                local_transports=local_transports,
            )

            pricing = self._build_pricing(
                structured_plan,
                check_in_date=attraction_start_date,
                check_out_date=attraction_end_date,
            )

            simplified_local_transports = self._simplify_local_transports(local_transports)

            response_structured_plan = {
                "transport": structured_plan.to_dict().get("transport", {}),
                "attractions": [item.to_dict() for item in attractions],
                "foods": [item.to_dict() for item in foods],
                "hotels": hotels.to_dict(),
                "local_transports": simplified_local_transports,
            }

            cards = self._build_cards(
                StructuredTripPlan(
                    transport=transport_plan_dict,
                    attractions=attractions,
                    foods=foods,
                    hotels=hotels,
                    local_transports=simplified_local_transports,
                )
            )
            timeline = self._build_timeline(
                StructuredTripPlan(
                    transport=transport_plan_dict,
                    attractions=attractions,
                    foods=foods,
                    hotels=hotels,
                    local_transports=simplified_local_transports,
                )
            )

            result = PlannerResult(
                trip=trip_request.to_dict(),
                transport_hub={
                    "outbound": transport_plan_dict["outbound"].to_dict(),
                    "return": transport_plan_dict["return"].to_dict(),
                },
                attractions=[item.to_dict() for item in attractions],
                hotels=[item.to_dict() for item in hotels.options],
                foods=[item.to_dict() for item in foods],
                cards=cards,
                timeline=[item.to_dict() for item in timeline],
                pricing=pricing.to_dict(),
                warnings=[],
                structured_plan=response_structured_plan,
                local_transports=simplified_local_transports,
            )

            result_dict = result.to_dict()
            result_dict = self._remove_polylines(result_dict)

            return {
                "code": 0,
                "data": result_dict,
                "message": "规划成功",
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "code": 500,
                "data": None,
                "message": f"规划失败: {str(e)}",
            }

    def replan_with_hotel_change(
        self,
        trip_request: TripRequest,
        new_hotel_anchor: str,
    ) -> Dict[str, Any]:
        """
        当前版本保留接口，直接重新规划。
        """
        return self.plan(trip_request)

    def _build_cards(self, structured_plan: StructuredTripPlan) -> Dict[str, List[Dict[str, Any]]]:
        outbound = structured_plan.transport.get("outbound")
        return_plan = structured_plan.transport.get("return")

        cards = {
            "transport": [],
            "attractions": [],
            "foods": [],
            "hotels": [],
        }

        if outbound:
            cards["transport"].append({
                "id": "transport-outbound",
                "type": "transport",
                "label": "去程",
                **outbound.to_dict(),
            })

        if return_plan:
            cards["transport"].append({
                "id": "transport-return",
                "type": "transport",
                "label": "返程",
                **return_plan.to_dict(),
            })

        for idx, item in enumerate(structured_plan.attractions):
            cards["attractions"].append({
                "id": f"attraction-{idx}",
                "type": "attraction",
                **item.to_dict(),
            })

        for idx, item in enumerate(structured_plan.foods):
            cards["foods"].append({
                "id": f"food-{idx}",
                "type": "food",
                **item.to_dict(),
            })

        cards["hotels"].append({
            "id": "hotel-plan",
            "type": "hotel",
            **structured_plan.hotels.to_dict(),
        })

        return cards

    def _build_timeline(self, structured_plan: StructuredTripPlan) -> List[TimelineBlock]:
        """
        时间轴逻辑：
        1. 保留去程大交通、返程大交通；
        2. 仅保留时间位于去程结束与返程开始之间的有效节点（景点/饮食/住宿）；
        3. 对有效节点按时间排序；
        4. 把初始小交通和相邻有效节点之间的小交通插入时间轴；
        5. 最终按时间排序输出。
        """
        timeline: List[TimelineBlock] = []

        outbound = structured_plan.transport.get("outbound")
        return_plan = structured_plan.transport.get("return")
        if not outbound or not outbound.selected_option or not return_plan or not return_plan.selected_option:
            return timeline

        outbound_selected = outbound.selected_option
        return_selected = return_plan.selected_option

        outbound_end_day = self._extract_day_label(outbound_selected.arrival_time)
        outbound_end_clock = self._extract_clock_only(outbound_selected.arrival_time) or "00:00"
        return_start_day = self._extract_day_label(return_selected.departure_time)
        return_start_clock = self._extract_clock_only(return_selected.departure_time) or "23:59"

        timeline.append(
            TimelineBlock(
                id="timeline-transport-outbound",
                day=self._extract_day_number_from_label(self._extract_day_label(outbound_selected.departure_time)),
                block_type="transport",
                title=f"{outbound_selected.transport_type} {outbound_selected.trip_number}",
                subtitle="去程大交通",
                start_time=self._extract_clock_only(outbound_selected.departure_time) or outbound_selected.departure_time,
                end_time=self._extract_clock_only(outbound_selected.arrival_time) or outbound_selected.arrival_time,
                price=outbound_selected.estimated_price,
                location=f"{outbound_selected.departure_station} → {outbound_selected.arrival_station}",
                card_type="transport",
                selected=True,
                alternatives=[f"{item.transport_type} {item.trip_number}" for item in outbound.options],
                fields=outbound.to_dict(),
            )
        )

        valid_nodes: List[Dict[str, Any]] = []

        for idx, item in enumerate(structured_plan.attractions):
            day_label = item.day_label or ""
            clock = item.start_time or "09:00"
            if not self._is_between_range(day_label, clock, outbound_end_day, outbound_end_clock, return_start_day, return_start_clock):
                continue
            valid_nodes.append({
                "id": f"timeline-attraction-{idx}",
                "day": self._extract_day_number_from_label(day_label),
                "day_label": day_label,
                "time": clock,
                "type": "attraction",
                "title": item.location,
                "subtitle": f"开放时间：{item.opening_hours}",
                "start_time": item.start_time,
                "end_time": item.end_time,
                "price": item.estimated_price_value,
                "location": item.location,
                "card_type": "attraction",
                "selected": True,
                "alternatives": [],
                "fields": item.to_dict(),
            })

        for idx, item in enumerate(structured_plan.foods):
            selected = item.selected_option
            day_label = item.day_label or ""
            clock = item.meal_clock or "12:00"
            if not selected:
                continue
            if not self._is_between_range(day_label, clock, outbound_end_day, outbound_end_clock, return_start_day, return_start_clock):
                continue
            valid_nodes.append({
                "id": f"timeline-food-{idx}",
                "day": self._extract_day_number_from_label(day_label),
                "day_label": day_label,
                "time": clock,
                "type": "food",
                "title": selected.name,
                "subtitle": item.nearby_attraction,
                "start_time": clock,
                "end_time": clock,
                "price": selected.estimated_price,
                "location": selected.name,
                "card_type": "food",
                "selected": True,
                "alternatives": [opt.name for opt in item.options],
                "fields": item.to_dict(),
            })

        if structured_plan.hotels.selected_option:
            hotel = structured_plan.hotels.selected_option
            hotel_day_label = outbound_end_day or "1.1"
            hotel_clock = "21:00"
            if self._is_between_range(hotel_day_label, hotel_clock, outbound_end_day, outbound_end_clock, return_start_day, return_start_clock):
                valid_nodes.append({
                    "id": "timeline-hotel",
                    "day": self._extract_day_number_from_label(hotel_day_label),
                    "day_label": hotel_day_label,
                    "time": hotel_clock,
                    "type": "hotel",
                    "title": hotel.hotel_name,
                    "subtitle": "住宿推荐",
                    "start_time": hotel_clock,
                    "end_time": "23:00",
                    "price": hotel.estimated_price,
                    "location": hotel.hotel_name,
                    "card_type": "hotel",
                    "selected": True,
                    "alternatives": [opt.hotel_name for opt in structured_plan.hotels.options],
                    "fields": structured_plan.hotels.to_dict(),
                })

        valid_nodes.sort(key=lambda item: (self._sort_day_label(item["day_label"]), self._time_to_minutes(item["time"])))

        local_transport_blocks: List[TimelineBlock] = []
        for idx, transport in enumerate(structured_plan.local_transports):
            from_location = transport.get("from_location", {}).get("name", "")
            to_location = transport.get("to_location", {}).get("name", "")
            sort_day_label = transport.get("sort_day_label") or ""
            sort_time = transport.get("sort_time") or "00:00"
            local_transport_blocks.append(
                TimelineBlock(
                    id=f"timeline-local-transport-{idx}",
                    day=self._extract_day_number_from_label(sort_day_label),
                    block_type="local_transport",
                    title=f"{from_location} → {to_location}",
                    subtitle="本地交通",
                    start_time=sort_time,
                    end_time=sort_time,
                    price=0.0,
                    location=f"{from_location} → {to_location}",
                    card_type="local_transport",
                    selected=True,
                    alternatives=[],
                    fields={
                        "from_location": transport.get("from_location"),
                        "to_location": transport.get("to_location"),
                        "sort_time": transport.get("sort_time"),
                        "sort_day_label": transport.get("sort_day_label"),
                        "selected_index": transport.get("selected_index", 0),
                        "routes": transport.get("routes", []),
                    },
                )
            )

        for node in valid_nodes:
            timeline.append(
                TimelineBlock(
                    id=node["id"],
                    day=node["day"],
                    block_type=node["type"],
                    title=node["title"],
                    subtitle=node["subtitle"],
                    start_time=node["start_time"],
                    end_time=node["end_time"],
                    price=node["price"],
                    location=node["location"],
                    card_type=node["card_type"],
                    selected=node["selected"],
                    alternatives=node["alternatives"],
                    fields=node["fields"],
                )
            )

        timeline.extend(local_transport_blocks)

        timeline.append(
            TimelineBlock(
                id="timeline-transport-return",
                day=self._extract_day_number_from_label(self._extract_day_label(return_selected.departure_time)),
                block_type="transport",
                title=f"{return_selected.transport_type} {return_selected.trip_number}",
                subtitle="返程大交通",
                start_time=self._extract_clock_only(return_selected.departure_time) or return_selected.departure_time,
                end_time=self._extract_clock_only(return_selected.arrival_time) or return_selected.arrival_time,
                price=return_selected.estimated_price,
                location=f"{return_selected.departure_station} → {return_selected.arrival_station}",
                card_type="transport",
                selected=True,
                alternatives=[f"{item.transport_type} {item.trip_number}" for item in return_plan.options],
                fields=return_plan.to_dict(),
            )
        )

        timeline.sort(key=self._timeline_sort_key)
        return timeline

    def _build_pricing(
        self,
        structured_plan: StructuredTripPlan,
        check_in_date: str,
        check_out_date: str,
    ) -> PriceSummary:
        transport_total = 0.0
        attraction_total = 0.0
        food_total = 0.0
        hotel_total = 0.0

        outbound = structured_plan.transport.get("outbound")
        if outbound and outbound.selected_option:
            transport_total += outbound.selected_option.estimated_price

        return_plan = structured_plan.transport.get("return")
        if return_plan and return_plan.selected_option:
            transport_total += return_plan.selected_option.estimated_price

        attraction_total = sum(item.estimated_price_value for item in structured_plan.attractions)
        food_total = sum(item.selected_option.estimated_price for item in structured_plan.foods if item.selected_option)

        if structured_plan.hotels.selected_option:
            nights = self._calculate_nights(check_in_date, check_out_date)
            hotel_total = structured_plan.hotels.selected_option.estimated_price * nights

        return PriceSummary(
            transport=transport_total,
            hotel=hotel_total,
            attraction=attraction_total,
            food=food_total,
        )

    def _calculate_nights(self, departure_time: str, return_time: str) -> int:
        try:
            dep = datetime.fromisoformat(self._normalize_iso_datetime(departure_time))
            ret = datetime.fromisoformat(self._normalize_iso_datetime(return_time))
            return max(1, (ret.date() - dep.date()).days)
        except Exception:
            return 1

    def _extract_transport_datetime(self, value: str, fallback_iso: str) -> tuple[str, str]:
        fallback = datetime.fromisoformat(self._normalize_iso_datetime(fallback_iso))
        date_label = f"{fallback.month}.{fallback.day}"
        time_label = fallback.strftime("%H:%M")

        if not value:
            return date_label, time_label

        day_match = datetime.strptime(fallback.strftime("%Y-%m-%d"), "%Y-%m-%d")
        del day_match  # keep implementation simple while preserving fallback year context

        date_match = None
        time_match = None

        import re

        date_search = re.search(r"(\d{1,2})\.(\d{1,2})", value)
        if date_search:
            date_label = f"{int(date_search.group(1))}.{int(date_search.group(2))}"

        time_search = re.search(r"(\d{1,2}:\d{2})", value)
        if time_search:
            time_label = time_search.group(1)

        return date_label, time_label

    def _normalize_iso_datetime(self, value: str) -> str:
        if "T" in value:
            return value
        if " " in value:
            date_part, time_part = value.split(" ", 1)
            return f"{date_part}T{time_part[:5]}"
        return f"{value}T00:00"

    def _extract_day_number_from_label(self, label: str) -> int:
        if not label:
            return 1
        if "." in label:
            try:
                return int(label.split(".")[1])
            except Exception:
                return 1
        try:
            return int(label)
        except Exception:
            return 1

    def _timeline_sort_key(self, block: TimelineBlock) -> tuple[int, int]:
        return (block.day, self._time_to_minutes(block.start_time or "99:99"))

    def _plan_local_transports(
        self,
        trip_request: TripRequest,
        outbound_selected: Any,
        attractions: List[AttractionItem],
        foods: List[MealItem],
        hotels: Any,
    ) -> List[Dict[str, Any]]:
        """
        小交通逻辑：
        1. 先得到有效节点：仅保留去程大交通结束时间与返程大交通开始时间之间的景点/饮食/住宿；
        2. 按节点时间排序；
        3. 规划用户输入地址 -> 去程大交通出发点的小交通，时间=去程出发前30分钟；
        4. 对每两个有效节点 A->B 规划小交通，时间=B前30分钟。
        """
        print("[OrchestratorAgent] ===== local transport planning start =====")
        local_transports: List[Dict[str, Any]] = []

        if not outbound_selected:
            return local_transports

        outbound_departure_day = self._extract_day_label(outbound_selected.departure_time)
        outbound_departure_clock = self._extract_clock_only(outbound_selected.departure_time) or "00:00"
        outbound_arrival_day = self._extract_day_label(outbound_selected.arrival_time)
        outbound_arrival_clock = self._extract_clock_only(outbound_selected.arrival_time) or "00:00"

        return_selected = self.transport_agent.plan(
            departure=trip_request.departure,
            destination=trip_request.destination,
            departure_time=trip_request.departure_time,
            return_time=trip_request.return_time,
        ).get("return")
        return_option = return_selected.selected_option if return_selected else None
        return_start_day = self._extract_day_label(return_option.departure_time) if return_option else ""
        return_start_clock = self._extract_clock_only(return_option.departure_time) if return_option else "23:59"

        valid_nodes: List[Dict[str, Any]] = []

        for idx, attraction in enumerate(attractions):
            day_label = attraction.day_label or ""
            clock = attraction.start_time or "09:00"
            if not self._is_between_range(day_label, clock, outbound_arrival_day, outbound_arrival_clock, return_start_day, return_start_clock):
                continue
            attraction_coords = self._coords_to_dict(getattr(attraction, "coords", None))
            if not self._has_valid_coords(attraction_coords):
                attraction_coords = self._resolve_place_coords(
                    name=attraction.location,
                    city=trip_request.destination,
                    fallback={
                        "lat": trip_request.destination_coords.lat + (idx * 0.01),
                        "lng": trip_request.destination_coords.lng + (idx * 0.01),
                    },
                )
            valid_nodes.append({
                "name": attraction.location,
                "type": "attraction",
                "coords": attraction_coords,
                "time": clock,
                "day_label": day_label,
            })

        for idx, food in enumerate(foods):
            if not food.selected_option:
                continue
            day_label = food.day_label or ""
            clock = food.meal_clock or "12:00"
            if not self._is_between_range(day_label, clock, outbound_arrival_day, outbound_arrival_clock, return_start_day, return_start_clock):
                continue
            food_coords = self._coords_to_dict(getattr(food.selected_option, "coords", None))
            if not self._has_valid_coords(food_coords):
                food_coords = self._resolve_place_coords(
                    name=food.selected_option.name,
                    city=trip_request.destination,
                    fallback={
                        "lat": trip_request.destination_coords.lat + (idx * 0.005),
                        "lng": trip_request.destination_coords.lng + (idx * 0.005),
                    },
                )
            valid_nodes.append({
                "name": food.selected_option.name,
                "type": "food",
                "coords": food_coords,
                "time": clock,
                "day_label": day_label,
            })

        if hotels and hotels.selected_option:
            hotel = hotels.selected_option
            hotel_coords = self._coords_to_dict(getattr(hotel, "coords", None))
            if not self._has_valid_coords(hotel_coords):
                hotel_coords = self._resolve_place_coords(
                    name=hotel.hotel_name,
                    city=trip_request.destination,
                    fallback={
                        "lat": trip_request.destination_coords.lat,
                        "lng": trip_request.destination_coords.lng,
                    },
                )
            hotel_day_label = outbound_arrival_day or "1.1"
            hotel_clock = "21:00"
            if self._is_between_range(hotel_day_label, hotel_clock, outbound_arrival_day, outbound_arrival_clock, return_start_day, return_start_clock):
                valid_nodes.append({
                    "name": hotel.hotel_name,
                    "type": "hotel",
                    "coords": hotel_coords,
                    "time": hotel_clock,
                    "day_label": hotel_day_label,
                })

        valid_nodes.sort(key=lambda x: (self._sort_day_label(x.get("day_label", "")), self._time_to_minutes(x.get("time", "00:00"))))

        if trip_request.departure and outbound_selected:
            user_coords = {
                "lat": trip_request.departure_coords.lat,
                "lng": trip_request.departure_coords.lng,
            }
            transport_hub_coords = self._resolve_place_coords(
                name=outbound_selected.departure_station,
                city=trip_request.departure,
                fallback={
                    "lat": trip_request.departure_coords.lat,
                    "lng": trip_request.departure_coords.lng,
                },
            )
            initial_transport = self.local_transport_agent.plan_initial_transport(
                user_location=trip_request.departure,
                user_coords=user_coords,
                transport_hub_location=outbound_selected.departure_station,
                transport_hub_coords=transport_hub_coords,
            )
            if initial_transport:
                departure_minutes = self._time_to_minutes(outbound_departure_clock)
                initial_minutes = max(0, departure_minutes - 30)
                initial_transport["sort_time"] = f"{initial_minutes // 60:02d}:{initial_minutes % 60:02d}"
                initial_transport["sort_day_label"] = outbound_departure_day
                local_transports.append(initial_transport)

        if valid_nodes:
            outbound_arrival_coords = self._resolve_place_coords(
                name=outbound_selected.arrival_station,
                city=trip_request.destination,
                fallback={
                    "lat": trip_request.destination_coords.lat,
                    "lng": trip_request.destination_coords.lng,
                },
            )
            first_node = valid_nodes[0]
            outbound_to_first = self.local_transport_agent.plan_between_items(
                from_item={
                    "name": outbound_selected.arrival_station,
                    "type": "transport",
                    "coords": outbound_arrival_coords,
                    "time": outbound_arrival_clock,
                    "day_label": outbound_arrival_day,
                },
                to_item=first_node,
            )
            if outbound_to_first:
                first_node_minutes = self._time_to_minutes(first_node.get("time", "00:00"))
                sort_minutes = max(0, first_node_minutes - 30)
                outbound_to_first["sort_time"] = f"{sort_minutes // 60:02d}:{sort_minutes % 60:02d}"
                outbound_to_first["sort_day_label"] = first_node.get("day_label") or outbound_arrival_day
                local_transports.append(outbound_to_first)

        for idx in range(len(valid_nodes) - 1):
            from_item = valid_nodes[idx]
            to_item = valid_nodes[idx + 1]
            between_transport = self.local_transport_agent.plan_between_items(
                from_item=from_item,
                to_item=to_item,
            )
            if not between_transport:
                continue
            to_minutes = self._time_to_minutes(to_item.get("time", "00:00"))
            sort_minutes = max(0, to_minutes - 30)
            between_transport["sort_time"] = f"{sort_minutes // 60:02d}:{sort_minutes % 60:02d}"
            between_transport["sort_day_label"] = to_item.get("day_label") or from_item.get("day_label") or ""
            local_transports.append(between_transport)

        if valid_nodes and return_option:
            last_node = valid_nodes[-1]
            return_coords = self._resolve_place_coords(
                name=return_option.departure_station,
                city=trip_request.destination,
                fallback={
                    "lat": trip_request.destination_coords.lat,
                    "lng": trip_request.destination_coords.lng,
                },
            )
            last_to_return = self.local_transport_agent.plan_between_items(
                from_item=last_node,
                to_item={
                    "name": return_option.departure_station,
                    "type": "transport",
                    "coords": return_coords,
                    "time": return_start_clock,
                    "day_label": return_start_day,
                },
            )
            if last_to_return:
                return_minutes = self._time_to_minutes(return_start_clock)
                sort_minutes = max(0, return_minutes - 30)
                last_to_return["sort_time"] = f"{sort_minutes // 60:02d}:{sort_minutes % 60:02d}"
                last_to_return["sort_day_label"] = return_start_day
                local_transports.append(last_to_return)

        print(f"[OrchestratorAgent] ===== local transport planning end total={len(local_transports)} =====")
        return local_transports

    def _is_after_outbound_arrival(self, item_day: str, item_time: str, arrival_day: str, arrival_minutes: int) -> bool:
        """判断项目是否在大交通到达后"""
        item_minutes = self._time_to_minutes(item_time)

        item_day_tuple = self._sort_day_label(item_day)
        arrival_day_tuple = self._sort_day_label(arrival_day)

        if item_day_tuple > arrival_day_tuple:
            return True
        if item_day_tuple < arrival_day_tuple:
            return False

        return item_minutes >= arrival_minutes

    def _is_between_range(
        self,
        item_day: str,
        item_time: str,
        start_day: str,
        start_time: str,
        end_day: str,
        end_time: str,
    ) -> bool:
        item_day_tuple = self._sort_day_label(item_day)
        start_day_tuple = self._sort_day_label(start_day)
        end_day_tuple = self._sort_day_label(end_day)

        item_minutes = self._time_to_minutes(item_time)
        start_minutes = self._time_to_minutes(start_time)
        end_minutes = self._time_to_minutes(end_time)

        if item_day_tuple < start_day_tuple or item_day_tuple > end_day_tuple:
            return False
        if item_day_tuple == start_day_tuple and item_minutes < start_minutes:
            return False
        if item_day_tuple == end_day_tuple and item_minutes > end_minutes:
            return False
        return True

    def _time_to_minutes(self, time_str: str) -> int:
        """将时间字符串转换为分钟数，用于排序"""
        try:
            parts = str(time_str or "00:00").split(":")
            hours = int(parts[0]) if len(parts) > 0 else 0
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        except Exception:
            return 0

    def _coords_to_dict(self, coords: Any) -> Dict[str, Any]:
        if not coords:
            return {"lat": None, "lng": None}
        if isinstance(coords, dict):
            return {"lat": coords.get("lat"), "lng": coords.get("lng")}
        return {
            "lat": getattr(coords, "lat", None),
            "lng": getattr(coords, "lng", None),
        }

    def _has_valid_coords(self, coords: Dict[str, Any]) -> bool:
        return coords.get("lat") is not None and coords.get("lng") is not None

    def _resolve_place_coords(self, name: str, city: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        fallback = fallback or {"lat": None, "lng": None}
        if not name:
            print(f"[OrchestratorAgent] resolve coords skipped: empty name, fallback={fallback}")
            return fallback

        try:
            print(f"[OrchestratorAgent] resolve coords search_poi: name={name}, city={city}")
            pois = self.amap.search_poi(name, city=city, page_size=1)
            print(f"[OrchestratorAgent] resolve coords search_poi result: {pois}")
            if pois:
                return {"lat": pois[0].get("lat"), "lng": pois[0].get("lng")}
        except Exception as e:
            print(f"[OrchestratorAgent] resolve coords search_poi error: {e}")

        try:
            print(f"[OrchestratorAgent] resolve coords geocode: name={name}, city={city}")
            geo = self.amap.geocode(name, city=city)
            print(f"[OrchestratorAgent] resolve coords geocode result: {geo}")
            if geo.get("lat") is not None and geo.get("lng") is not None:
                return {"lat": geo.get("lat"), "lng": geo.get("lng")}
        except Exception as e:
            print(f"[OrchestratorAgent] resolve coords geocode error: {e}")

        print(f"[OrchestratorAgent] resolve coords fallback used: {fallback}")
        return fallback

    def _sort_day_label(self, value: str) -> tuple[int, int]:
        import re
        match = re.search(r"(\d+)\.(\d+)", value or "")
        if not match:
            return (99, 99)
        return (int(match.group(1)), int(match.group(2)))

    def _extract_clock_only(self, value: str) -> str:
        import re
        match = re.search(r"(\d{1,2}:\d{2})", value or "")
        return match.group(1) if match else ""

    def _extract_day_label(self, value: str) -> str:
        import re
        match = re.search(r"(\d{1,2}\.\d{1,2})", value or "")
        return match.group(1) if match else ""

    def _simplify_local_transports(self, local_transports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
         simplified_local_transports: List[Dict[str, Any]] = []
         for lt in local_transports:
             simplified_lt = {
                 "from_location": lt.get("from_location"),
                 "to_location": lt.get("to_location"),
                 "sort_time": lt.get("sort_time"),
                 "sort_day_label": lt.get("sort_day_label"),
                 "selected_index": lt.get("selected_index", 0),
             }
             if "routes" in lt:
                 simplified_lt["routes"] = [
                     {
                         "type": route.get("transport_type", "driving"),
                         "distance_m": int(route.get("distance", 0)),
                         "duration_s": int(route.get("duration", 0)),
                         "steps": route.get("steps", []),
                     }
                     for route in lt.get("routes", [])
                 ]
             simplified_local_transports.append(simplified_lt)
         return simplified_local_transports

    def _remove_polylines(self, obj: Any) -> Any:
         """递归移除所有 polyline 字段以减小响应体"""
         if isinstance(obj, dict):
             return {k: self._remove_polylines(v) for k, v in obj.items() if k != 'polyline'}
         elif isinstance(obj, list):
             return [self._remove_polylines(item) for item in obj]
         return obj
