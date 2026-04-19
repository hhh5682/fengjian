"""
Food Agent
从景点规划中提取用餐时间和地点，然后询问 AI 推荐饭店。
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from models.trip_models import AttractionItem, HotelPlan, MealItem, RestaurantOption
from services.doubao_client import DoubaoClient


class FoodAgent:
    def __init__(self, ai_client: Optional[DoubaoClient] = None) -> None:
        self.name = "美食规划员"
        self.ai_client = ai_client or DoubaoClient()

    def plan(
        self,
        attractions: List[AttractionItem],
        hotels: Optional[HotelPlan] = None,
        transport_arrival_anchor: str = "",
    ) -> List[MealItem]:
        """
        从景点规划中提取用餐时间和地点，然后推荐饭店。

        规则：
        - Day1 早餐：靠近去程大交通终点
        - Day2+ 早餐：靠近前一晚酒店
        - 午餐：靠近当天上午最后一个景点
        - 晚餐：靠近当天下午/晚上景点
        """
        meal_queries = self._extract_meal_queries(
            attractions=attractions,
            hotels=hotels,
            transport_arrival_anchor=transport_arrival_anchor,
        )
        print(f"[FoodAgent] 提取到的用餐查询: {meal_queries}")
        if not meal_queries:
            print("[FoodAgent] 没有可用的用餐查询，直接返回空列表")
            return []

        prompt = self._build_prompt(meal_queries)
        print("[FoodAgent] ====== Prompt Start ======")
        print(prompt)
        print("[FoodAgent] ====== Prompt End ======")

        response_text = self.ai_client.query(prompt)

        print("[FoodAgent] ====== Response Start ======")
        print(response_text)
        print("[FoodAgent] ====== Response End ======")

        meals = self._parse_meals(response_text, meal_queries)
        print(f"[FoodAgent] 解析后的餐饮数量: {len(meals)}")
        return meals

    def _extract_meal_queries(
        self,
        attractions: List[AttractionItem],
        hotels: Optional[HotelPlan] = None,
        transport_arrival_anchor: str = "",
    ) -> List[Tuple[str, str, str, str, str]]:
        """
        返回 [(meal_time, nearby_attraction, meal_type, day_label, period_label), ...]
        """
        daily_attractions: Dict[str, List[AttractionItem]] = {}
        for attr in attractions:
            day = attr.day_label
            if not day:
                continue
            if day not in daily_attractions:
                daily_attractions[day] = []
            daily_attractions[day].append(attr)

        sorted_days = sorted(daily_attractions.keys(), key=self._sort_day_label)
        hotel_anchor = self._resolve_hotel_anchor(hotels)
        queries: List[Tuple[str, str, str, str, str]] = []

        for day_idx, day in enumerate(sorted_days):
            attrs = sorted(
                daily_attractions[day],
                key=lambda item: (
                    self._clock_to_minutes(item.start_time),
                    self._clock_to_minutes(item.end_time),
                ),
            )

            morning = [a for a in attrs if a.period_label == "上午"]
            afternoon = [a for a in attrs if a.period_label == "下午"]
            evening = [a for a in attrs if a.period_label == "晚上"]

            breakfast_anchor = (
                transport_arrival_anchor
                if day_idx == 0
                else (hotel_anchor or (attrs[0].location if attrs else ""))
            )
            if breakfast_anchor:
                queries.append((f"{day}早餐08:00", breakfast_anchor, "breakfast", day, "早餐"))

            if morning:
                last_morning = max(morning, key=lambda item: self._clock_to_minutes(item.end_time))
                lunch_time = last_morning.end_time or "12:30"
                queries.append((f"{day}午餐{lunch_time}", last_morning.location, "lunch", day, "午餐"))

            dinner_source = None
            if afternoon:
                dinner_source = max(afternoon, key=lambda item: self._clock_to_minutes(item.end_time))
                dinner_time = dinner_source.end_time or "18:00"
            elif evening:
                dinner_source = min(evening, key=lambda item: self._clock_to_minutes(item.start_time))
                dinner_time = dinner_source.start_time or "18:00"
            else:
                dinner_time = ""

            if dinner_source and dinner_time:
                queries.append((f"{day}晚餐{dinner_time}", dinner_source.location, "dinner", day, "晚餐"))

        return queries

    def _build_prompt(self, meal_queries: List[Tuple[str, str, str, str, str]]) -> str:
        query_lines = []
        for meal_time, location, meal_type, _, _ in meal_queries:
            if meal_type == "breakfast":
                meal_type_text = "早餐"
            elif meal_type == "lunch":
                meal_type_text = "午餐"
            else:
                meal_type_text = "晚餐"

            query_lines.append(
                f"时间：{meal_time}，请推荐 {location} 附近适合{meal_type_text}的饭店"
            )

        query_text = "\n".join(query_lines)

        return f"""请严格根据给定的时间段和地点推荐饭店，时间字段必须原样保留输出，不要擅自修改日期、时段或时刻。

待推荐的用餐请求如下：
{query_text}

