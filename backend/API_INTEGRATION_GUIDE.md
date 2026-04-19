# 风间 AI 旅行规划 - API 集成指南

## 当前状态

后端架构已完成，但目前使用**硬编码 fallback 数据**而非真实 API 调用。这是为了让系统先跑通，再逐步接入真实数据源。

## 为什么不能直接用真实 API？

### 1. 高德地图 API 限制

**问题**：高德地图 API 不直接提供城际大交通（高铁、飞机）数据。

**当前实现**：[`AMapClient.intercity_transport_candidates()`](services/provider_clients.py:153)
- 返回硬编码的高铁/飞机/大巴/顺风车候选方案
- 包含价格、时间、车次号等信息

**真实方案**：需要接入多个第三方平台
- **高铁**：12306 API（需要企业认证）
- **飞机**：携程/去哪儿/飞猪 API（需要商务合作）
- **大巴**：长途汽车联网售票系统 API
- **顺风车**：滴滴/嘀嗒出行 API

**替换步骤**：
```python
# 修改 AMapClient.intercity_transport_candidates()
def intercity_transport_candidates(self, ...):
    # 1. 调用 12306 API 获取高铁
    rail_options = self._fetch_from_12306(departure_city, destination_city, departure_time)
    
    # 2. 调用航班 API 获取飞机
    flight_options = self._fetch_flights(departure_city, destination_city, departure_time)
    
    # 3. 调用大巴 API
    bus_options = self._fetch_buses(departure_city, destination_city, departure_time)
    
    # 4. 合并结果
    return {
        "outbound": rail_options + flight_options + bus_options,
        "return": ...
    }
```

### 2. 美团 API 限制

**问题**：美团开放平台的酒店/景点/餐饮 API 需要企业认证和商务合作。

**当前实现**：
- [`MeituanClient.search_hotels()`](services/provider_clients.py:236)：返回硬编码酒店列表
- [`MeituanClient.search_attractions()`](services/provider_clients.py:277)：返回硬编码景点列表
- [`MeituanClient.search_foods()`](services/provider_clients.py:315)：返回硬编码餐饮列表

**真实方案**：
- 申请美团开放平台企业账户
- 获取 API 密钥和 token
- 调用对应的搜索接口

**替换步骤**：
```python
# 修改 MeituanClient.search_hotels()
def search_hotels(self, city: str, anchor: str, page_size: int = 5):
    if not self.is_ready():
        return []
    
    response = self.get_json(
        f"{self.base_url}/hotel/search",
        params={
            "city": city,
            "keyword": anchor,
            "limit": page_size,
        },
        headers=self._headers()
    )
    
    hotels = response.get("data", [])
    return [
        {
            "id": h["id"],
            "name": h["name"],
            "address": h["address"],
            "price": h["price"],
            "rating": h["rating"],
            "image": h.get("image_url", ""),
            "reason": h.get("description", ""),
            "source": "meituan_api",
        }
        for h in hotels
    ]
```

### 3. 高德小交通路线规划

**当前实现**：[`AMapClient.route_plan()`](services/provider_clients.py:96)
- 已实现真实调用高德驾车路线规划 API
- 返回距离、时间、费用等信息

**状态**：✅ 已可用（需要配置 `AMAP_API_KEY`）

## 配置步骤

### 1. 获取高德 API 密钥

1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册企业账户
3. 创建应用，获取 `Web 服务 API` 密钥
4. 在 `backend/.env` 中配置：

```env
AMAP_API_KEY=your_amap_api_key_here
AMAP_SECURITY_CODE=your_amap_security_code_here
```

### 2. 获取美团 API 密钥

1. 访问 [美团开放平台](https://open.meituan.com/)
2. 申请企业认证
3. 创建应用，获取 token
4. 在 `backend/.env` 中配置：

```env
MEITUAN_TOKEN=your_meituan_token_here
MEITUAN_BASE_URL=https://openapi.meituan.com
```

### 3. 获取 12306 API（可选）

目前 12306 没有官方开放 API，可选方案：
- 使用第三方聚合平台（携程、去哪儿等）
- 自建爬虫（需遵守法律法规）
- 使用开源库如 `12306-python`

## 代码替换清单

| 模块 | 文件 | 方法 | 状态 | 优先级 |
|------|------|------|------|--------|
| 高德地图 | `services/provider_clients.py` | `geocode()` | ✅ 可用 | 低 |
| 高德地图 | `services/provider_clients.py` | `search_poi()` | ✅ 可用 | 低 |
| 高德地图 | `services/provider_clients.py` | `route_plan()` | ✅ 可用 | 中 |
| 高德地图 | `services/provider_clients.py` | `transit_hubs()` | ✅ 可用 | 中 |
| 高德地图 | `services/provider_clients.py` | `intercity_transport_candidates()` | ❌ 硬编码 | **高** |
| 美团 | `services/provider_clients.py` | `search_hotels()` | ❌ 硬编码 | **高** |
| 美团 | `services/provider_clients.py` | `search_attractions()` | ❌ 硬编码 | **高** |
| 美团 | `services/provider_clients.py` | `search_foods()` | ❌ 硬编码 | **高** |

## 测试当前系统

即使没有真实 API 密钥，系统也能正常运行（使用 fallback 数据）：

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt

# 2. 启动后端
cd backend
python app.py

# 3. 前端调用 API
# POST http://localhost:5000/api/planner/generate
# 返回完整规划结果（使用硬编码数据）
```

## 下一步计划

1. **第一阶段**：完成高德 API 集成（地理编码、POI 搜索、路线规划）
2. **第二阶段**：接入 12306 或第三方航班 API
3. **第三阶段**：申请美团开放平台，集成酒店/景点/餐饮搜索
4. **第四阶段**：性能优化和缓存策略

## 常见问题

**Q: 为什么现在不直接用真实 API？**
A: 因为需要企业认证和商务合作，申请周期长。现在用硬编码 fallback 让系统先跑通，验证架构可行性。

**Q: 硬编码数据会影响最终效果吗？**
A: 不会。只要替换 `services/provider_clients.py` 中的方法实现，其他代码无需改动。

**Q: 如何快速测试真实 API？**
A: 可以先用高德 API（相对容易获取），然后逐步接入其他平台。

**Q: 有没有开源的替代方案？**
A: 可以考虑 OpenTripPlanner、GraphHopper 等开源路线规划引擎。