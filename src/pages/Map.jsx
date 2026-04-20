import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useTripStore } from '../store/tripStore'

// 前端使用 Web端 Key（用于地图展示、前端交互式路线显示）
const AMAP_WEB_KEY = '058fde223092ef30e2693a7d2bfd1edf'
const AMAP_SECURITY_CODE = '319c9017cefd129ab12b8e4c0ee67cda'

function loadAmapScript() {
  return new Promise((resolve, reject) => {
    if (window.AMap) {
      resolve(window.AMap)
      return
    }

    window._AMapSecurityConfig = {
      securityJsCode: AMAP_SECURITY_CODE
    }

    const existingScript = document.querySelector('script[data-amap="true"]')
    if (existingScript) {
      existingScript.addEventListener('load', () => resolve(window.AMap))
      existingScript.addEventListener('error', () => reject(new Error('高德地图脚本加载失败')))
      return
    }

    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_WEB_KEY}&plugin=AMap.AutoComplete,AMap.PlaceSearch`
    script.async = true
    script.defer = true
    script.dataset.amap = 'true'
    script.onload = () => resolve(window.AMap)
    script.onerror = () => reject(new Error('高德地图脚本加载失败'))
    document.body.appendChild(script)
  })
}

export function Map() {
  const navigate = useNavigate()
  const location = useLocation()
  const { tripData, setDeparture, setDestination } = useTripStore()

  const locationType = location.state?.type || 'departure'

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [sdkReady, setSdkReady] = useState(false)
  const [showResults, setShowResults] = useState(false)

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markerRef = useRef(null)
  const resultsRef = useRef(null)

  const title = useMemo(
    () => `选择${locationType === 'departure' ? '出发地' : '目的地'}`,
    [locationType]
  )

  // 初始化时，如果已有该类型的地址，则填充搜索框和地图
  useEffect(() => {
    if (locationType === 'departure' && tripData.departure) {
      setSearchQuery(tripData.departure)
      if (tripData.departureCoords) {
        setSelectedLocation({
          name: tripData.departure,
          address: '',
          location: {
            lng: tripData.departureCoords[0],
            lat: tripData.departureCoords[1]
          }
        })
      }
    } else if (locationType === 'destination' && tripData.destination) {
      setSearchQuery(tripData.destination)
      if (tripData.destinationCoords) {
        setSelectedLocation({
          name: tripData.destination,
          address: '',
          location: {
            lng: tripData.destinationCoords[0],
            lat: tripData.destinationCoords[1]
          }
        })
      }
    }
  }, [locationType, tripData])

  useEffect(() => {
    let mounted = true

    loadAmapScript()
      .then(() => {
        if (!mounted) return
        setSdkReady(true)
        setErrorMessage('')
      })
      .catch((error) => {
        if (!mounted) return
        setSdkReady(false)
        setErrorMessage(error.message || '高德地图加载失败')
      })

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    if (!sdkReady || !mapRef.current || mapInstanceRef.current) return

    mapInstanceRef.current = new window.AMap.Map(mapRef.current, {
      zoom: 11,
      center: [116.397428, 39.90923],
      resizeEnable: true
    })

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.destroy()
        mapInstanceRef.current = null
        markerRef.current = null
      }
    }
  }, [sdkReady])

  useEffect(() => {
    if (!sdkReady) return

    if (!searchQuery.trim()) {
      setSearchResults([])
      setShowResults(false)
      setErrorMessage('')
      return
    }

    let cancelled = false
    setLoading(true)
    setErrorMessage('')
    setShowResults(true)

    const timer = setTimeout(() => {
      const autoComplete = new window.AMap.AutoComplete({
        city: '全国'
      })

      autoComplete.search(searchQuery.trim(), (status, result) => {
        if (cancelled) return

        if (status !== 'complete' || !result?.tips) {
          setSearchResults([])
          setLoading(false)
          setErrorMessage('搜索失败，请稍后重试')
          return
        }

        const normalized = result.tips
          .filter((tip) => tip && (tip.location || tip.address || tip.district || tip.name))
          .map((tip, index) => ({
            id: `${tip.id || tip.name || 'tip'}-${index}`,
            name: tip.name || '未知地点',
            address: [tip.district, tip.address].filter(Boolean).join(' '),
            location: tip.location
              ? {
                  lng: Number(tip.location.lng),
                  lat: Number(tip.location.lat)
                }
              : null
          }))

        setSearchResults(normalized)
        setLoading(false)

        if (normalized.length === 0) {
          setErrorMessage('未找到相关地点')
        }
      })
    }, 300)

    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [searchQuery, sdkReady])

  const handleSelectLocation = (item) => {
    if (item.location) {
      setSelectedLocation(item)
      setShowResults(false)
      return
    }

    setLoading(true)
    setErrorMessage('')

    const placeSearch = new window.AMap.PlaceSearch({
      city: '全国'
    })

    placeSearch.search(item.name, (status, result) => {
      setLoading(false)

      if (status !== 'complete' || !result?.poiList?.pois?.length) {
        setErrorMessage('未能获取地点坐标，请尝试更具体的关键词')
        return
      }

      const poi = result.poiList.pois[0]
      if (!poi.location) {
        setErrorMessage('该地点暂无可用坐标')
        return
      }

      setSelectedLocation({
        id: poi.id || item.id,
        name: poi.name || item.name,
        address: poi.address || item.address || '',
        location: {
          lng: Number(poi.location.lng),
          lat: Number(poi.location.lat)
        }
      })
      setShowResults(false)
    })
  }

  useEffect(() => {
    if (!mapInstanceRef.current || !selectedLocation?.location) return

    const position = [selectedLocation.location.lng, selectedLocation.location.lat]

    if (!markerRef.current) {
      markerRef.current = new window.AMap.Marker({
        position,
        map: mapInstanceRef.current
      })
    } else {
      markerRef.current.setPosition(position)
    }

    mapInstanceRef.current.setFitView([markerRef.current], false, [80, 80, 80, 80], 15)
  }, [selectedLocation])

  const handleSave = () => {
    if (!selectedLocation?.location) return

    const coords = [selectedLocation.location.lng, selectedLocation.location.lat]

    if (locationType === 'departure') {
      setDeparture(selectedLocation.name, coords)
    } else {
      setDestination(selectedLocation.name, coords)
    }

    navigate(-1)
  }

  return (
    <div className="fj-page" style={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
      <div className="fj-map-search-wrap">
        <button className="fj-back" onClick={() => navigate(-1)} style={{ marginBottom: 12 }}>
          ‹ 返回
        </button>

        <div
          style={{
            fontFamily: "'Noto Serif SC', serif",
            fontSize: 18,
            fontWeight: 300,
            color: '#000',
            letterSpacing: '0.06em',
            marginBottom: 10
          }}
        >
          {title}
        </div>

        <input
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value)
            setShowResults(true)
          }}
          onFocus={() => {
            if (searchQuery.trim()) {
              setShowResults(true)
            }
          }}
          placeholder="请输入学校、商圈、景点、车站、详细地址"
          className="fj-map-search-input"
        />
      </div>

      <div className="fj-map-canvas">
        <div
          ref={mapRef}
          style={{
            position: 'absolute',
            inset: 0
          }}
        />

        {selectedLocation && (
          <div
            style={{
              position: 'absolute',
              top: 14,
              left: 18,
              right: 18,
              zIndex: 6,
              background: 'rgba(255,255,255,.94)',
              border: '1px solid #ebebeb',
              borderRadius: 14,
              padding: '12px 14px',
              boxShadow: '0 10px 24px rgba(0,0,0,.06)'
            }}
          >
            <div
              style={{
                fontFamily: "'Noto Serif SC', serif",
                fontSize: 14,
                fontWeight: 300,
                color: '#111'
              }}
            >
              {selectedLocation.name}
            </div>
          </div>
        )}

        {showResults && searchResults.length > 0 && (
          <div
            ref={resultsRef}
            className="fj-map-results"
            style={{
              maxHeight: 240,
              overflowY: 'auto',
              scrollbarWidth: 'thin'
            }}
          >
            {searchResults.map((item) => {
              const isActive =
                selectedLocation &&
                item.name === selectedLocation.name

              return (
                <div
                  key={item.id}
                  onClick={() => handleSelectLocation(item)}
                  className="fj-map-result-item"
                  style={{
                    background: isActive ? '#fafafa' : '#fff',
                    padding: '12px 14px',
                    fontSize: 13
                  }}
                >
                  <div
                    style={{
                      fontFamily: "'Noto Serif SC', serif",
                      fontSize: 13,
                      fontWeight: 300,
                      color: '#111'
                    }}
                  >
                    {item.name}
                  </div>
                  {isActive && (
                    <div style={{ marginTop: 4, fontSize: 10, color: '#000' }}>已选中 ✓</div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {!sdkReady && !errorMessage && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 4,
              color: '#888',
              fontSize: 13,
              background: 'rgba(255,255,255,.3)'
            }}
          >
            高德地图加载中...
          </div>
        )}

        {loading && (
          <div
            style={{
              position: 'absolute',
              bottom: 100,
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'rgba(0,0,0,.82)',
              color: '#fff',
              padding: '10px 18px',
              borderRadius: 20,
              fontSize: 12,
              zIndex: 8
            }}
          >
            搜索中...
          </div>
        )}

        {errorMessage && (
          <div
            style={{
              position: 'absolute',
              bottom: 100,
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'rgba(192,48,48,.92)',
              color: '#fff',
              padding: '10px 18px',
              borderRadius: 20,
              fontSize: 12,
              zIndex: 8,
              whiteSpace: 'nowrap'
            }}
          >
            {errorMessage}
          </div>
        )}
      </div>

      <div className="fj-map-save">
        <button className="fj-primary-btn" onClick={handleSave} disabled={!selectedLocation?.location}>
          保存地点
        </button>
      </div>
    </div>
  )
}