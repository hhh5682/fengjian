# 小交通规划功能指南

## 概述

小交通规划功能负责规划行程中的本地交通路线，包括：
1. **初始小交通**：从用户起始点到大交通起始点（如机场、火车站）
2. **项目间小交通**：行程中相邻卡片之间的路线（如酒店→早餐→景点→午餐等）

## 架构

### 后端组件

#### 1. LocalTransportAgent (`backend/agents/local_transport_agent.py`)
负责小交通路线规划的核心逻辑。

**主要方法：**
- `plan_initial_transport()`：规划初始小交通
- `plan_between_items()`：规划项目间小交通
- `_get_route()`：从高德API获取路线

**支持的交通方式：**
- `driving`：驾车/出租车
- `transit`：公交
- `walking`：步行

#### 2. OrchestratorAgent 更新
在主编排Agent中集成小交通规划：
- 初始化 `LocalTransportAgent`
- 在规划流程中调用小交通规划方法
- 将结果添加到 `StructuredTripPlan`

### 前端组件

#### LocalTransportCard (`src/components/LocalTransportCard.jsx`)
展示小交通路线的卡片组件。

**功能：**
- 显示起点→终点
- 提供多种交通方式选择
- 显示距离、耗时、预估费用
- 展开查看详细路线步骤
- 支持交通方式切换

## 数据流

### 1. 初始小交通流程

```
用户输入 (起始点)
    ↓
地理编码 (获取坐标)
    ↓
大交通规划 (获取大交通起始点)
    ↓
地理编码 (获取大交通起始点坐标)
    ↓
小交通规划 (调用高德API)
    ↓
返回多种交通方式的路线
```

### 2. 项目间小交通流程

```
构建项目列表 (酒店、景点、餐厅等)
    ↓
对所有项目地理编码
    ↓
遍历相邻项目对
    ↓
为每对项目规划小交通
    ↓
返回所有项目间的路线
```

## 数据模型

### LocalTransportRoute
```python
@dataclass
class LocalTransportRoute:
    from_location: Dict[str, Any]  # 起点信息
    to_location: Dict[str, Any]    # 终点信息
    routes: List[Dict[str, Any]]   # 多种交通方式的路线
    selected_index: int = 0        # 选中的路线索引
```

### 路线数据结构
```python
{
    "type": "driving|transit|walking",
    "distance_m": 1000,           # 距离（米）
    "duration_s": 600,            # 耗时（秒）
    "polyline": "...",            # 路线多边形
    "steps": [                    # 路线步骤
        {
            "instruction": "向北行驶100米"
        }
    ],
    "taxi_cost": 25.5             # 预估费用（仅驾车）
}
```

## 高德API集成

### 必需的API

1. **地理编码 API** (`/v3/geocode/geo`)
   - 将地址转换为坐标

2. **驾车路线规划 API** (`/v3/direction/driving`)
   - 获取驾车路线

3. **公交路线规划 API** (`/v3/direction/transit`)
   - 获取公交路线

4. **步行路线规划 API** (`/v3/direction/walking`)
   - 获取步行路线

### 环境配置

在 `backend/.env` 中配置：
```
AMAP_API_KEY=your_amap_api_key_here
AMAP_SECURITY_CODE=your_amap_security_code_here
```

获取API密钥：https://lbs.amap.com/

## 前端集成

### 在Itinerary中使用

```jsx
import { LocalTransportCard } from '../components/LocalTransportCard'

// 在项目间插入小交通卡片
<LocalTransportCard 
  route={localTransportRoute}
  onRouteSelect={handleRouteSelect}
/>
```

### 路由数据格式

```javascript
{
  from_location: {
    name: "酒店名称",
    type: "hotel",
    coords: { lat: 25.3, lng: 110.3 }
  },
  to_location: {
    name: "早餐店名称",
    type: "food",
    coords: { lat: 25.31, lng: 110.31 }
  },
  routes: [
    {
      type: "driving",
      distance_m: 1500,
      duration_s: 300,
      polyline: "...",
      steps: [...]
    }
  ]
}
```

## 使用流程

### 1. 规划阶段

用户提交行程信息后，系统自动：
1. 规划初始小交通（起始点→大交通起始点）
2. 规划项目间小交通（相邻卡片之间）
3. 返回完整的小交通路线数据

### 2. 展示阶段

前端在Itinerary中：
1. 显示初始小交通卡片（在去程大交通前）
2. 在相邻项目间插入小交通卡片
3. 用户可选择不同交通方式查看路线

### 3. 交互阶段

用户可以：
1. 切换交通方式（驾车/公交/步行）
2. 查看路线详情和步骤
3. 查看距离、耗时、预估费用

## 错误处理

### 常见问题

1. **地理编码失败**
   - 原因：地址不清晰或不存在
   - 处理：跳过该项目的小交通规划

2. **高德API调用失败**
   - 原因：API密钥无效或配额用尽
   - 处理：返回空路线列表

3. **坐标缺失**
   - 原因：无法获取项目的坐标
   - 处理：跳过该项目对的小交通规划