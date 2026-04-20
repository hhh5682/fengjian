# 风间 (Windroom) - 旅游规划 Web 应用

一个移动端优先、卡片化设计的旅游规划 Web 应用。核心理念是“无数卡片的组合”，由 Agent 生成交通、住宿、景点、餐饮、提醒等内容，并映射为不同 UI 卡片。

## 技术栈

- 前端：React + Vite + Tailwind CSS
- 状态管理：Zustand
- 路由：React Router
- 地图：高德地图 JS API
- 后端：Python Flask

## 高德 Key 说明

你提供的两串值含义不同：

- Web 端 `Key`：`058fde223092ef30e2693a7d2bfd1edf`
- 安全密钥 `securityJsCode`：`319c9017cefd129ab12b8e4c0ee67cda`

之前地图不能用的原因，就是把 `securityJsCode` 错当成了 Web Key，导致高德返回 `INVALID_USER_KEY`。

现在地图页 [`src/pages/Map.jsx`](src/pages/Map.jsx) 已改为：
- 使用真实 Web Key 加载高德 JS SDK
- 使用 `securityJsCode` 配置安全校验
- 使用 [`AMap.AutoComplete`](src/pages/Map.jsx:22) 和 [`AMap.PlaceSearch`](src/pages/Map.jsx:26) 做地点搜索

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