"""
Attraction Agent
按照固定提示词询问 AI，并将景点规划解析为结构化字段。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from models.trip_models import AttractionItem
from services.doubao_client import DoubaoClient


class AttractionAgent:
    def __init__(self, ai_client: Optional[DoubaoClient] = None) -> None:
        self.name = "景点规划员"
        self.ai_client = ai_client or DoubaoClient()

    def plan(
        self,
        destination: str,
        arrival_date: str,
        arrival_time: str,
        departure_date: str,
        departure_time: str,
    ) -> List[AttractionItem]:
        """
        基于大交通时间窗口返回景点列表，每个景点包含：
        - play_time: "4.18上午 9:30-12:00"
        - location: "象鼻山"
        - opening_hours: "8:00-18:00"
        - estimated_price_text: "免费" 或 "100元"
        """
        prompt = self._build_prompt(
            arrival_date=arrival_date,
            arrival_time=arrival_time,
            arrival_station=destination,
            departure_date=departure_date,
            departure_time=departure_time,
        )

        response_text = self.ai_client.query(prompt)
        return self._parse_attractions(response_text)

    def _build_prompt(
        self,
        arrival_date: str,
        arrival_time: str,
        arrival_station: str,
        departure_date: str,
        departure_time: str,
    ) -> str:
        return f"""我将在{arrival_date}号{arrival_time}到达{arrival_station}，{departure_date}号早上{departure_time}从{arrival_station}离开，帮我规划景点行程。

严格按照下面格式输出，每一行都要输出这些字段，不要输出其他的，不要输出任何解释：
游玩时间：4.18上午09:30-12:00 景点地点：象鼻山 开放时间：08:00-18:00 预估价格：免费
游玩时间：4.18下午14:30-17:30 景点地点：漓江游船 开放时间：09:00-14:00 预估价格：215元
游玩时间：4.19上午09:00-11:00 景点地点：阳朔西街 开放时间：全天 预估价格：免费"""

    def _parse_attractions(self, text: str) -> List[AttractionItem]:
        pattern = re.compile(
            r"游玩时间：(?P<play_time>.*?)\s+"
            r"景点地点：(?P<location>.*?)\s+"
            r"开放时间：(?P<opening_hours>.*?)\s+"
            r"预估价格：(?P<price>.*?)(?=\n|$)",
            re.MULTILINE,
        )

        attractions: List[AttractionItem] = []
        for match in pattern.finditer(text):
            play_time = match.group("play_time").strip()
            location = match.group("location").strip()
            opening_hours = match.group("opening_hours").strip()
            price_text = match.group("price").strip()

            day_label, period_label, start_time, end_time = self._parse_play_time(play_time)

            price_value = self._parse_price(price_text)

            attractions.append(
                AttractionItem(
                    play_time=play_time,
                    location=location,
                    opening_hours=opening_hours,
                    estimated_price_text=price_text,
                    day_label=day_label,
                    period_label=period_label,
                    start_time=start_time,
                    end_time=end_time,
                    estimated_price_value=price_value,
                )
            )

        return attractions

    def _parse_play_time(self, play_time: str) -> tuple[str, str, str, str]:
        """
        从 "4.18上午09:30-12:00" 提取：
        - day_label: "4.18"
        - period_label: "上午"
        - start_time: "09:30"
        - end_time: "12:00"
        """
        day_match = re.search(r"(\d+\.\d+)", play_time)
        day_label = day_match.group(1) if day_match else ""

        period_match = re.search(r"(上午|下午|晚上)", play_time)
        period_label = period_match.group(1) if period_match else ""

        time_match = re.search(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", play_time)
        if time_match:
          start_hour = time_match.group(1).zfill(2)
          start_min = time_match.group(2)
          end_hour = time_match.group(3).zfill(2)
          end_min = time_match.group(4)
          start_time = f"{start_hour}:{start_min}"
          end_time = f"{end_hour}:{end_min}"
        else:
          start_time = ""
          end_time = ""

        return day_label, period_label, start_time, end_time

    def _parse_price(self, price_text: str) -> float:
        """从 "免费" 或 "100元" 提取数值"""
        if "免费" in price_text:
            return 0.0
        match = re.search(r"(\d+(?:\.\d+)?)", price_text)
        return float(match.group(1)) if match else 0.0
