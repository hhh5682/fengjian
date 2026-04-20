# 风间 (Windroom) - 旅游规划 Web 应用

一个移动端优先、卡片化设计的旅游规划 Web 应用。核心理念是“无数卡片的组合”，由 Agent 生成交通、住宿、景点、餐饮、提醒等内容，并映射为不同 UI 卡片。

## 技术栈

- 前端：React + Vite + Tailwind CSS
- 状态管理：Zustand
- 路由：React Router
- 地图：高德地图 JS API
- 后端：Python Flask

## 高德web服务的 Key 说明
1. 需在backend/.env添加高德 web服务的 api key
如下：
```# 高德 API 配置
# 后端使用 Web服务 Key（用于坐标查询、POI 查询、服务端路线计算）
AMAP_API_KEY=高德key
AMAP_SECURITY_CODE=
```

2.文件：backend/app.py
位置：第 22 行
内容：amap_api_key = os.getenv("AMAP_API_KEY", "你的高德web服务类型的key")

# 添加高德 web端的 api key
1. src/pages/Map.jsx
位置：第 6-7 行

const AMAP_WEB_KEY = '你的key'
const AMAP_SECURITY_CODE = '你的密钥'
用途：地点选择地图（用户选择出发地/目的地时使用）

2. src/components/LocalTransportCardWithAMap.jsx
位置：第 4-5 行

const AMAP_WEB_KEY = '你的key'
const AMAP_SECURITY_CODE = '你的密钥'
用途：小交通路线地图（显示景点间的交通路线）

这两个文件都在前端代码中硬编码了相同的 Web 端 Key 和安全密钥。


## 豆包 key 说明
需在文件：backend/services/doubao_client.py， 位置：第 14-16 行添加你的豆包key
api_key: str = "豆包key",
ndpoint_id: str = "Ep ID",

## 已实现功能

- 首页：出发地、目的地、出发时间、返回时间填写
- 日期弹窗：支持左右切换月份
- 时间弹窗：支持 0-23 时、00-59 分选择
- 地图页：接入高德 API 搜索地点并保存回首页
- 行程页：预算汇总卡片、基础信息卡片、垂直时间轴
- 草稿箱：预留昨天、前 7 天、更早以前分组和删除接口
- 后端：Flask API 骨架和 Agent 模块骨架

## 前端运行

```bash
npm install
npm run dev
```

打开：

```text
http://localhost:3000
```

## 后端运行

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

后端地址：

```text
http://localhost:5000
```

## 关键文件

- [`src/App.jsx`](src/App.jsx)
- [`src/pages/Entry.jsx`](src/pages/Entry.jsx)
- [`src/pages/Map.jsx`](src/pages/Map.jsx)
- [`src/pages/Itinerary.jsx`](src/pages/Itinerary.jsx)
- [`src/pages/DraftBox.jsx`](src/pages/DraftBox.jsx)
- [`src/store/tripStore.js`](src/store/tripStore.js)
- [`backend/app.py`](backend/app.py)
