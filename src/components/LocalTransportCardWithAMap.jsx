import { useEffect, useMemo, useRef, useState } from 'react'

// 前端使用 Web端 Key（用于地图展示、前端交互式路线显示）
const AMAP_WEB_KEY = '058fde223092ef30e2693a7d2bfd1edf'
const AMAP_SECURITY_CODE = '319c9017cefd129ab12b8e4c0ee67cda'

const TRANSPORT_MODES = [
  { key: 'driving', label: '驾车', icon: '/img/汽车.png' },
  { key: 'transit', label: '公交', icon: '/img/地铁.png' },
  { key: 'walking', label: '步行', icon: '/img/步行.png' },
  { key: 'bicycling', label: '骑行', icon: '/img/自行车.png' },
  { key: 'ebike', label: '电动车', icon: '/img/电动车.png' }
]

// 全局 SDK 加载状态
let amapSdkPromise = null

function loadAmapScriptGlobal() {
  if (amapSdkPromise) return amapSdkPromise

  amapSdkPromise = new Promise((resolve, reject) => {
    // 检查 SDK 是否已加载且所有插件都可用
    if (window.AMap && window.AMap.Driving && window.AMap.Transfer && window.AMap.Walking && window.AMap.Riding) {
      resolve(window.AMap)
      return
    }

    window._AMapSecurityConfig = {
      securityJsCode: AMAP_SECURITY_CODE
    }

    const existingScript = document.querySelector('script[data-amap="true"]')
    if (existingScript) {
      const checkPlugins = () => {
        if (window.AMap && window.AMap.Driving && window.AMap.Transfer && window.AMap.Walking && window.AMap.Riding) {
          resolve(window.AMap)
        } else {
          setTimeout(checkPlugins, 100)
        }
      }
      existingScript.addEventListener('load', checkPlugins)
      existingScript.addEventListener('error', () => reject(new Error('高德地图脚本加载失败')))
      return
    }

    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_WEB_KEY}&plugin=AMap.Driving,AMap.Transfer,AMap.Walking,AMap.Riding`
    script.async = true
    script.defer = false
    script.dataset.amap = 'true'
    
    const checkPlugins = () => {
      if (window.AMap && window.AMap.Driving && window.AMap.Transfer && window.AMap.Walking && window.AMap.Riding) {
        resolve(window.AMap)
      } else {
        setTimeout(checkPlugins, 100)
      }
    }
    
    script.onload = checkPlugins
    script.onerror = () => reject(new Error('高德地图脚本加载失败'))
    document.head.appendChild(script)
  })

  return amapSdkPromise
}

function normalizeCoordinates(location) {
  if (!location) return null

  // 后端返回格式：{"lat": 25.3, "lng": 110.3}
  if (Number.isFinite(Number(location.lat)) && Number.isFinite(Number(location.lng))) {
    return [Number(location.lng), Number(location.lat)]
  }

  // 数组格式：[lng, lat]
  if (Array.isArray(location.coordinates) && location.coordinates.length >= 2) {
    const lng = Number(location.coordinates[0])
    const lat = Number(location.coordinates[1])
    if (Number.isFinite(lng) && Number.isFinite(lat)) {
      return [lng, lat]
    }
  }

  // 备用数组格式
  if (Array.isArray(location.coord) && location.coord.length >= 2) {
    const lng = Number(location.coord[0])
    const lat = Number(location.coord[1])
    if (Number.isFinite(lng) && Number.isFinite(lat)) {
      return [lng, lat]
    }
  }

  // 字符串格式
  if (typeof location.location === 'string' && location.location.includes(',')) {
    const [lng, lat] = location.location.split(',').map(Number)
    if (Number.isFinite(lng) && Number.isFinite(lat)) {
      return [lng, lat]
    }
  }

  return null
}

function formatDuration(seconds) {
  if (!seconds || !Number.isFinite(Number(seconds))) return ''
  const minutes = Math.round(Number(seconds) / 60)
  if (minutes < 60) return `${minutes}分钟`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
}

function formatDistance(meters) {
  if (!meters || !Number.isFinite(Number(meters))) return '0米'
  const value = Number(meters)
  if (value < 1000) return `${Math.round(value)}米`
  return `${(value / 1000).toFixed(1)}km`
}

function pickModeLabel(mode) {
  const target = TRANSPORT_MODES.find((item) => item.key === mode)
  return target?.label || '出行'
}

function pickModeIcon(mode) {
  const target = TRANSPORT_MODES.find((item) => item.key === mode)
  return target?.icon || '/img/汽车.png'
}

function extractStepText(step) {
  if (!step) return ''
  if (typeof step.instruction === 'string' && step.instruction.trim()) return step.instruction
  if (typeof step.action === 'string' && step.action.trim()) return step.action
  if (typeof step.road === 'string' && step.road.trim()) return `沿${step.road}前进`
  return '继续前往下一段路线'
}

function buildFallbackModes(route) {
  const routes = Array.isArray(route?.routes) ? route.routes : []

  if (routes.length > 0) {
    return routes.map((item, index) => ({
      key: item.type || `fallback-${index}`,
      label: pickModeLabel(item.type),
      icon: pickModeIcon(item.type),
      distance: item.distance_m || 0,
      duration: item.duration_s || 0,
      taxiCost: item.taxi_cost || 0,
      steps: Array.isArray(item.steps) ? item.steps : [],
      source: 'fallback'
    }))
  }

  return TRANSPORT_MODES.map((mode) => ({
    key: mode.key,
    label: mode.label,
    icon: mode.icon,
    distance: 0,
    duration: 0,
    taxiCost: 0,
    steps: [],
    source: 'empty'
  }))
}

export function LocalTransportCardWithAMap({ route, onRouteSelect }) {
  const [sdkReady, setSdkReady] = useState(false)
  const [selectedMode, setSelectedMode] = useState('walking')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [routeDataByMode, setRouteDataByMode] = useState({})
  const [showDetails, setShowDetails] = useState(true)
  const [mapLoadTimeout, setMapLoadTimeout] = useState(false)

  const mapContainerRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const plannerRef = useRef(null)

  const fromCoords = useMemo(() => normalizeCoordinates(route?.from_location), [route])
  const toCoords = useMemo(() => normalizeCoordinates(route?.to_location), [route])

  const fallbackModes = useMemo(() => buildFallbackModes(route), [route])

  // 全局加载 SDK 一次（带超时）
  useEffect(() => {
    let mounted = true
    let timeoutId = null

    loadAmapScriptGlobal()
      .then(() => {
        if (!mounted) return
        setSdkReady(true)
        setMapLoadTimeout(false)
      })
      .catch((err) => {
        if (!mounted) return
        console.warn('高德地图加载失败:', err.message)
        setSdkReady(false)
      })

    // 10秒超时
    timeoutId = setTimeout(() => {
      if (!mounted) return
      if (!sdkReady) {
        console.warn('高德地图加载超时')
        setMapLoadTimeout(true)
      }
    }, 10000)

    return () => {
      mounted = false
      if (timeoutId) clearTimeout(timeoutId)
    }
  }, [])

  // 地图初始化（SDK 加载后初始化）
  useEffect(() => {
    if (!sdkReady || !mapContainerRef.current || mapInstanceRef.current) return

    try {
      console.log('[LocalTransportCardWithAMap] 初始化地图，fromCoords=', fromCoords)
      const center = fromCoords && fromCoords[0] && fromCoords[1] ? fromCoords : [116.397428, 39.90923]
      console.log('[LocalTransportCardWithAMap] 地图中心=', center)
      
      mapInstanceRef.current = new window.AMap.Map(mapContainerRef.current, {
        zoom: 13,
        resizeEnable: true,
        center: center
      })
      console.log('[LocalTransportCardWithAMap] 地图初始化成功')
    } catch (err) {
      console.error('[LocalTransportCardWithAMap] 地图初始化失败:', err)
    }

    return () => {
      if (plannerRef.current && typeof plannerRef.current.clear === 'function') {
        plannerRef.current.clear()
      }
      if (mapInstanceRef.current) {
        mapInstanceRef.current.destroy()
        mapInstanceRef.current = null
      }
      plannerRef.current = null
    }
  }, [sdkReady, fromCoords])

  useEffect(() => {
    if (!route?.from_location || !route?.to_location) {
      setError('缺少起点或终点信息')
      return
    }

    if (!fromCoords || !toCoords) {
      setError('缺少起点或终点坐标，无法规划路线')
      return
    }

    setError('')
  }, [route, fromCoords, toCoords])

  useEffect(() => {
    if (!sdkReady || !mapInstanceRef.current || !fromCoords || !toCoords) return

    if (routeDataByMode[selectedMode]?.source === 'amap') {
      return
    }

    if (plannerRef.current && typeof plannerRef.current.clear === 'function') {
      plannerRef.current.clear()
    }

    setLoading(true)
    setError('')

    const origin = new window.AMap.LngLat(fromCoords[0], fromCoords[1])
    const destination = new window.AMap.LngLat(toCoords[0], toCoords[1])

    const saveRoute = (payload) => {
      setRouteDataByMode((prev) => ({
        ...prev,
        [selectedMode]: {
          ...payload,
          source: 'amap'
        }
      }))
      setLoading(false)
      if (onRouteSelect) {
        onRouteSelect(payload)
      }
    }

    const handleFailure = (message) => {
      setRouteDataByMode((prev) => {
        const fallback = fallbackModes.find((item) => item.key === selectedMode)
        if (!fallback) return prev
        return {
          ...prev,
          [selectedMode]: fallback
        }
      })
      setError(message)
      setLoading(false)
    }

    try {
      // 验证插件是否可用
      if (!window.AMap) {
        handleFailure('高德地图SDK未加载，已显示备用结果')
        return
      }

      if (selectedMode === 'driving') {
        if (!window.AMap.Driving) {
          handleFailure('高德地图驾车插件未加载，已显示备用结果')
          return
        }
        const planner = new window.AMap.Driving({
          map: mapInstanceRef.current,
          hideMarkers: false,
          autoFitView: true
        })
        plannerRef.current = planner
        planner.search(origin, destination, (status, result) => {
          if (status !== 'complete' || !result?.routes?.length) {
            handleFailure('驾车路线规划失败，已显示备用结果')
            return
          }
          const firstRoute = result.routes[0]
          saveRoute({
            key: 'driving',
            label: '驾车',
            icon: pickModeIcon('driving'),
            distance: Number(firstRoute.distance || 0),
            duration: Number(firstRoute.time || firstRoute.duration || 0),
            taxiCost: Number(result?.taxi_cost || firstRoute.taxi_cost || 0),
            steps: Array.isArray(firstRoute.steps) ? firstRoute.steps : []
          })
        })
        return
      }

      if (selectedMode === 'transit') {
        if (!window.AMap.Transfer) {
          handleFailure('高德地图公交插件未加载，已显示备用结果')
          return
        }
        const planner = new window.AMap.Transfer({
          map: mapInstanceRef.current,
          city: route?.city || route?.to_location?.city || '全国',
          policy: 0
        })
        plannerRef.current = planner
        planner.search(origin, destination, (status, result) => {
          if (status !== 'complete' || !result?.plans?.length) {
            handleFailure('公交路线规划失败，已显示备用结果')
            return
          }
          const firstPlan = result.plans[0]
          const steps = Array.isArray(firstPlan.segments)
            ? firstPlan.segments.flatMap((segment) => {
                const items = []
                if (segment.walking && Array.isArray(segment.walking.steps)) {
                  items.push(...segment.walking.steps)
                }
                if (segment.bus && Array.isArray(segment.bus.buslines)) {
                  items.push(
                    ...segment.bus.buslines.map((line) => ({
                      instruction: `乘坐${line.name || '公交'} ${line.via_stops ? `，共${line.via_stops.length}站` : ''}`
                    }))
                  )
                }
                if (segment.railway) {
                  items.push({
                    instruction: `换乘${segment.railway.name || '轨道交通'}`
                  })
                }
                return items
              })
            : []
          saveRoute({
            key: 'transit',
            label: '公交',
            icon: pickModeIcon('transit'),
            distance: Number(firstPlan.distance || 0),
            duration: Number(firstPlan.time || firstPlan.duration || 0),
            taxiCost: 0,
            steps
          })
        })
        return
      }

      if (selectedMode === 'walking') {
        if (!window.AMap.Walking) {
          handleFailure('高德地图步行插件未加载，已显示备用结果')
          return
        }
        const planner = new window.AMap.Walking({
          map: mapInstanceRef.current,
          hideMarkers: false,
          autoFitView: true
        })
        plannerRef.current = planner
        planner.search(origin, destination, (status, result) => {
          if (status !== 'complete' || !result?.routes?.length) {
            handleFailure('步行路线规划失败，已显示备用结果')
            return
          }
          const firstRoute = result.routes[0]
          saveRoute({
            key: 'walking',
            label: '步行',
            icon: pickModeIcon('walking'),
            distance: Number(firstRoute.distance || 0),
            duration: Number(firstRoute.time || firstRoute.duration || 0),
            taxiCost: 0,
            steps: Array.isArray(firstRoute.steps) ? firstRoute.steps : []
          })
        })
        return
      }

      if (!window.AMap.Riding) {
        handleFailure('高德地图骑行插件未加载，已显示备用结果')
        return
      }
      const planner = new window.AMap.Riding({
        map: mapInstanceRef.current,
        hideMarkers: false,
        autoFitView: true
      })
      plannerRef.current = planner
      planner.search(origin, destination, (status, result) => {
        if (status !== 'complete' || !result?.routes?.length) {
          handleFailure('骑行路线规划失败，已显示备用结果')
          return
        }
        const firstRoute = result.routes[0]
        saveRoute({
          key: selectedMode,
          label: selectedMode === 'ebike' ? '电动车' : '骑行',
          icon: pickModeIcon(selectedMode === 'ebike' ? 'ebike' : 'bicycling'),
          distance: Number(firstRoute.distance || 0),
          duration: Number(firstRoute.time || firstRoute.duration || 0),
          taxiCost: 0,
          steps: Array.isArray(firstRoute.steps) ? firstRoute.steps : []
        })
      })
    } catch (err) {
      handleFailure(err.message || '路线规划失败，已显示备用结果')
    }
  }, [sdkReady, selectedMode, fromCoords, toCoords, route, fallbackModes, routeDataByMode, onRouteSelect])

  const currentRoute =
    routeDataByMode[selectedMode] ||
    fallbackModes.find((item) => item.key === selectedMode) ||
    fallbackModes[0]

  const fareText =
    currentRoute?.taxiCost && Number(currentRoute.taxiCost) > 0
      ? `预计¥${Math.round(Number(currentRoute.taxiCost))}`
      : '费用待定'

  return (
    <div
      className="fj-card"
      style={{
        padding: '12px 12px 10px',
        borderRadius: 18,
        border: '1px solid #efefef',
        boxShadow: '0 6px 20px rgba(0,0,0,0.04)',
        overflow: 'hidden',
        background: '#fff'
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 10,
          marginBottom: 10
        }}
      >
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: 11, color: '#999', marginBottom: 6 }}>出行</div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: '#111',
              lineHeight: 1.4,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {route.from_location?.name || '起点'} → {route.to_location?.name || '终点'}
          </div>
        </div>

        <div
          style={{
            flexShrink: 0,
            fontSize: 11,
            color: '#999',
            alignSelf: 'flex-end'
          }}
        >
          {fareText}
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'stretch',
          gap: 8,
          marginBottom: 10,
          overflowX: 'auto',
          paddingBottom: 2
        }}
      >
        {TRANSPORT_MODES.map((mode) => {
          const active = selectedMode === mode.key
          const modeData = routeDataByMode[mode.key] || fallbackModes.find((item) => item.key === mode.key)

          return (
            <button
              key={mode.key}
              type="button"
              onClick={() => setSelectedMode(mode.key)}
              style={{
                border: active ? '1px solid #111' : '1px solid #ececec',
                background: active ? '#111' : '#fff',
                color: active ? '#fff' : '#111',
                borderRadius: 12,
                minWidth: 74,
                padding: '6px 10px',
                cursor: 'pointer',
                flex: '0 0 auto'
              }}
            >
              <div
                style={{
                  width: 20,
                  height: 20,
                  margin: '0 auto 3px',
                  borderRadius: 999,
                  background: active ? 'rgba(255,255,255,.12)' : '#f6f6f6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <img
                  src={mode.icon}
                  alt={mode.label}
                  style={{ width: 14, height: 14, objectFit: 'contain', filter: active ? 'brightness(0) invert(1)' : 'none' }}
                />
              </div>
              <div style={{ fontSize: 10, fontWeight: 600, lineHeight: 1.1 }}>{mode.label}</div>
              <div style={{ fontSize: 10, opacity: 0.75, marginTop: 2, lineHeight: 1.1 }}>
                {modeData?.duration ? formatDuration(modeData.duration) : ''}
              </div>
            </button>
          )
        })}
      </div>

      <div
        style={{
          width: '100%',
          height: 210,
          borderRadius: 14,
          overflow: 'hidden',
          background: '#f4f4f4',
          position: 'relative',
          marginBottom: 10
        }}
      >
        <div
          ref={mapContainerRef}
          style={{
            width: '100%',
            height: '100%'
          }}
        />
        {!sdkReady && !mapLoadTimeout && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255,255,255,.7)',
              color: '#777',
              fontSize: 12
            }}
          >
            地图加载中...
          </div>
        )}
        {mapLoadTimeout && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255,255,255,.7)',
              color: '#d4380d',
              fontSize: 12
            }}
          >
            地图加载超时，请刷新重试
          </div>
        )}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '56px minmax(0, 1fr)',
          gap: 10,
          alignItems: 'start',
          marginBottom: 8
        }}
      >
        <div
          style={{
            width: 52,
            minHeight: 52,
            borderRadius: 12,
            background: '#f7f7f7',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '6px 4px'
          }}
        >
          <img
            src={currentRoute?.icon || pickModeIcon(selectedMode)}
            alt={currentRoute?.label || pickModeLabel(selectedMode)}
            style={{ width: 20, height: 20, objectFit: 'contain', marginBottom: 4 }}
          />
          <div style={{ fontSize: 10, color: '#333', fontWeight: 600 }}>
            {currentRoute?.label || pickModeLabel(selectedMode)}
          </div>
        </div>

        <div style={{ minWidth: 0 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              marginBottom: 8
            }}
          >
            <div style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>
              {currentRoute?.label || pickModeLabel(selectedMode)}
            </div>
            <div style={{ fontSize: 14, color: '#111', fontWeight: 600 }}>
              {currentRoute?.duration ? formatDuration(currentRoute.duration) : '--'}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: '#666', marginBottom: 6 }}>
            <span>距离 {currentRoute?.distance ? formatDistance(currentRoute.distance) : '--'}</span>
            <span>{fareText}</span>
          </div>

          {loading && (
            <div style={{ fontSize: 12, color: '#999' }}>
              正在通过高德规划路线...
            </div>
          )}

          {!loading && error && (
            <div style={{ fontSize: 12, color: '#d4380d' }}>
              {error}
            </div>
          )}
        </div>
      </div>

      <div style={{ borderTop: '1px solid #f2f2f2', paddingTop: 8 }}>
        <button
          type="button"
          onClick={() => setShowDetails((prev) => !prev)}
          style={{
            width: '100%',
            height: 34,
            borderRadius: 10,
            border: '1px solid #ececec',
            background: '#fff',
            fontSize: 12,
            color: '#333',
            cursor: 'pointer',
            marginBottom: showDetails ? 8 : 0
          }}
        >
          {showDetails ? '收起路线详情' : '查看路线详情'}
        </button>

        {showDetails && (
          <div
            style={{
              background: '#fafafa',
              borderRadius: 12,
              padding: '10px 12px',
              maxHeight: 170,
              overflowY: 'auto'
            }}
          >
            {(currentRoute?.steps || []).length > 0 ? (
              currentRoute.steps.slice(0, 8).map((step, index) => (
                <div
                  key={`${selectedMode}-step-${index}`}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 8,
                    fontSize: 11,
                    color: '#444',
                    lineHeight: 1.5,
                    marginBottom: index === Math.min((currentRoute.steps || []).length, 8) - 1 ? 0 : 8
                  }}
                >
                  <span style={{ color: '#111', fontWeight: 600 }}>{index + 1}.</span>
                  <span>{extractStepText(step)}</span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: 11, color: '#999' }}>暂无路线步骤</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}