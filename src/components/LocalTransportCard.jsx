import { useState } from 'react'

const TRANSPORT_ICONS = {
  driving: '🚗',
  transit: '🚌',
  walking: '🚶',
  bicycling: '🚴'
}

const TRANSPORT_LABELS = {
  driving: '驾车',
  transit: '公交',
  walking: '步行',
  bicycling: '骑行'
}

export function LocalTransportCard({ route, onRouteSelect }) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [showMap, setShowMap] = useState(false)

  console.log('[LocalTransportCard] received route data:', route)

  if (!route || !route.routes || route.routes.length === 0) {
    console.warn('[LocalTransportCard] invalid route data, returning null')
    return null
  }

  console.log('[LocalTransportCard] valid route with %d modes', route.routes.length)
  const selectedRoute = route.routes[selectedIndex]
  console.log('[LocalTransportCard] selected route [%d]:', selectedIndex, selectedRoute)

  const formatDuration = (seconds) => {
    if (!seconds) return '0分钟'
    const minutes = Math.round(seconds / 60)
    if (minutes < 60) return `${minutes}分钟`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}小时${mins}分钟`
  }

  const formatDistance = (meters) => {
    if (!meters) return '0km'
    if (meters < 1000) return `${Math.round(meters)}米`
    return `${(meters / 1000).toFixed(1)}km`
  }

  const handleSelectRoute = (index) => {
    setSelectedIndex(index)
    if (onRouteSelect) {
      onRouteSelect(route.routes[index])
    }
  }

  return (
    <div
      style={{
        background: '#fff',
        borderRadius: 14,
        border: '1px solid #efefef',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        padding: '12px 14px',
        marginBottom: 12
      }}
    >
      {/* 路线头部 - 起点到终点 */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 12,
          fontSize: 12
        }}
      >
        <div
          style={{
            flex: 1,
            minWidth: 0,
            padding: '8px 10px',
            background: '#f0f7ff',
            borderRadius: 8,
            overflow: 'hidden'
          }}
        >
          <div style={{ fontSize: 10, color: '#666', marginBottom: 2 }}>
            {route.from_location?.type || '出发地'}
          </div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: '#111',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {route.from_location?.name || '出发地'}
          </div>
        </div>

        <div style={{ color: '#0066ff', fontSize: 16, fontWeight: 'bold' }}>→</div>

        <div
          style={{
            flex: 1,
            minWidth: 0,
            padding: '8px 10px',
            background: '#f0fff0',
            borderRadius: 8,
            overflow: 'hidden'
          }}
        >
          <div style={{ fontSize: 10, color: '#666', marginBottom: 2 }}>
            {route.to_location?.type || '目的地'}
          </div>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: '#111',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {route.to_location?.name || '目的地'}
          </div>
        </div>
      </div>

      {/* 交通方式选项 */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          marginBottom: 12,
          overflowX: 'auto',
          paddingBottom: 4
        }}
      >
        {route.routes.map((r, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSelectRoute(idx)}
            style={{
              flex: '0 0 auto',
              minWidth: 90,
              padding: '10px 12px',
              border: selectedIndex === idx ? '2px solid #0066ff' : '1px solid #e0e0e0',
              borderRadius: 8,
              background: selectedIndex === idx ? '#0066ff' : '#fff',
              color: selectedIndex === idx ? '#fff' : '#333',
              cursor: 'pointer',
              transition: 'all 0.2s',
              fontSize: 12,
              fontWeight: 500
            }}
          >
            <div style={{ fontSize: 16, marginBottom: 4 }}>
              {TRANSPORT_ICONS[r.type] || '🚗'}
            </div>
            <div>{TRANSPORT_LABELS[r.type] || r.type}</div>
            <div style={{ fontSize: 11, opacity: 0.8, marginTop: 2 }}>
              {formatDuration(r.duration_s)}
            </div>
          </button>
        ))}
      </div>

      {/* 选中路线详情 */}
      {selectedRoute && (
        <div style={{ background: '#f9f9f9', borderRadius: 8, padding: '10px 12px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 12,
              marginBottom: 10,
              fontSize: 12
            }}
          >
            <div>
              <div style={{ color: '#999', marginBottom: 4 }}>距离</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>
                {formatDistance(selectedRoute.distance_m)}
              </div>
            </div>
            <div>
              <div style={{ color: '#999', marginBottom: 4 }}>耗时</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>
                {formatDuration(selectedRoute.duration_s)}
              </div>
            </div>
          </div>

          {selectedRoute.taxi_cost && (
            <div style={{ fontSize: 11, color: '#999', marginBottom: 10 }}>
              预估费用：¥{Math.round(selectedRoute.taxi_cost)}
            </div>
          )}

          {selectedRoute.steps && selectedRoute.steps.length > 0 && (
            <div>
              <button
                type="button"
                onClick={() => setShowMap(!showMap)}
                style={{
                  width: '100%',
                  padding: '8px',
                  background: '#0066ff',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  marginBottom: 8
                }}
              >
                {showMap ? '隐藏路线' : '查看路线'}
              </button>

              {showMap && (
                <div
                  style={{
                    background: '#f0f0f0',
                    borderRadius: 6,
                    padding: '8px',
                    marginBottom: 8,
                    maxHeight: 200,
                    overflowY: 'auto',
                    fontSize: 11
                  }}
                >
                  <div style={{ color: '#666', marginBottom: 6, fontWeight: 600 }}>
                    路线步骤：
                  </div>
                  {selectedRoute.steps.slice(0, 5).map((step, idx) => (
                    <div key={idx} style={{ marginBottom: 4, color: '#333' }}>
                      <span style={{ color: '#0066ff', marginRight: 4 }}>→</span>
                      {step.instruction || `步骤 ${idx + 1}`}
                    </div>
                  ))}
                  {selectedRoute.steps.length > 5 && (
                    <div style={{ color: '#0066ff', marginTop: 4 }}>
                      +{selectedRoute.steps.length - 5} 更多步骤
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}