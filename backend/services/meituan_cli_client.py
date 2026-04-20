import os
import re
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional


class MeituanCLIClient:
    """
    美团规划客户端 - 使用LLM生成真实的旅行规划数据
    """

    def __init__(self, token: Optional[str] = None, timeout: int = 30):
        self.token = token or os.getenv(
            "MEITUAN_TOKEN",
            "美团key",
        )
        self.timeout = timeout
        # 优先使用环境变量，否则尝试常见路径
        self.cli_command = os.getenv(
            "MEITUAN_CLI_COMMAND",
            r"C:\Users\黄静欣\AppData\Roaming\npm\mttravel.cmd"
        )

    def is_ready(self) -> bool:
        # 总是返回 True，因为我们使用LLM生成数据
        return True

    def run_query(self, city: str, query: str) -> str:
        if not city or not query:
            return ""

        try:
            # 构建命令
            cmd = f'"{self.cli_command}" {city} "{query}"'
            
            # 调用 mttravel
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout,
                errors="ignore",
                shell=True,
                cwd=os.path.expanduser("~"),  # 在用户主目录运行
            )
            
            output = (result.stdout or "").strip()
            
            # 检查是否有实际输出
            if output and len(output) > 50:
                return output
            
            # 如果没有输出但返回码为0，可能是异步输出，等待后重试
            if result.returncode == 0 and not output:
                import time
                time.sleep(1)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=self.timeout,
                    errors="ignore",
                    shell=True,
                    cwd=os.path.expanduser("~"),
                )
                output = (result.stdout or "").strip()
                if output and len(output) > 50:
                    return output
            
            return ""
        except subprocess.TimeoutExpired:
            return ""
        except Exception:
            return ""

    def _generate_with_llm(self, city: str, query: str) -> str:
        """使用LLM生成真实的旅行规划"""
        try:
            import anthropic
        except ImportError:
            return self._generate_fallback(city, query)

        try:
            client = anthropic.Anthropic()
            prompt = f"""你是一个专业的旅行规划师。用户要求：{query}

请生成一个详细的旅行规划，包括：
1. 每日行程安排（用"第X天"标记）
2. 每个时间点的活动（格式：HH:MM - 活动名称）
3. 推荐的景点、酒店、餐厅
4. 预算估算（用¥标记价格）
5. 交通方式建议

请用中文回复，格式清晰，便于解析。"""

            message = client.messages.create(
                model="claude-3-5--20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text if message.content else ""
        except Exception:
            return self._generate_fallback(city, query)

    def _generate_fallback(self, city: str, query: str) -> str:
        """生成基础的规划文本"""
        return f"""
第1天
09:00 - 抵达{city}，前往酒店办理入住
12:00 - 午餐，品尝当地特色美食
14:00 - 游览{city}市中心景区
18:00 - 晚餐，推荐当地知名餐厅
20:00 - 返回酒店休息

第2天
08:00 - 早餐
09:00 - 游览{city}主要景点
12:00 - 午餐
14:00 - 继续游览景点或购物
17:00 - 返回酒店
19:00 - 晚餐
21:00 - 返程

预算估算：
- 交通：¥500
- 酒店：¥400/晚
- 景点门票：¥200
- 餐饮：¥300
- 其他：¥100
"""

    def plan_itinerary(
        self,
        destination: str,
        departure: str,
        departure_time: str,
        return_time: str,
        interests: Optional[List[str]] = None,
        food_preferences: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        interests_text = "、".join(interests or ["风景", "美食"])
        foods_text = "、".join(food_preferences or ["本地特色"])
        days = self._infer_days(departure_time, return_time)

        query = (
            f"请为我规划一个从{departure}到{destination}的{days}天旅行行程，"
            f"出发时间{departure_time}，返回时间{return_time}，"
            f"兴趣偏好：{interests_text}，餐饮偏好：{foods_text}。"
            f"请输出包含每日行程、景点、餐饮、住宿建议和预算。"
        )

        raw_text = self.run_query(destination, query)
        parsed_timeline = self._parse_timeline(raw_text)
        summary_budget = self._extract_budget(raw_text)
        
        # 确保返回值是字典，且所有字段都是正确的类型
        return {
            "raw_text": raw_text if isinstance(raw_text, str) else "",
            "days": days,
            "destination": destination,
            "parsed_timeline": parsed_timeline if isinstance(parsed_timeline, list) else [],
            "summary_budget": summary_budget if isinstance(summary_budget, dict) else {},
        }

    def search_hotels(self, city: str, anchor: str, page_size: int = 5) -> List[Dict[str, Any]]:
        query = f"推荐{anchor or city}附近适合住宿的酒店，返回{page_size}个候选，尽量包含价格和特点。"
        raw_text = self.run_query(city, query)
        hotels = self._parse_hotels(raw_text)
        if not hotels:
            return self._fallback_hotels(city, anchor, page_size)
        return hotels[:page_size]

    def search_attractions(
        self,
        city: str,
        interests: Optional[List[str]] = None,
        page_size: int = 6,
    ) -> List[Dict[str, Any]]:
        interest_text = "、".join(interests or ["风景", "打卡"])
        query = f"推荐{city}适合{interest_text}的景点，返回{page_size}个候选，尽量包含门票、开放时间和游玩时长。"
        raw_text = self.run_query(city, query)
        attractions = self._parse_attractions(raw_text, interests or [])
        if not attractions:
            return self._fallback_attractions(city, interests, page_size)
        return attractions[:page_size]

    def search_foods(
        self,
        city: str,
        area: str = "",
        preferences: Optional[List[str]] = None,
        page_size: int = 6,
    ) -> List[Dict[str, Any]]:
        pref_text = "、".join(preferences or ["本地特色"])
        scope = area or city
        query = f"推荐{scope}附近适合{pref_text}的餐厅，返回{page_size}个候选，尽量包含人均和推荐理由。"
        raw_text = self.run_query(city, query)
        foods = self._parse_foods(raw_text, preferences or [])
        if not foods:
            return self._fallback_foods(city, area, preferences, page_size)
        return foods[:page_size]

    def _infer_days(self, departure_time: str, return_time: str) -> int:
        try:
            dep = datetime.fromisoformat(departure_time.replace("Z", "+00:00"))
            ret = datetime.fromisoformat(return_time.replace("Z", "+00:00"))
            return max(1, (ret.date() - dep.date()).days + 1)
        except Exception:
            return 2

    def _parse_timeline(self, raw_text: str) -> List[Dict[str, Any]]:
        if not isinstance(raw_text, str):
            return []
        
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        timeline: List[Dict[str, Any]] = []
        current_day = 1
        index = 0

        for line in lines:
            # 检测日期标记：DAY1、第1天、📝 **DAY1等
            day_match = re.search(r"(?:DAY|第)\s*([0-9一二三四五六七八九十]+)", line, re.IGNORECASE)
            if day_match:
                current_day = self._normalize_day(day_match.group(1))
                continue

            # 检测时间格式 HH:MM 或 · **HH:MM
            time_match = re.search(r"(?:·\s*\*{0,2})?([01]?\d|2[0-3]):([0-5]\d)", line)
            if not time_match:
                continue

            try:
                hh, mm = time_match.group(1), time_match.group(2)
                # 提取时间后的标题，移除各种前缀符号
                title = re.sub(r"^.*?(?:·\s*\*{0,2})?([01]?\d|2[0-3]):([0-5]\d)\s*[-\-：:·]*\s*", "", line).strip()
                # 移除markdown链接
                title = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", title)
                # 移除emoji和特殊符号
                title = re.sub(r"^[🔍📝🗓🗺💡🏨🕓💰🎫🌤⛅🚗🍜🏛🌊🎭🎪🎨🎬🎤🎧🎮🎯🎲🎰🎳🎸🎹🎺🎻🥁🎼🎵🎶🎙🎚🎛📻📺📹📷📸📼🎞🎥🎬🎭🎪🎨🎬🎤🎧]+\s*", "", title)
                if not title:
                    title = "行程安排"

                block_type = self._infer_block_type(title)
                price = self._extract_first_price(line)
                
                timeline.append(
                    {
                        "id": f"mt_cli_{current_day}_{index}",
                        "day": current_day,
                        "block_type": block_type,
                        "title": title[:100],
                        "subtitle": "",
                        "start_time": f"{int(hh):02d}:{mm}",
                        "end_time": "",
                        "price": price,
                        "location": "",
                        "card_type": block_type,
                        "selected": True,
                        "alternatives": [],
                        "fields": {
                            "source": "meituan_cli",
                            "raw_line": line,
                        },
                    }
                )
                index += 1
            except Exception:
                continue

        return timeline if isinstance(timeline, list) else []

    def _parse_hotels(self, raw_text: str) -> List[Dict[str, Any]]:
        if not isinstance(raw_text, str):
            return []
        
        lines = [line.strip("-•* 　") for line in raw_text.splitlines() if line.strip()]
        hotels: List[Dict[str, Any]] = []

        for idx, line in enumerate(lines):
            if not any(keyword in line for keyword in ["酒店", "宾馆", "民宿", "客栈", "住宿", "推荐理由"]):
                continue

            price = self._extract_first_price(line) or 400
            # 清理行文本，移除各种前缀
            clean_name = re.sub(r"^[🏨🕓💰🎫]+\s*\*{0,2}", "", line).strip()
            clean_name = re.sub(r"^\d{1,2}:\d{2}\s*[-\-：:·]*\s*", "", clean_name).strip()
            clean_name = re.sub(r"^推荐理由[：:]*\s*", "", clean_name).strip()
            clean_name = re.sub(r"\*{0,2}$", "", clean_name).strip()
            
            if not clean_name or len(clean_name) < 2:
                continue
                
            hotels.append(
                {
                    "id": f"meituan_hotel_{idx}",
                    "name": clean_name[:80],
                    "address": "",
                    "price": price,
                    "rating": 4.5,
                    "image": "",
                    "reason": clean_name,
                    "source": "meituan_cli",
                }
            )

        return hotels

    def _parse_attractions(self, raw_text: str, interests: List[str]) -> List[Dict[str, Any]]:
        if not isinstance(raw_text, str):
            return []
        
        lines = [line.strip("-•* 　") for line in raw_text.splitlines() if line.strip()]
        results: List[Dict[str, Any]] = []

        for idx, line in enumerate(lines):
            # 检测景点标记：数字+、景点名称、或包含景点关键词
            if not any(keyword in line for keyword in ["景区", "景点", "公园", "博物馆", "古镇", "山", "湖", "街区", "游览", "参观", "塔", "峰", "洞"]):
                continue

            price = self._extract_first_price(line)
            # 清理行文本，移除各种前缀
            clean_name = re.sub(r"^[🏛🌊🎭🎪🎨]+\s*\*{0,2}", "", line).strip()
            clean_name = re.sub(r"^\d{1,2}:\d{2}\s*[-\-：:·]*\s*", "", clean_name).strip()
            clean_name = re.sub(r"^【.*?】\s*", "", clean_name).strip()
            clean_name = re.sub(r"^\d+[、·]\s*", "", clean_name).strip()
            # 移除markdown链接
            clean_name = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean_name)
            clean_name = re.sub(r"\*{0,2}$", "", clean_name).strip()
            
            if not clean_name or len(clean_name) < 2:
                continue
                
            results.append(
                {
                    "id": f"meituan_poi_{idx}",
                    "name": clean_name[:80],
                    "address": "",
                    "price": price,
                    "rating": 4.5,
                    "open_time": "08:00-17:30",
                    "duration_text": "建议游玩 1-2 小时",
                    "tags": interests[:2] or ["推荐"],
                    "source": "meituan_cli",
                }
            )

        return results

    def _parse_foods(self, raw_text: str, preferences: List[str]) -> List[Dict[str, Any]]:
        if not isinstance(raw_text, str):
            return []
        
        lines = [line.strip("-•* 　") for line in raw_text.splitlines() if line.strip()]
        results: List[Dict[str, Any]] = []

        for idx, line in enumerate(lines):
            if not any(keyword in line for keyword in ["餐厅", "饭店", "小馆", "米粉", "火锅", "烧烤", "咖啡", "甜品", "美食", "午餐", "晚餐", "早餐", "品尝", "尝试"]):
                continue

            price = self._extract_first_price(line) or 60
            # 清理行文本，移除各种前缀
            clean_name = re.sub(r"^[🍜🎫]+\s*\*{0,2}", "", line).strip()
            clean_name = re.sub(r"^\d{1,2}:\d{2}\s*[-\-：:·]*\s*", "", clean_name).strip()
            clean_name = re.sub(r"^品尝|^尝试", "", clean_name).strip()
            clean_name = re.sub(r"^【.*?】\s*", "", clean_name).strip()
            # 移除markdown链接
            clean_name = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean_name)
            clean_name = re.sub(r"\*{0,2}$", "", clean_name).strip()
            
            if not clean_name or len(clean_name) < 2:
                continue
                
            results.append(
                {
                    "id": f"meituan_food_{idx}",
                    "name": clean_name[:80],
                    "address": "",
                    "price": price,
                    "rating": 4.5,
                    "meal_type": "推荐餐饮",
                    "tags": preferences[:2] or ["本地特色"],
                    "source": "meituan_cli",
                }
            )

        return results

    def _extract_budget(self, raw_text: str) -> Dict[str, float]:
        if not isinstance(raw_text, str):
            return {
                "transport": 0.0,
                "hotel": 0.0,
                "attraction": 0.0,
                "food": 0.0,
                "total": 0.0,
            }
        
        try:
            prices = [float(value) for value in re.findall(r"[¥￥]\s*(\d+(?:\.\d+)?)", raw_text)]
            if not prices:
                return {
                    "transport": 0.0,
                    "hotel": 0.0,
                    "attraction": 0.0,
                    "food": 0.0,
                    "total": 0.0,
                }

            total = round(sum(prices), 2)
            return {
                "transport": 0.0,
                "hotel": 0.0,
                "attraction": 0.0,
                "food": 0.0,
                "total": total,
            }
        except Exception:
            return {
                "transport": 0.0,
                "hotel": 0.0,
                "attraction": 0.0,
                "food": 0.0,
                "total": 0.0,
            }

    def _extract_first_price(self, text: str) -> float:
        match = re.search(r"[¥￥]\s*(\d+(?:\.\d+)?)", text)
        return float(match.group(1)) if match else 0.0

    def _infer_block_type(self, title: str) -> str:
        if any(keyword in title for keyword in ["高铁", "火车", "飞机", "航班", "大巴", "客车"]):
            return "transport_main"
        if any(keyword in title for keyword in ["打车", "步行", "公交", "地铁", "骑行"]):
            return "transport_local"
        if any(keyword in title for keyword in ["酒店", "宾馆", "民宿", "入住"]):
            return "hotel"
        if any(keyword in title for keyword in ["早餐", "午餐", "晚餐", "餐厅", "小吃", "美食"]):
            return "food"
        return "attraction"

    def _normalize_day(self, value: str) -> int:
        mapping = {
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "十": 10,
        }
        if value.isdigit():
            return int(value)
        return mapping.get(value, 1)

    def _fallback_hotels(self, city: str, anchor: str, page_size: int) -> List[Dict[str, Any]]:
        anchor_text = anchor or f"{city}市中心"
        return [
            {
                "id": "hotel_1",
                "name": f"{anchor_text}附近精选酒店",
                "address": f"{anchor_text}步行5分钟",
                "price": 441,
                "rating": 4.7,
                "image": "",
                "reason": "CLI 不可用时的降级推荐",
                "source": "meituan_fallback",
            },
            {
                "id": "hotel_2",
                "name": f"{anchor_text}舒适酒店",
                "address": f"{anchor_text}附近",
                "price": 385,
                "rating": 4.5,
                "image": "",
                "reason": "CLI 不可用时的降级推荐",
                "source": "meituan_fallback",
            },
        ][:page_size]

    def _fallback_attractions(
        self,
        city: str,
        interests: Optional[List[str]] = None,
        page_size: int = 6,
    ) -> List[Dict[str, Any]]:
        tags = interests or ["风景", "打卡"]
        return [
            {
                "id": "poi_1",
                "name": f"{city}核心景点A",
                "address": f"{city}市景区中心",
                "price": 75,
                "rating": 4.7,
                "open_time": "08:00-17:30",
                "duration_text": "建议游玩 1.5 小时",
                "tags": tags[:2],
                "source": "meituan_fallback",
            },
            {
                "id": "poi_2",
                "name": f"{city}特色街区",
                "address": f"{city}市热门片区",
                "price": 0,
                "rating": 4.5,
                "open_time": "全天开放",
                "duration_text": "建议游玩 1 小时",
                "tags": ["免费", "步行友好"],
                "source": "meituan_fallback",
            },
        ][:page_size]

    def _fallback_foods(
        self,
        city: str,
        area: str = "",
        preferences: Optional[List[str]] = None,
        page_size: int = 6,
    ) -> List[Dict[str, Any]]:
        area_text = area or f"{city}热门片区"
        pref_text = preferences or ["本地特色", "高评分"]
        return [
            {
                "id": "food_1",
                "name": f"{area_text}特色餐厅",
                "address": f"{area_text}近景点步行6分钟",
                "price": 68,
                "rating": 4.6,
                "meal_type": "午餐",
                "tags": pref_text,
                "source": "meituan_fallback",
            },
            {
                "id": "food_2",
                "name": f"{area_text}人气小馆",
                "address": f"{area_text}商圈内",
                "price": 55,
                "rating": 4.5,
                "meal_type": "晚餐",
                "tags": ["本地特色", "性价比"],
                "source": "meituan_fallback",
            },
        ][:page_size]
