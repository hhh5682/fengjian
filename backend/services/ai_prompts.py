"""
AI prompt templates for structured itinerary planning.
Each agent uses standardized prompts to extract structured data from Ollama.
"""
from typing import List, Optional


class AttractionPrompts:
    """Attraction planning prompts."""

    @staticmethod
    def plan_attractions(
        destination: str,
        days: int,
        interests: List[str],
        departure_time: str,
        return_time: str,
    ) -> str:
        interests_str = "、".join(interests) if interests else "风景、文化、美食"
        return f"""请为我规划一个{destination}的{days}天旅行景点行程。

出发时间：{departure_time}
返回时间：{return_time}
兴趣爱好：{interests_str}

请按照以下JSON格式返回景点规划（必须是有效的JSON）：
{{
  "attractions": [
    {{
      "name": "景点名称",
      "address": "景点地址",
      "day": 1,
      "start_time": "09:30",
      "duration_hours": 2,
      "ticket_price": 100,
      "description": "景点描述",
      "image_url": "景点图片链接（如果有）",
      "tips": "游玩建议",
      "tags": ["风景", "拍照"]
    }}
  ]
}}

要求：
1. 景点要合理分配到各天
2. 考虑景点之间的距离和交通时间
3. 包含门票价格信息
4. 尽量提供图片链接，没有则留空字符串
5. 返回有效JSON，不要输出额外解释文字"""


class HotelPrompts:
    """Hotel recommendation prompts."""

    @staticmethod
    def recommend_hotels(
        destination: str,
        check_in_date: str,
        check_out_date: str,
        attraction_locations: List[str],
        budget: Optional[float] = None,
    ) -> str:
        attractions_str = "、".join(attraction_locations) if attraction_locations else "市中心"
        budget_str = f"预算：{budget}元/晚" if budget else "中等价位"
        return f"""请为我推荐{destination}的酒店。

入住日期：{check_in_date}
退房日期：{check_out_date}
主要景点位置：{attractions_str}
{budget_str}

请返回以下JSON格式（必须是有效的JSON）：
{{
  "hotels": [
    {{
      "name": "酒店名称",
      "address": "酒店地址",
      "price_per_night": 200,
      "rating": 4.5,
      "distance_to_attractions": "距离景点描述",
      "image_url": "酒店图片链接",
      "reason": "推荐理由",
      "amenities": ["WiFi", "早餐", "停车场"]
    }}
  ]
}}

要求：
1. 推荐3-5家酒店
2. 优先选择靠近第二天第一个景点或核心景区的位置
3. 提供酒店图片链接，没有则留空字符串
4. 说明推荐理由
5. 返回有效JSON，不要输出额外解释文字"""


class FoodPrompts:
    """Food recommendation prompts."""

    @staticmethod
    def recommend_meals(
        destination: str,
        current_location: str,
        meal_type: str,
        preferences: List[str],
        day: int,
        time: str,
    ) -> str:
        prefs_str = "、".join(preferences) if preferences else "本地特色"
        return f"""请为我推荐{destination}的{meal_type}。

当前位置：{current_location}
用餐时间：第{day}天 {time}
饮食偏好：{prefs_str}

请返回以下JSON格式（必须是有效的JSON）：
{{
  "meals": [
    {{
      "name": "餐厅名称",
      "address": "餐厅地址",
      "cuisine_type": "菜系",
      "price_per_person": 50,
      "rating": 4.5,
      "distance_from_current": "距离描述",
      "image_url": "餐厅图片链接",
      "signature_dishes": ["菜品1", "菜品2"],
      "reason": "推荐理由"
    }}
  ]
}}

要求：
1. 推荐3-5家餐厅
2. 优先选择靠近当前位置的餐厅
3. 早饭偏酒店附近，午饭偏当前景点附近，晚饭偏晚间活动附近
4. 提供餐厅图片链接，没有则留空字符串
5. 返回有效JSON，不要输出额外解释文字"""