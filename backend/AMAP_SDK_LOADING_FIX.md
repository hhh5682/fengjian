# 高德地图 SDK 加载修复指南

## 问题诊断

### 前端错误
```
window.AMap.Driving is not a constructor
```

### 根本原因
高德地图 SDK 脚本加载时，插件（Driving、Transfer、Walking、Riding）的初始化需要时间。React 组件在脚本 `onload` 事件触发时立即尝试使用这些插件，但此时插件可能还未完全初始化。

## 修复方案

### 1. 前端 SDK 加载逻辑改进

**文件**: `src/components/LocalTransportCardWithAMap.jsx`

**改动**:
- 修改 `loadAmapScript()` 函数，添加插件可用性检查
- 使用轮询机制等待所有插件初始化完成
- 将脚本加载位置从 `document.body` 改为 `document.head`
- 将 `defer` 属性改为 `false`，确保脚本同步加载

**关键代码**:
```javascript
function loadAmapScript() {
  return new Promise((resolve, reject) => {
    // 检查 SDK 是否已加载且所有插件都可用
    if (window.AMap && window.AMap.Driving && window.AMap.Transfer && window.AMap.Walking && window.AMap.Riding) {
      resolve(window.AMap)
      return
    }

    // ... 其他代码 ...

    const checkPlugins = () => {
      if (window.AMap && window.AMap.Driving && window.AMap.Transfer && window.AMap.Walking && window.AMap.Riding) {
        resolve(window.AMap)
      } else {
        setTimeout(checkPlugins, 100)  // 每 100ms 检查一次
      }
    }
    
    script.onload = checkPlugins
    document.head.appendChild(script)
  })
}
```

### 2. 前端插件可用性验证

**改动**: 在每个路线规划方法前添加插件检查

```javascript
if (selectedMode === 'driving') {
  if (!window.AMap.Driving) {
    handleFailure('高德地图驾车插件未加载，已显示备用结果')
    return
  }
  // ... 继续执行 ...
}
```

### 3. 后端 Key 配置

**文件**: `backend/.env`

```
AMAP_API_KEY=26d116615582e27a30197162f0eb9ec3
AMAP_SECURITY_CODE=
```

**说明**:
- `AMAP_API_KEY`: Web 服务 Key（用于后端 REST API 调用）
- `AMAP_SECURITY_CODE`: Web 服务安全密钥（可选）

### 4. 前端 Key 配置

**文件**: `src/components/LocalTransportCardWithAMap.jsx`

```javascript
const AMAP_WEB_KEY = '058fde223092ef30e2693a7d2bfd1edf'
const AMAP_SECURITY_CODE = '319c9017cefd129ab12b8e4c0ee67cda'
```

**说明**:
- `AMAP_WEB_KEY`: Web 端 Key（用于前端地图展示和交互）
- `AMAP_SECURITY_CODE`: Web 端安全密钥（用于前端请求签名）

## Key 类型对照表

| Key 类型 | 用途 | 调用方 | 配置位置 |
|---------|------|--------|---------|
| Web 端 Key | 前端地图展示、交互式路线规划 | 浏览器 | `src/components/LocalTransportCardWithAMap.jsx` |
| Web 服务 Key | 后端 REST API 调用（地理编码、POI 搜索、路线规划） | 服务器 | `backend/.env` |

## 验证步骤

### 1. 检查后端 Key 配置
```bash
cd backend
python test_amap_key.py
```

### 2. 检查前端 SDK 加载
打开浏览器开发者工具 → Console，执行：
```javascript
console.log('AMap:', window.AMap)
console.log('Driving:', window.AMap?.Driving)
console.log('Transfer:', window.AMap?.Transfer)
console.log('Walking:', window.AMap?.Walking)
console.log('Riding:', window.AMap?.Riding)
```

所有插件都应该显示为函数（constructor）。

### 3. 测试路线规划
1. 重启后端服务
2. 重新生成行程规划
3. 查看小交通卡片是否正常显示地图和路线

## 常见问题

### Q: 仍然显示 "window.AMap.Driving is not a constructor"
**A**: 
1. 检查浏览器控制台是否有其他错误
2. 清除浏览器缓存，重新加载页面
3. 检查网络连接，确保高德 SDK 脚本能正常加载
4. 检查 AMAP_WEB_KEY 是否正确

### Q: 后端路线规划返回错误
**A**:
1. 检查 `backend/.env` 中的 `AMAP_API_KEY` 是否正确
2. 运行 `python backend/test_amap_key.py` 诊断
3. 确保后端服务已重启（环境变量修改后需要重启）

### Q: 地图显示但路线不显示
**A**:
1. 检查起点和终点坐标是否有效
2. 查看浏览器控制台是否有错误信息
3. 检查高德 API 是否返回了路线数据

## 相关文件

- 前端地图组件: `src/components/LocalTransportCardWithAMap.jsx`
- 后端 Key 配置: `backend/.env`
- 后端 AMap 客户端: `backend/services/provider_clients.py`
- 后端诊断脚本: `backend/test_amap_key.py`
- 小交通规划: `backend/agents/orchestrator_agent.py`