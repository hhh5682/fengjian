# 高德 API Key 配置指南

## 概述

本项目采用前后端分离的高德 API Key 配置方案，确保各自的功能正常运行。

## 配置方案

### 后端配置（Web服务 Key）

**用途**：坐标查询、POI 搜索、服务端路线计算

**Key**：`26d116615582e27a30197162f0eb9ec3`

**配置位置**：`backend/.env`

```env
AMAP_API_KEY=26d116615582e27a30197162f0eb9ec3
AMAP_SECURITY_CODE=
```

**使用场景**：
- 地理编码（地址 → 坐标）：`AMapClient.geocode()`
- POI 搜索（搜索地点）：`AMapClient.search_poi()`
- 路线规划（服务端计算）：`AMapClient.route_plan()`

**调用方**：
- `OrchestratorAgent._resolve_place_coords()` - 获取景点、酒店、餐厅坐标
- `LocalTransportAgent._get_multi_mode_routes()` - 规划小交通路线

### 前端配置（Web端 Key）

**用途**：地图展示、前端交互式路线显示

**Key**：`058fde223092ef30e2693a7d2bfd1edf`

**安全密钥**：`319c9017cefd129ab12b8e4c0ee67cda`

**配置位置**：
- `src/pages/Map.jsx` - 地点选择地图
- `src/components/LocalTransportCardWithAMap.jsx` - 小交通路线地图

**使用场景**：
- 地图初始化和展示
- 地点搜索和自动完成
- 前端路线规划（驾车、公交、步行、骑行）

**调用方**：
- `Map.jsx` - 用户选择出发地/目的地
- `LocalTransportCardWithAMap.jsx` - 显示小交通路线和地图

## 工作流程

### 1. 初始小交通规划流程

```
用户输入起始点 (前端 Web端 Key 搜索)
    ↓
后端获取坐标 (后端 Web服务 Key 地理编码)
    ↓
后端规划路线 (后端 Web服务 Key 路线规划)
    ↓
前端显示地图和路线 (前端 Web端 Key 地图展示)
```

### 2. 项目间小交通规划流程

```
后端获取景点/酒店/餐厅坐标 (后端 Web服务 Key POI 搜索)
    ↓
后端规划相邻项目间路线 (后端 Web服务 Key 路线规划)
    ↓
前端显示小交通卡片和地图 (前端 Web端 Key 地图展示)
```

## 关键代码位置

### 后端

- **AMapClient 初始化**：`backend/app.py` 第 20-24 行
- **Web服务 Key 配置**：`backend/.env`
- **坐标解析**：`backend/agents/orchestrator_agent.py` 第 586-611 行
- **路线规划**：`backend/agents/local_transport_agent.py` 第 116-158 行

### 前端

- **Web端 Key 配置**：`src/pages/Map.jsx` 第 5-6 行
- **地图初始化**：`src/pages/Map.jsx` 第 114-118 行
- **小交通地图**：`src/components/LocalTransportCardWithAMap.jsx` 第 180-196 行

## 故障排查

### 后端 API 调用失败

1. 检查 `backend/.env` 中的 `AMAP_API_KEY` 是否正确
2. 查看后端日志中的 `[AMapClient]` 输出
3. 确保 Web服务 Key 已在高德开放平台开通相应接口

### 前端地图不显示

1. 检查 `src/pages/Map.jsx` 中的 `AMAP_WEB_KEY` 是否正确
2. 检查浏览器控制台是否有加载错误
3. 确保 Web端 Key 已在高德开放平台配置

### 小交通卡片显示异常

1. 检查后端是否正确返回坐标数据
2. 检查前端是否正确解析坐标格式
3. 查看浏览器控制台的地图加载日志

## 更新 Key 的步骤

1. 登录高德开放平台
2. 创建新的应用和 Key
3. 更新 `backend/.env` 或 `src/pages/Map.jsx` 中的 Key
4. 重启后端服务
5. 刷新前端页面