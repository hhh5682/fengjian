# 风间运行说明

## 1. 运行前端

在项目根目录执行：

```bash
npm install
npm run dev
```

启动后访问：

```text
http://localhost:3000
```

## 2. 运行后端

进入 [`backend`](backend) 目录后执行：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

启动后访问：

```text
http://localhost:5000/api/health
```

## 3. 当前已完成内容

- [`package.json`](package.json) 前端依赖与脚本
- [`src/components`](src/components) 基础组件库
- [`src/pages/Entry.jsx`](src/pages/Entry.jsx) 首页
- [`src/pages/Map.jsx`](src/pages/Map.jsx) 地图搜索页
- [`src/pages/Itinerary.jsx`](src/pages/Itinerary.jsx) 行程展示页
- [`src/pages/DraftBox.jsx`](src/pages/DraftBox.jsx) 草稿箱
- [`backend/app.py`](backend/app.py) Flask 后端骨架
- [`backend/agents`](backend/agents) Agent 模块骨架

## 4. 下一步建议

先执行前端安装和运行，确认页面能打开。然后再启动后端。