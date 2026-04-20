import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { useTripStore } from '../store/tripStore'

const API_BASE = 'http://localhost:5000'

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function LoadingScreen() {
  const navigate = useNavigate()
  const { tripData, setPlanResult, planResult } = useTripStore()
  const [isLoading, setIsLoading] = useState(true)
  const [requestError, setRequestError] = useState('')
  const requestRef = useRef({
    done: false,
    ok: false,
    error: null
  })

  const startDate = useMemo(() => {
    return tripData?.departureTime ? new Date(tripData.departureTime) : null
  }, [tripData?.departureTime])

  const endDate = useMemo(() => {
    return tripData?.returnTime ? new Date(tripData.returnTime) : null
  }, [tripData?.returnTime])

  const tripDays = useMemo(() => {
    if (!startDate || !endDate) return 0
    return Math.max(1, Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)))
  }, [startDate, endDate])

  const dateSummary = useMemo(() => {
    if (!startDate) return ''
    return `${format(startDate, 'M月d日')} · ${tripDays}天`
  }, [startDate, tripDays])

  useEffect(() => {
    if (!tripData?.departure || !tripData?.destination || !tripData?.departureTime || !tripData?.returnTime) {
      navigate('/', { replace: true })
    }
  }, [navigate, tripData])

  useEffect(() => {
    const controller = new AbortController()

    requestRef.current = {
      done: false,
      ok: false,
      error: null
    }
    setRequestError('')

    async function requestPlan() {
      try {
        console.log('[LoadingScreen] 开始发起规划请求...')
        const response = await fetch(`${API_BASE}/api/planner/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal,
          body: JSON.stringify({
            departure: tripData.departure,
            destination: tripData.destination,
            departureTime: tripData.departureTime,
            returnTime: tripData.returnTime,
            departureCoords: tripData.departureCoords,
            destinationCoords: tripData.destinationCoords,
            transportModes: ['高铁', '飞机', '大巴', '顺风车'],
            hotelAnchor: tripData.destination,
            interests: ['风景', '美食'],
            foodPreferences: ['本地特色'],
            budget: 5000,
            adults: 1
          })
        })

        console.log('[LoadingScreen] 收到响应，状态码:', response.status)
        const result = await response.json()
        console.log('[LoadingScreen] 解析结果:', result.code, result.message)

        if (result.code === 0 && result.data) {
          console.log('[LoadingScreen] 规划成功，保存结果')
          setPlanResult(result.data)
          requestRef.current = { done: true, ok: true, error: null }
          setIsLoading(false)
          // 规划成功后延迟跳转
          setTimeout(() => {
            navigate('/itinerary', { replace: true })
          }, 500)
        } else {
          console.log('[LoadingScreen] 规划失败:', result.message)
          requestRef.current = { done: true, ok: false, error: result.message || '未知错误' }
          setRequestError(result.message || '未知错误')
          setIsLoading(false)
        }
      } catch (error) {
        if (error?.name === 'AbortError') {
          console.log('[LoadingScreen] 请求已取消')
          return
        }

        console.error('[LoadingScreen] 请求异常:', error)
        const errorMsg = '规划请求失败，请检查后端服务是否运行'
        requestRef.current = { done: true, ok: false, error: errorMsg }
        setRequestError(errorMsg)
        setIsLoading(false)
      }
    }

    requestPlan()

    return () => {
      controller.abort()
    }
  }, [setPlanResult, tripData, navigate])

  if (!tripData?.departure || !tripData?.destination || !tripData?.departureTime || !tripData?.returnTime) {
    return (
      <div className="app-scroll">
        <div
          className="fj-page fj-page-padding"
          style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}
        >
          <div style={{ textAlign: 'center' }}>
            <p style={{ marginBottom: 16, color: '#999' }}>请先填写行程信息</p>
            <button className="fj-primary-btn" onClick={() => navigate('/')}>
              返回首页
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (requestError) {
    return (
      <div className="app-scroll">
        <div
          className="fj-page fj-page-padding"
          style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}
        >
          <div style={{ textAlign: 'center' }}>
            <p style={{ marginBottom: 16, color: '#999' }}>{requestError}</p>
            <button className="fj-primary-btn" onClick={() => navigate('/')}>
              返回重试
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading || !planResult?.structured_plan) {
    return (
      <div className="app-scroll">
        <div
          className="fj-page"
          style={{
            position: 'relative',
            height: '100%',
            background: '#fff',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <div
            style={{
              padding: '18px 18px 0',
              borderBottom: '1px solid #f0f0f0',
              background: '#fff',
              position: 'sticky',
              top: 0,
              zIndex: 10
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 10
              }}
            >
              <button
                className="fj-back"
                onClick={() => navigate('/')}
                style={{
                  fontSize: 14,
                  color: '#999',
                  padding: 0,
                  minWidth: 48,
                  textAlign: 'left'
                }}
              >
                ‹ 返回
              </button>

              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 10,
                  minWidth: 0
                }}
              >
                <div
                  style={{
                    maxWidth: 88,
                    fontSize: 18,
                    fontWeight: 500,
                    color: '#111',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                >
                  {tripData.departure}
                </div>
                <div style={{ width: 48, height: 1, background: '#111', flexShrink: 0 }} />
                <div
                  style={{
                    maxWidth: 88,
                    fontSize: 18,
                    fontWeight: 500,
                    color: '#111',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                >
                  {tripData.destination}
                </div>
              </div>

              <div style={{ width: 48, flexShrink: 0 }} />
            </div>

            <div
              style={{
                textAlign: 'center',
                fontSize: 12,
                color: '#999',
                marginTop: 8,
                marginBottom: 14
              }}
            >
              {dateSummary}
            </div>
          </div>

          <div
            className="app-scroll"
            style={{
              flex: 1,
              padding: '40px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <div style={{ textAlign: 'center', color: '#999' }}>
              <div style={{ fontSize: 14, marginBottom: 16 }}>行程规划中...</div>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  border: '3px solid #f0f0f0',
                  borderTopColor: '#111',
                  animation: 'spin 1s linear infinite',
                  margin: '0 auto'
                }}
              />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app-scroll">
      <div
        className="fj-page"
        style={{
          position: 'relative',
          height: '100%',
          background: '#fff',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <div
          style={{
            padding: '18px 18px 0',
            borderBottom: '1px solid #f0f0f0',
            background: '#fff',
            position: 'sticky',
            top: 0,
            zIndex: 10
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 10
            }}
          >
            <button
              className="fj-back"
              onClick={() => navigate('/')}
              style={{
                fontSize: 14,
                color: '#999',
                padding: 0,
                minWidth: 48,
                textAlign: 'left'
              }}
            >
              ‹ 返回
            </button>

            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
                minWidth: 0
              }}
            >
              <div
                style={{
                  maxWidth: 88,
                  fontSize: 18,
                  fontWeight: 500,
                  color: '#111',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {tripData.departure}
              </div>
              <div style={{ width: 48, height: 1, background: '#111', flexShrink: 0 }} />
              <div
                style={{
                  maxWidth: 88,
                  fontSize: 18,
                  fontWeight: 500,
                  color: '#111',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {tripData.destination}
              </div>
            </div>

            <div style={{ width: 48, flexShrink: 0 }} />
          </div>

          <div
            style={{
              textAlign: 'center',
              fontSize: 12,
              color: '#999',
              marginTop: 8,
              marginBottom: 14
            }}
          >
            {dateSummary}
          </div>
        </div>

        <div
          className="app-scroll"
          style={{
            flex: 1,
            padding: '8px 18px 120px'
          }}
        >
          <div
            className="fj-card"
            style={{
              padding: '28px 16px',
              textAlign: 'center',
              color: '#999',
              fontSize: 13,
              marginTop: 16
            }}
          >
            规划完成，即将跳转...
          </div>
        </div>

        <div
          className="fj-bottom-actions"
          style={{
            padding: 0,
            background: 'transparent',
            borderTop: 'none'
          }}
        >
          <button
            className="fj-primary-btn"
            onClick={() => navigate('/itinerary', { replace: true })}
            style={{
              width: '100%',
              height: 60,
              borderRadius: 0
            }}
          >
            查看行程
          </button>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}