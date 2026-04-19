"""
Hotel Agent
按照固定提示词询问 AI，并将酒店推荐解析为结构化字段。
"""
from __future__ import annotations

import re
from typing import List, Optional

from models.trip_models import HotelOption, HotelPlan
from services.doubao_client import DoubaoClient


class HotelAgent:
    def __init__(self, ai_client: Optional[DoubaoClient] = None) -> None:
        self.name = "住宿规划员"
        self.ai_client = ai_client or DoubaoClient()

    def plan(
        self,
        destination: str,
        check_in_date: str,
        check_out_date: str,
        anchor: Optional[str] = None,
        attraction_locations: Optional[List[str]] = None,
    ) -> HotelPlan:
        """
        基于大交通日期窗口返回多酒店可选结构。
        """
        prompt = self._build_prompt(destination, check_in_date, check_out_date)
        response_text = self.ai_client.query(prompt)
        return self._parse_hotels(response_text)

    def _build_prompt(self, destination: str, check_in_date: str, check_out_date: str) -> str:
        return f"""去{destination}游玩，入住日期{check_in_date}，离店日期{check_out_date}，有什么推荐的酒店，按照下面的格式输出：
1.酒店名称：XX酒店 临近景点/地标：XX景点 预估价格：200r/晚
2.酒店名称：XX酒店 临近景点/地标：XX景点 预估价格：250r/晚
3.酒店名称：XX酒店 临近景点/地标：XX景点 预估价格：300r/晚

严格按照这个格式输出，不要输出其他解释文字。"""

    def _parse_hotels(self, text: str) -> HotelPlan:
        pattern = re.compile(
            r"(?:^|\n)\s*\d+\.\s*酒店名称：(?P<hotel_name>.*?)\s+"
            r"临近景点/地标：(?P<nearby_landmark>.*?)\s+"
            r"预估价格：(?P<price>\d+(?:\.\d+)?)\s*[rR元]?(?:/晚)?",
            re.MULTILINE,
        )

        options: List[HotelOption] = []
        for match in pattern.finditer(text):
            options.append(
                HotelOption(
                    hotel_name=match.group("hotel_name").strip(),
                    nearby_landmark=match.group("nearby_landmark").strip(),
                    estimated_price=float(match.group("price")),
                )
            )

        return HotelPlan(options=options, selected_index=0)