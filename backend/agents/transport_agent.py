"""
Transport Agent
按照固定提示词询问 AI，并将去程/返程的大交通方案解析为结构化字段。
"""
from __future__ import annotations

import re
from typing import List, Optional

from models.trip_models import TransportOption, TransportPlan
from services.doubao_client import DoubaoClient


class TransportAgent:
    def __init__(self, ai_client: Optional[DoubaoClient] = None) -> None:
        self.name = "大交通规划员"
        self.ai_client = ai_client or DoubaoClient()

    def plan(
        self,
        departure: str,
        destination: str,
        departure_time: str,
        return_time: str,
    ) -> dict:
        """
        返回结构：
        {
            "outbound": TransportPlan,
            "return": TransportPlan
        }
        """
        prompt = self._build_prompt(
            departure=departure,
            destination=destination,
            departure_time=departure_time,
            return_time=return_time,
        )

        response_text = self.ai_client.query(prompt)
        return self._parse_transport_response(response_text)

    def _build_prompt(
        self,
        departure: str,
        destination: str,
        departure_time: str,
        return_time: str,
    ) -> str:
        departure_date_text, departure_clock_text = self._format_datetime_text(departure_time, is_departure=True)
        return_date_text, return_clock_text = self._format_datetime_text(return_time, is_departure=False)

        return f"""你是大交通规划 agent。
请回答：{departure_date_text} {departure_clock_text}从{departure}出发去{destination}，以及{return_date_text} {return_clock_text}从{destination}返回{departure}，可以怎么前往（只是大交通，不考虑从起始点到交通站的事，保证去程起始时间大于{departure_date_text} {departure_clock_text}，返程起始时间大于{return_date_text} {return_clock_text}）。

严格按照下面格式输出，不要输出任何解释，不要输出额外文字：

去程：
1.交通方式：高铁/飞机/火车/大巴 交通班次：XXX 起始点：xxx 终点：xxx 起始时间：4.18 18:00 到达时间：4.18 20:00 所需时间：xxx 预估价格：200r
2.交通方式：高铁/飞机/火车/大巴 交通班次：XXX 起始点：xxx 终点：xxx 起始时间：4.18 18:00 到达时间：4.18 20:00 所需时间：xxx 预估价格：200r

返程：
1.交通方式：高铁/飞机/火车/大巴 交通班次：XXX 起始点：xxx 终点：xxx 起始时间：4.20 10:00 到达时间：4.20 14:00 所需时间：xxx 预估价格：200r
2.交通方式：高铁/飞机/火车/大巴 交通班次：XXX 起始点：xxx 终点：xxx 起始时间：4.20 10:00 到达时间：4.20 14:00 所需时间：xxx 预估价格：200r"""

    def _parse_transport_response(self, text: str) -> dict:
        outbound_text = self._extract_section(text, "去程：", "返程：")
        return_text = self._extract_section(text, "返程：", None)

        outbound_options = self._parse_options(outbound_text)
        return_options = self._parse_options(return_text)

        return {
            "outbound": TransportPlan(label="去程", options=outbound_options, selected_index=0),
            "return": TransportPlan(label="返程", options=return_options, selected_index=0),
            "raw_text": text,
        }

    def _parse_options(self, text: str) -> List[TransportOption]:
        pattern = re.compile(
            r"(?:^|\n)\s*\d+\.\s*交通方式：(?P<transport_type>.*?)\s+"
            r"交通班次：(?P<trip_number>.*?)\s+"
            r"起始点：(?P<departure_station>.*?)\s+"
            r"终点：(?P<arrival_station>.*?)\s+"
            r"起始时间：(?P<departure_time>.*?)\s+"
            r"到达时间：(?P<arrival_time>.*?)\s+"
            r"所需时间：(?P<duration>.*?)\s+"
            r"预估价格：(?P<price>[0-9]+(?:\.[0-9]+)?)\s*[rR元]?",
            re.MULTILINE,
        )

        options: List[TransportOption] = []
        for match in pattern.finditer(text):
            options.append(
                TransportOption(
                    transport_type=match.group("transport_type").strip(),
                    trip_number=match.group("trip_number").strip(),
                    departure_station=match.group("departure_station").strip(),
                    arrival_station=match.group("arrival_station").strip(),
                    departure_time=match.group("departure_time").strip(),
                    arrival_time=match.group("arrival_time").strip(),
                    duration=match.group("duration").strip(),
                    estimated_price=float(match.group("price")),
                )
            )
        return options

    def _extract_section(self, text: str, start_marker: str, end_marker: Optional[str]) -> str:
        if start_marker not in text:
            return ""
        start_index = text.index(start_marker) + len(start_marker)
        if end_marker and end_marker in text[start_index:]:
            end_index = text.index(end_marker, start_index)
            return text[start_index:end_index].strip()
        return text[start_index:].strip()

    def _format_datetime_text(self, value: str, is_departure: bool) -> tuple[str, str]:
        date_part = value.split("T")[0] if "T" in value else value.split(" ")[0]
        time_part = "09:00"
        if "T" in value:
            time_part = value.split("T")[1][:5]
        elif " " in value and ":" in value:
            time_part = value.split(" ")[1][:5]

        year, month, day = date_part.split("-")
        day_text = f"{int(month)}.{int(day)}"
        hour = int(time_part.split(":")[0])

        if hour < 12:
            period = "早上"
        elif hour < 18:
            period = "下午"
        else:
            period = "晚上"

        if is_departure:
            return day_text, f"{period}{time_part}"
        return day_text, f"{period}{time_part}"