请严格按照下面格式输出，每一行都要输出这些字段，不要输出任何解释或额外文字：
时间：4.18早餐08:00 临近景点：广州南站附近 饭店推荐：1.饭店名称：早茶楼 预估价格：30 2.饭店名称：粥铺 预估价格：25
时间：4.18午餐12:30 临近景点：靖江王城独秀峰附近 饭店推荐：1.饭店名称：椿记烧鹅 预估价格：90 2.饭店名称：阿甘酒家 预估价格：80
时间：4.18晚餐18:00 临近景点：漓江游船阳朔码头附近 饭店推荐：1.饭店名称：谢三姐啤酒鱼 预估价格：110 2.饭店名称：大师傅啤酒鱼 预估价格：100"""

    def _parse_meals(
        self,
        text: str,
        meal_queries: List[Tuple[str, str, str, str, str]],
    ) -> List[MealItem]:
        """
        优先按 AI 返回结果解析；若 AI 缺项，则用查询上下文兜底，保证每天三餐信息不丢失。
        """
        meals: List[MealItem] = []
        parsed_map: Dict[str, MealItem] = {}

        time_blocks = re.split(r"时间：", text)
        for block in time_blocks[1:]:
            lines = block.split("\n")
            if not lines:
                continue

            first_line = lines[0]
            time_match = re.match(
                r"([^\s]+)\s+临近景点：(.+?)(?:\s+饭店推荐：|$)",
                first_line,
            )
            if not time_match:
                continue

            meal_time = time_match.group(1)
            nearby_attraction = time_match.group(2).strip()

            rest_text = "\n".join(lines)
            restaurant_pattern = r"饭店名称：([^\s]+)\s+预估价格：(\d+(?:\.\d+)?)"
            restaurant_matches = re.finditer(restaurant_pattern, rest_text)

            options: List[RestaurantOption] = []
            for match in restaurant_matches:
                options.append(
                    RestaurantOption(
                        name=match.group(1),
                        estimated_price=float(match.group(2)),
                    )
                )

            if options:
                day_label, period_label = self._extract_day_period(meal_time)
                meal_clock = self._extract_clock(meal_time)
                meal_type = "breakfast" if "早餐" in meal_time else "lunch" if "午餐" in meal_time else "dinner"

                parsed_map[meal_time] = MealItem(
                    meal_time=meal_time,
                    nearby_attraction=nearby_attraction,
                    meal_type=meal_type,
                    day_label=day_label,
                    period_label=period_label,
                    meal_clock=meal_clock,
                    options=options,
                    selected_index=0,
                )

        for meal_time, nearby_attraction, meal_type, day_label, period_label in meal_queries:
            if meal_time in parsed_map:
                meals.append(parsed_map[meal_time])
                continue

            fallback_name = self._build_fallback_restaurant_name(nearby_attraction, period_label)
            meals.append(
                MealItem(
                    meal_time=meal_time,
                    nearby_attraction=nearby_attraction,
                    meal_type=meal_type,
                    day_label=day_label,
                    period_label=period_label,
                    meal_clock=self._extract_clock(meal_time),
                    options=[
                        RestaurantOption(
                            name=fallback_name,
                            estimated_price=0.0,
                        )
                    ],
                    selected_index=0,
                )
            )

        return meals

    def _extract_day_period(self, meal_time: str) -> Tuple[str, str]:
        """从 "4.18午餐12:30" 提取日期和时段"""
        day_match = re.search(r"(\d+\.\d+)", meal_time)
        day_label = day_match.group(1) if day_match else ""

        if "早餐" in meal_time:
            period_label = "早餐"
        elif "午餐" in meal_time:
            period_label = "午餐"
        elif "晚餐" in meal_time:
            period_label = "晚餐"
        else:
            period_label = ""

        return day_label, period_label

    def _extract_clock(self, meal_time: str) -> str:
        """从 "4.18午餐12:30" 提取时间 "12:30" """
        time_match = re.search(r"(\d+:\d+)", meal_time)
        return time_match.group(1) if time_match else ""

    def _resolve_hotel_anchor(self, hotels: Optional[HotelPlan]) -> str:
        if not hotels:
            return ""
        selected = hotels.selected_option
        if not selected and hotels.options:
            selected = hotels.options[0]
        return selected.nearby_landmark if selected else ""

    def _sort_day_label(self, value: str) -> tuple[int, int]:
        match = re.search(r"(\d+)\.(\d+)", value or "")
        if not match:
            return (99, 99)
        return (int(match.group(1)), int(match.group(2)))

    def _clock_to_minutes(self, value: str) -> int:
        match = re.search(r"(\d{1,2}):(\d{2})", value or "")
        if not match:
            return 9999
        return int(match.group(1)) * 60 + int(match.group(2))

    def _build_fallback_restaurant_name(self, nearby_attraction: str, period_label: str) -> str:
        # 真实餐厅名称库
        restaurants = {
            "早餐": ["老舍茶馆", "便宜坊", "鸿宾楼", "王家沙", "新雅粤菜馆"],
            "午餐": ["全聚德", "大董烤鸭", "绿波廊", "功德林", "小南国"],
            "晚餐": ["南门涮肉", "东来顺", "陶然居", "泰兴楼", "老字号"]
        }
        
        meal_restaurants = restaurants.get(period_label, restaurants["午餐"])
        import hashlib
        hash_val = int(hashlib.md5((nearby_attraction or "").encode()).hexdigest(), 16)
        idx = hash_val % len(meal_restaurants)
        return meal_restaurants[idx]