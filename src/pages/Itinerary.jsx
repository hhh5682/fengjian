import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { useTripStore } from '../store/tripStore'
import { LocalTransportCard } from '../components/LocalTransportCard'
import { LocalTransportCardWithAMap } from '../components/LocalTransportCardWithAMap'

const CATEGORY_CONFIG = [
  { key: 'overview', label: '总览', budgetLabel: '总计' },
  { key: 'transport', label: '交通', budgetLabel: '交通' },
  { key: 'hotel', label: '住宿', budgetLabel: '住宿' },
  { key: 'attraction', label: '景点', budgetLabel: '景点' },
  { key: 'food', label: '餐饮', budgetLabel: '餐饮' }
]

export function Itinerary() {
  const navigate = useNavigate()
  const {
    tripData,
    planResult,
    saveDraft,
    currentTripId,
    drafts,
    selectTransportOutbound,
    selectTransportReturn,
    selectMealRestaurant,
    selectHotel,
    getPricingBreakdown
  } = useTripStore()

  const [isSaving, setIsSaving] = useState(false)
  const [expandedKey, setExpandedKey] = useState(null)
  const [activeCategory, setActiveCategory] = useState('overview')

  if (!tripData.departure || !tripData.destination || !tripData.departureTime || !tripData.returnTime) {
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

  if (!planResult?.structured_plan) {
    return (
      <div className="app-scroll">
        <div
          className="fj-page fj-page-padding"
          style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}
        >
          <div style={{ textAlign: 'center' }}>
            <p style={{ marginBottom: 16, color: '#999' }}>规划数据加载中...</p>
            <button className="fj-primary-btn" onClick={() => navigate('/')}>
              返回首页
            </button>
          </div>
        </div>
      </div>
    )
  }

  const structuredPlan = planResult.structured_plan
  const pricing = getPricingBreakdown()

  const startDate = new Date(tripData.departureTime)
  const endDate = new Date(tripData.returnTime)
  const tripDays = Math.max(1, Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)))

  const daySections = useMemo(() => {
    return buildDaySections(structuredPlan, tripData, tripDays)
  }, [structuredPlan, tripData, tripDays])

  const visibleSections = useMemo(() => {
    if (activeCategory === 'overview') {
      return daySections
    }

    return daySections
      .map((day) => ({
        ...day,
        periods: day.periods
          .map((period) => ({
            ...period,
            items: period.items.filter((item) => item.category === activeCategory)
          }))
          .filter((period) => period.items.length > 0)
      }))
      .filter((day) => day.periods.length > 0)
  }, [activeCategory, daySections])

  const budgetItems = [
    { key: 'overview', label: '总计', value: `≈¥${pricing.total}` },
    { key: 'transport', label: '交通', value: `¥${pricing.transport}` },
    { key: 'hotel', label: '住宿', value: `¥${pricing.hotel}` },
    { key: 'attraction', label: '景点', value: `¥${pricing.attraction}` },
    { key: 'food', label: '餐饮', value: `≈¥${pricing.food}` }
  ]

  const dateSummary = `${format(startDate, 'M月d日')} · ${tripDays}天`

  const handleSaveDraft = () => {
    setIsSaving(true)
    const draft = {
      id: String(Date.now()),
      departure: tripData.departure,
      destination: tripData.destination,
      departureTime: tripData.departureTime,
      returnTime: tripData.returnTime,
      departureCoords: tripData.departureCoords,
      destinationCoords: tripData.destinationCoords,
      days: tripDays,
      createdAt: new Date().toISOString(),
      content: planResult
    }
    saveDraft(draft)
    setTimeout(() => {
      setIsSaving(false)
      navigate('/drafts')
    }, 400)
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

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
              borderBottom: '1px solid #ddd'
            }}
          >
            {CATEGORY_CONFIG.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => {
                  setActiveCategory(tab.key)
                  setExpandedKey(null)
                }}
                style={{
                  position: 'relative',
                  height: 34,
                  border: 'none',
                  background: 'transparent',
                  fontSize: 12,
                  color: activeCategory === tab.key ? '#111' : '#666',
                  cursor: 'pointer'
                }}
              >
                {tab.label}
                {activeCategory === tab.key && (
                  <span
                    style={{
                      position: 'absolute',
                      left: '50%',
                      bottom: -1,
                      width: 26,
                      height: 2,
                      borderRadius: 999,
                      background: '#111',
                      transform: 'translateX(-50%)'
                    }}
                  />
                )}
              </button>
            ))}
          </div>

          <div
            style={{
              paddingTop: 8,
              paddingBottom: 10
            }}
          >
            <button
              type="button"
              onClick={() => navigate('/drafts')}
              aria-label="打开购物车"
              style={{
                position: 'relative',
                width: 34,
                height: 34,
                border: 'none',
                background: 'transparent',
                padding: 0,
                marginBottom: 8,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <span style={{ fontSize: 24, lineHeight: 1 }}>🛒</span>
              <span
                style={{
                  position: 'absolute',
                  top: 2,
                  right: 0,
                  minWidth: 16,
                  height: 16,
                  borderRadius: 999,
                  background: '#ff3b30',
                  color: '#fff',
                  fontSize: 10,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0 4px'
                }}
              >
                {Math.max(1, drafts?.length || 0)}
              </span>
            </button>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, minmax(0, 1fr))',
                gap: 8
              }}
            >
              {budgetItems.map((item) => {
                const active = activeCategory === item.key
                return (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => {
                      setActiveCategory(item.key)
                      setExpandedKey(null)
                    }}
                    style={{
                      border: 'none',
                      borderRadius: 14,
                      padding: '10px 4px 8px',
                      background: active ? '#111' : '#efefef',
                      color: active ? '#fff' : '#666',
                      cursor: 'pointer'
                    }}
                  >
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: 500,
                        lineHeight: 1.1,
                        marginBottom: 8,
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {item.value}
                    </div>
                    <div style={{ fontSize: 11 }}>{item.label}</div>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <div
          className="app-scroll"
          style={{
            flex: 1,
            padding: '8px 18px 120px'
          }}
        >
          {visibleSections.length > 0 ? (
            visibleSections.map((day) => (
              <div key={`day-${day.dayIndex}`} style={{ marginBottom: 18 }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 10,
                    marginTop: 6
                  }}
                >
                  <span
                    style={{
                      background: '#f3f3f3',
                      color: '#111',
                      fontSize: 11,
                      padding: '4px 10px',
                      borderRadius: 999
                    }}
                  >
                    Day {day.dayIndex}
                  </span>
                  <span style={{ fontSize: 11, color: '#aaa' }}>{day.dateLabel}</span>
                </div>

                {day.periods.map((period) => (
                  <div key={`${day.dayIndex}-${period.label}`} style={{ marginBottom: 12 }}>
                    {!period.isTransportOnly && (
                      <div
                        className="fj-timeline-period"
                        style={{
                          marginBottom: 8
                        }}
                      >
                        <span className="fj-timeline-period-badge">{period.label}</span>
                      </div>
                    )}

                    <div style={{ position: 'relative' }}>
                      {period.items.map((item, itemIndex) => (
                        <div
                          key={item.key}
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '42px 14px minmax(0, 1fr)',
                            columnGap: 6,
                            alignItems: 'start',
                            marginBottom: itemIndex === period.items.length - 1 ? 0 : 12
                          }}
                        >
                          <div
                            style={{
                              paddingTop: 10,
                              fontSize: 13,
                              lineHeight: 1.2,
                              fontWeight: 600,
                              color: '#111',
                              textAlign: 'right',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {getDisplayTime(item)}
                          </div>

                          <div style={{ position: 'relative', display: 'flex', justifyContent: 'center', minHeight: 24 }}>
                            <div
                              style={{
                                width: 10,
                                height: 10,
                                borderRadius: '50%',
                                background: '#111',
                                marginTop: 12,
                                position: 'relative',
                                zIndex: 1
                              }}
                            />
                            {itemIndex !== period.items.length - 1 && (
                              <div
                                style={{
                                  position: 'absolute',
                                  top: 22,
                                  bottom: -20,
                                  width: 1,
                                  background: '#e6e6e6'
                                }}
                              />
                            )}
                          </div>

                          <div>
                            {renderCard({
                              item,
                              expandedKey,
                              setExpandedKey,
                              selectTransportOutbound,
                              selectTransportReturn,
                              selectMealRestaurant,
                              selectHotel,
                              daySections
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ))
          ) : (
            <div
              className="fj-card"
              style={{
                padding: '28px 16px',
                textAlign: 'center',
                color: '#bbb',
                fontSize: 13,
                marginTop: 16
              }}
            >
              当前分类下暂无可展示内容
            </div>
          )}
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
            onClick={handleSaveDraft}
            disabled={isSaving}
            style={{
              width: '100%',
              height: 60,
              borderRadius: 0,
              marginTop: 'auto'
            }}
          >
            {isSaving ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  )
}

function buildDaySections(structuredPlan, tripData, tripDays) {
  const sections = []

  for (let i = 0; i < tripDays; i += 1) {
    const date = new Date(new Date(tripData.departureTime).getTime() + i * 24 * 60 * 60 * 1000)
    sections.push({
      dayIndex: i + 1,
      dateLabel: format(date, 'M月d日'),
      periods: []
    })
  }

  const pushItem = (dayIndex, periodLabel, item, isTransportOnly = false) => {
    const targetDay = sections[Math.max(0, Math.min(sections.length - 1, dayIndex - 1))]
    if (!targetDay) return

    let period = targetDay.periods.find((p) => p.label === periodLabel)
    if (!period) {
      period = { label: periodLabel, items: [], isTransportOnly }
      targetDay.periods.push(period)
    }
    period.items.push(item)
  }

  const outboundPlan = structuredPlan.transport?.outbound
  const outboundSelected = getSelectedOption(outboundPlan)
  const outboundArrivalDay = outboundSelected
    ? resolveDayIndex(outboundSelected.arrival_time, tripData.departureTime, 1)
    : null
  const outboundArrivalClock = outboundSelected
    ? normalizeClock(outboundSelected.arrival_time)
    : null

  const returnPlan = structuredPlan.transport?.return
  const returnSelected = getSelectedOption(returnPlan)
  const returnDepartureDay = returnSelected
    ? resolveDayIndex(returnSelected.departure_time, tripData.departureTime, tripDays)
    : null
  const returnDepartureClock = returnSelected
    ? normalizeClock(returnSelected.departure_time)
    : null

  const isWithinVisibleRange = (dayIndex, clock) => {
    const normalizedClock = normalizeClock(clock)

    if (outboundArrivalDay != null) {
      if (dayIndex < outboundArrivalDay) return false
      if (dayIndex === outboundArrivalDay && outboundArrivalClock && normalizedClock !== '--:--') {
        if (clockToMinutes(normalizedClock) < clockToMinutes(outboundArrivalClock)) {
          return false
        }
      }
    }

    if (returnDepartureDay != null) {
      if (dayIndex > returnDepartureDay) return false
      if (dayIndex === returnDepartureDay && returnDepartureClock && normalizedClock !== '--:--') {
        if (clockToMinutes(normalizedClock) > clockToMinutes(returnDepartureClock)) {
          return false
        }
      }
    }

    return true
  }

  // 1. 添加去程大交通
  if (outboundPlan?.options?.length && outboundSelected) {
    pushItem(
      resolveDayIndex(outboundSelected.departure_time, tripData.departureTime, 1),
      '交通',
      {
        key: 'transport-outbound',
        type: 'transport-outbound',
        category: 'transport',
        timeNode: normalizeClock(outboundSelected.departure_time),
        title: `${outboundSelected.transport_type} ${outboundSelected.trip_number}`,
        data: outboundPlan
      },
      true
    )
  }

  // 2. 收集所有有效节点（景点、餐饮、酒店）
  const validNodes = []

  ;(structuredPlan.attractions || []).forEach((attraction, index) => {
    const timeNode = normalizeClock(attraction.start_time || attraction.time || '--:--')
    const dayIndex = resolveDayIndex(
      attraction.day_label || attraction.start_time || attraction.time,
      tripData.departureTime,
      1
    )

    if (!isWithinVisibleRange(dayIndex, timeNode)) return

    validNodes.push({
      dayIndex,
      timeNode,
      sortMinutes: clockToMinutes(timeNode),
      item: {
        key: `attraction-${index}`,
        type: 'attraction',
        category: 'attraction',
        timeNode,
        title: attraction.location,
        data: attraction
      }
    })
  })

  ;(structuredPlan.foods || []).forEach((meal, index) => {
    const timeNode = normalizeClock(meal.meal_clock || meal.meal_time || '--:--')
    const dayIndex = resolveDayIndex(meal.day_label || meal.meal_time || meal.meal_clock, tripData.departureTime, 1)

    if (!isWithinVisibleRange(dayIndex, timeNode)) return

    validNodes.push({
      dayIndex,
      timeNode,
      sortMinutes: clockToMinutes(timeNode),
      item: {
        key: `food-${index}`,
        type: 'food',
        category: 'food',
        timeNode,
        title: meal.selectedOption?.name || meal.selected_option?.name || '餐厅',
        data: meal,
        mealIndex: index
      }
    })
  })

  const selectedHotel = getSelectedOption(structuredPlan.hotels)
  if (selectedHotel) {
    for (let day = 1; day < tripDays; day += 1) {
      if (isWithinVisibleRange(day, '21:00')) {
        validNodes.push({
          dayIndex: day,
          timeNode: '21:00',
          sortMinutes: clockToMinutes('21:00'),
          item: {
            key: `hotel-${day}`,
            type: 'hotel',
            category: 'hotel',
            timeNode: '21:00',
            title: selectedHotel.hotel_name,
            data: structuredPlan.hotels
          }
        })
      }
    }
  }

  // 3. 按时间排序有效节点
  validNodes.sort((a, b) => {
    if (a.dayIndex !== b.dayIndex) return a.dayIndex - b.dayIndex
    return a.sortMinutes - b.sortMinutes
  })

  // 4. 添加有效节点到时间轴
  validNodes.forEach((node) => {
    const periodLabel = node.item.period_label || inferPeriodByClock(node.timeNode)
    pushItem(node.dayIndex, periodLabel, node.item)
  })

  // 5. 添加返程大交通
  if (returnPlan?.options?.length && returnSelected) {
    pushItem(
      resolveDayIndex(returnSelected.departure_time, tripData.departureTime, tripDays),
      '交通',
      {
        key: 'transport-return',
        type: 'transport-return',
        category: 'transport',
        timeNode: normalizeClock(returnSelected.departure_time),
        title: `${returnSelected.transport_type} ${returnSelected.trip_number}`,
        data: returnPlan
      },
      true
    )
  }

  // 6. 添加小交通卡片
  const localTransports = structuredPlan.local_transports || []
  localTransports.forEach((localTransport, index) => {
    if (!localTransport || !localTransport.from_location || !localTransport.to_location) return

    const sortTime = localTransport.sort_time || '--:--'
    const sortDayLabel = localTransport.sort_day_label || ''
    const dayIndex = resolveDayIndex(sortDayLabel || sortTime, tripData.departureTime, 1)
    const periodLabel = inferPeriodByClock(sortTime)
    
    pushItem(
      dayIndex,
      periodLabel,
      {
        key: `local-transport-${index}`,
        type: 'local-transport',
        category: 'transport',
        timeNode: sortTime,
        sortClock: sortTime,
        sortDayLabel,
        title: `${localTransport.from_location.name} → ${localTransport.to_location.name}`,
        data: localTransport,
        hideTime: false
      },
      true
    )
  })

  // 7. 标记初始小交通
  let isFirstLocalTransport = true
  const allItems = sections.flatMap(s => s.periods.flatMap(p => p.items))
  allItems.forEach((item) => {
    if (item.type === 'local-transport') {
      if (isFirstLocalTransport) {
        item._isInitialTransport = true
        isFirstLocalTransport = false
      }
    }
  })

  // 8. 先把每天所有项目按真实时间全量排序，再重新分组，避免分组后顺序错乱
  sections.forEach((section) => {
    const allItems = section.periods.flatMap((period) => period.items)

    allItems.sort((a, b) => {
      const timeDiff = getSortMinutes(a) - getSortMinutes(b)
      if (timeDiff !== 0) return timeDiff

      if (a.type === 'transport-outbound' && b.type !== 'transport-outbound') return -1
      if (b.type === 'transport-outbound' && a.type !== 'transport-outbound') return 1

      if (a.type === 'transport-return' && b.type !== 'transport-return') return 1
      if (b.type === 'transport-return' && a.type !== 'transport-return') return -1

      return getPeriodRank(a) - getPeriodRank(b)
    })

    const rebuiltPeriods = []
    allItems.forEach((item) => {
      const periodLabel =
        item.type === 'transport-outbound' || item.type === 'transport-return'
          ? '交通'
          : inferPeriodByClock(item.sortClock || item.timeNode)

      let period = rebuiltPeriods.find((p) => p.label === periodLabel)
      if (!period) {
        period = {
          label: periodLabel,
          items: [],
          isTransportOnly: item.category === 'transport'
        }
        rebuiltPeriods.push(period)
      } else if (item.category !== 'transport') {
        period.isTransportOnly = false
      }

      period.items.push(item)
    })

    section.periods = rebuiltPeriods
  })

  return sections.filter((section) => section.periods.length > 0)
}

function renderCard({
  item,
  expandedKey,
  setExpandedKey,
  selectTransportOutbound,
  selectTransportReturn,
  selectMealRestaurant,
  selectHotel,
  daySections
}) {
  if (item.type === 'local-transport') {
    const route = item.data
    console.log('[Itinerary] rendering local-transport card:', route)
    if (!route || !route.from_location || !route.to_location) {
      console.warn('[Itinerary] local-transport data invalid, skipping:', route)
      return null
    }
    return <LocalTransportCardWithAMap route={route} onRouteSelect={() => {}} />
  }

  if (item.type === 'transport-outbound' || item.type === 'transport-return') {
    const plan = item.data
    const selectedIdx = getSelectedIndex(plan)
    const selected = plan.options?.[selectedIdx] || plan.options?.[0]
    const options = plan.options || []
    const isExpanded = expandedKey === item.key

    if (!selected) return null

    const getTransportIcon = (transportType) => {
      const text = String(transportType || '')
      if (text.includes('飞机')) return '/img/飞机.svg'
      if (text.includes('高铁') || text.includes('火车')) return '/img/高铁火车.svg'
      if (text.includes('大巴')) return '/img/大巴车.svg'
      return '/img/汽车.png'
    }

    return (
      <div
        className="fj-card"
        style={{
          padding: '14px 14px 12px',
          borderRadius: 18,
          border: '1px solid #efefef',
          boxShadow: '0 6px 20px rgba(0,0,0,0.04)'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 0 }}>
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: 6,
                background: '#f7f7f7',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}
            >
              <img
                src={getTransportIcon(selected.transport_type)}
                alt={selected.transport_type}
                style={{ width: 14, height: 14, objectFit: 'contain' }}
              />
            </div>
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  fontSize: 12,
                  fontWeight: 600,
                  color: '#111',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {selected.transport_type}
              </div>
            </div>
          </div>

          <button
            type="button"
            style={{
              minWidth: 82,
              height: 34,
              borderRadius: 10,
              border: '1px solid #e8e8e8',
              background: '#fff',
              fontSize: 14,
              color: '#111',
              cursor: 'pointer'
            }}
          >
            ¥{Math.round(selected.estimated_price || 0)}
          </button>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr',
            gap: 12,
            alignItems: 'center',
            marginBottom: 12
          }}
        >
          <div>
            <div style={{ fontSize: 18, lineHeight: 1, fontFamily: "'DM Sans', sans-serif", color: '#111' }}>
              {extractClock(selected.departure_time)}
            </div>
            <div style={{ fontSize: 10, color: '#777', marginTop: 4, wordBreak: 'break-all' }}>{selected.departure_station}</div>
          </div>

          <div style={{ minWidth: 70, textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: '#555', marginBottom: 4 }}>{selected.trip_number}</div>
            <div style={{ height: 1, background: '#ddd', marginBottom: 4 }} />
            <div style={{ fontSize: 10, color: '#999' }}>{selected.duration}</div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 18, lineHeight: 1, fontFamily: "'DM Sans', sans-serif", color: '#111' }}>
              {extractClock(selected.arrival_time)}
            </div>
            <div style={{ fontSize: 10, color: '#777', marginTop: 4, wordBreak: 'break-all' }}>{selected.arrival_station}</div>
          </div>
        </div>

        {options.length > 1 && (
          <>
            <div
              style={{
                marginTop: 2,
                marginBottom: 10,
                fontSize: 12,
                color: '#666',
                cursor: 'pointer',
                textAlign: 'center'
              }}
              onClick={() => setExpandedKey(isExpanded ? null : item.key)}
            >
              {isExpanded ? '收起交通方案' : '更换交通方式'}
            </div>

            {isExpanded && (
              <div style={{ marginTop: 6, display: 'grid', gap: 8 }}>
                {options.map((option, index) => (
                  <button
                    key={`${item.key}-${index}`}
                    type="button"
                    onClick={() => {
                      if (item.type === 'transport-outbound') {
                        selectTransportOutbound(index)
                      } else {
                        selectTransportReturn(index)
                      }
                      setExpandedKey(null)
                    }}
                    style={optionButtonStyle(index === selectedIdx)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                      <span>{option.transport_type} {option.trip_number}</span>
                      <span>¥{Math.round(option.estimated_price || 0)}</span>
                    </div>
                    <div style={{ fontSize: 11, color: '#777', marginTop: 4 }}>
                      {option.departure_time} - {option.arrival_time}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    )
  }

  if (item.type === 'attraction') {
    const attraction = item.data
    const attractionName = attraction.location || attraction.name || '景点'
    const attractionPrice =
      attraction.estimated_price_value > 0
        ? `¥${Math.round(attraction.estimated_price_value)}`
        : '免费'

    const attractionIndex = (daySections.flatMap(d => d.periods.flatMap(p => p.items)).findIndex(i => i.key === item.key) % 16) + 1
    const attractionImageUrl = `/img/景点图片/景点图片${attractionIndex}.png`

    return (
      <div
        className="fj-card"
        style={{
          padding: 0,
          overflow: 'hidden',
          borderRadius: 18,
          border: '1px solid #efefef',
          boxShadow: '0 6px 20px rgba(0,0,0,0.04)'
        }}
      >
        <div style={{ display: 'flex', gap: 12, padding: 12, alignItems: 'stretch' }}>
          <div
            style={{
              width: 116,
              minWidth: 116,
              height: 88,
              borderRadius: 12,
              overflow: 'hidden',
              background: '#f4f4f4'
            }}
          >
            <img
              src={attractionImageUrl}
              alt={attractionName}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>

          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 10, color: '#aaa', marginBottom: 6 }}>门票景点</div>
              <div
                style={{
                  fontSize: 18,
                  lineHeight: 1.2,
                  fontWeight: 600,
                  color: '#111',
                  marginBottom: 8,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {attractionName}
              </div>
              <div style={{ fontSize: 12, color: '#777' }}>
                开放时间：{attraction.opening_hours || '--'}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
              <button
                type="button"
                style={{
                  minWidth: 96,
                  height: 36,
                  borderRadius: 10,
                  border: '1px solid #e8e8e8',
                  background: '#fff',
                  fontSize: 16,
                  color: '#111',
                  cursor: 'pointer'
                }}
              >
                {attractionPrice}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (item.type === 'food') {
    const meal = item.data
    const selected = getSelectedOption(meal)
    const options = meal.options || []
    const isExpanded = expandedKey === item.key

    if (!selected) return null

    // 根据时间推断饮食类型
    const getMealType = (clock) => {
      if (!clock) return '饮食'
      const hour = Number(String(clock).split(':')[0] || 0)
      if (hour >= 5 && hour < 11) return '早餐'
      if (hour >= 11 && hour < 14) return '午餐'
      if (hour >= 17 && hour < 21) return '晚餐'
      return '饮食'
    }

    const mealType =
      meal.period_label ||
      (meal.meal_type === 'breakfast' ? '早餐' : meal.meal_type === 'lunch' ? '午餐' : meal.meal_type === 'dinner' ? '晚餐' : '') ||
      getMealType(meal.meal_clock || item.timeNode)

    const isBreakfast = mealType === '早餐'
    const foodIndex = (daySections.flatMap(d => d.periods.flatMap(p => p.items)).filter(i => i.type === 'food').findIndex(i => i.key === item.key) % (isBreakfast ? 6 : 11)) + 1
    const foodImageUrl = isBreakfast ? `/img/早餐图片/早餐图片${foodIndex}.png` : `/img/饮食图片/饮食图片${foodIndex}.png`

    return (
      <div
        className="fj-card"
        style={{
          padding: 0,
          overflow: 'hidden',
          borderRadius: 18,
          border: '1px solid #efefef',
          boxShadow: '0 6px 20px rgba(0,0,0,0.04)'
        }}
      >
        <div style={{ display: 'flex', gap: 12, padding: 12, alignItems: 'stretch' }}>
          <div
            style={{
              width: 116,
              minWidth: 116,
              height: 88,
              borderRadius: 12,
              overflow: 'hidden',
              background: '#f4f4f4'
            }}
          >
            <img
              src={foodImageUrl}
              alt={selected.name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>

          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 10, color: '#aaa', marginBottom: 6 }}>{mealType}</div>
              <div
                style={{
                  fontSize: 18,
                  lineHeight: 1.2,
                  fontWeight: 600,
                  color: '#111',
                  marginBottom: 8,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {selected.name}
              </div>
              <div style={{ fontSize: 12, color: '#777', marginBottom: 2 }}>
                {meal.nearby_attraction}
              </div>
              <div style={{ fontSize: 12, color: '#aaa' }}>{getDisplayTime(item)}</div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
              <button
                type="button"
                style={{
                  minWidth: 96,
                  height: 36,
                  borderRadius: 10,
                  border: '1px solid #e8e8e8',
                  background: '#fff',
                  fontSize: 16,
                  color: '#111',
                  cursor: 'pointer'
                }}
              >
                ¥{Math.round(selected.estimated_price || 0)}
              </button>
            </div>
          </div>
        </div>

        {options.length > 1 && (
          <div style={{ padding: '0 12px 12px' }}>
            <div
              style={{
                marginBottom: 10,
                fontSize: 12,
                color: '#666',
                cursor: 'pointer',
                textAlign: 'center'
              }}
              onClick={() => setExpandedKey(isExpanded ? null : item.key)}
            >
              {isExpanded ? '收起餐厅' : '更换餐厅'}
            </div>

            {isExpanded && (
              <div style={{ display: 'grid', gap: 8 }}>
                {options.map((option, index) => (
                  <button
                    key={`${item.key}-${index}`}
                    type="button"
                    onClick={() => {
                      selectMealRestaurant(item.mealIndex, index)
                      setExpandedKey(null)
                    }}
                    style={optionButtonStyle(index === getSelectedIndex(meal))}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                      <span>{option.name}</span>
                      <span>¥{Math.round(option.estimated_price || 0)}/人</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  if (item.type === 'hotel') {
    const hotelPlan = item.data
    const selected = getSelectedOption(hotelPlan)
    const options = hotelPlan.options || []
    const isExpanded = expandedKey === item.key

    if (!selected) return null

    const hotelIndex = (daySections.flatMap(d => d.periods.flatMap(p => p.items)).filter(i => i.type === 'hotel').findIndex(i => i.key === item.key) % 5) + 1
    const hotelImageUrl = `/img/住宿图片/住宿图片${hotelIndex}.png`
    const isFirstHotel = daySections.flatMap(d => d.periods.flatMap(p => p.items)).filter(i => i.type === 'hotel').findIndex(i => i.key === item.key) === 0
    const hotelActionLabel = isFirstHotel ? '办理入住' : '返回酒店'

    return (
      <div
        className="fj-card"
        style={{
          padding: 0,
          overflow: 'hidden',
          borderRadius: 18,
          border: '1px solid #efefef',
          boxShadow: '0 6px 20px rgba(0,0,0,0.04)'
        }}
      >
        <div style={{ display: 'flex', gap: 12, padding: 12, alignItems: 'stretch' }}>
          <div
            style={{
              width: 116,
              minWidth: 116,
              height: 88,
              borderRadius: 12,
              overflow: 'hidden',
              background: '#f4f4f4'
            }}
          >
            <img
              src={hotelImageUrl}
              alt={selected.hotel_name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>

          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 10, color: '#aaa', marginBottom: 6 }}>{hotelActionLabel}</div>
              <div
                style={{
                  fontSize: 18,
                  lineHeight: 1.2,
                  fontWeight: 600,
                  color: '#111',
                  marginBottom: 8,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {selected.hotel_name}
              </div>
              <div style={{ fontSize: 12, color: '#777' }}>{selected.nearby_landmark}</div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
              <button
                type="button"
                style={{
                  minWidth: 96,
                  height: 36,
                  borderRadius: 10,
                  border: '1px solid #e8e8e8',
                  background: '#fff',
                  fontSize: 16,
                  color: '#111',
                  cursor: 'pointer'
                }}
              >
                ¥{Math.round(selected.estimated_price || 0)}
              </button>
            </div>
          </div>
        </div>

        {options.length > 1 && (
          <div style={{ padding: '0 12px 12px' }}>
            <div
              style={{
                marginBottom: 10,
                fontSize: 12,
                color: '#666',
                cursor: 'pointer',
                textAlign: 'center'
              }}
              onClick={() => setExpandedKey(isExpanded ? null : item.key)}
            >
              {isExpanded ? '收起酒店' : '更换住宿地点'}
            </div>

            {isExpanded && (
              <div style={{ display: 'grid', gap: 8 }}>
                {options.map((option, index) => (
                  <button
                    key={`${item.key}-${index}`}
                    type="button"
                    onClick={() => {
                      selectHotel(index)
                      setExpandedKey(null)
                    }}
                    style={optionButtonStyle(index === getSelectedIndex(hotelPlan))}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                      <span>{option.hotel_name}</span>
                      <span>¥{Math.round(option.estimated_price || 0)}/晚</span>
                    </div>
                    <div style={{ fontSize: 11, color: '#777', marginTop: 4 }}>
                      {option.nearby_landmark}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return null
}

function optionButtonStyle(active) {
  return {
    textAlign: 'left',
    width: '100%',
    border: active ? '2px solid #111' : '1px solid #ececec',
    background: active ? '#fafafa' : '#fff',
    borderRadius: 12,
    padding: '10px 12px',
    cursor: 'pointer',
    boxShadow: active ? '0 4px 12px rgba(0,0,0,0.04)' : 'none'
  }
}

function getSelectedOption(plan) {
  if (!plan) return null

  const selectedIndex =
    typeof plan.selectedIndex === 'number'
      ? plan.selectedIndex
      : typeof plan.selected_index === 'number'
        ? plan.selected_index
        : 0

  if (plan.selectedOption) return plan.selectedOption
  if (plan.selected_option) return plan.selected_option
  if (Array.isArray(plan.options)) return plan.options[selectedIndex] || plan.options[0] || null

  return null
}

function getSelectedIndex(plan) {
  if (!plan) return 0
  if (typeof plan.selectedIndex === 'number') return plan.selectedIndex
  if (typeof plan.selected_index === 'number') return plan.selected_index
  return 0
}

function inferPeriodByClock(clock) {
  const raw = String(clock || '')
  if (!raw) return '其他'

  if (raw.includes('早餐')) return '早餐'
  if (raw.includes('午餐')) return '午餐'
  if (raw.includes('晚餐')) return '晚餐'
  if (raw.includes('上午')) return '上午'
  if (raw.includes('下午')) return '下午'
  if (raw.includes('晚上')) return '晚上'

  const normalized = normalizeClock(raw)
  if (normalized === '--:--') return '其他'

  const hour = Number(normalized.split(':')[0] || 0)
  if (hour < 11) return '上午'
  if (hour < 14) return '午餐'
  if (hour < 18) return '下午'
  if (hour < 21) return '晚餐'
  return '晚上'
}

function resolveDayIndex(dayLabel, departureTime, fallbackDay = 1) {
  if (!departureTime) return fallbackDay

  const base = new Date(departureTime)
  const value = String(dayLabel || '').trim()

  // 先尝试完整日期格式
  const dateTimeMatch = value.match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (dateTimeMatch) {
    const target = new Date(Number(dateTimeMatch[1]), Number(dateTimeMatch[2]) - 1, Number(dateTimeMatch[3]))
    return Math.max(1, Math.floor((target - startOfDay(base)) / (1000 * 60 * 60 * 24)) + 1)
  }

  // 尝试月.日 格式（如 "4.18" 或 "4.18 18:00"）
  const mdMatch = value.match(/(\d{1,2})\.(\d{1,2})/)
  if (mdMatch) {
    const month = Number(mdMatch[1])
    const day = Number(mdMatch[2])
    const target = new Date(base.getFullYear(), month - 1, day)
    return Math.max(1, Math.floor((target - startOfDay(base)) / (1000 * 60 * 60 * 24)) + 1)
  }

  // 尝试 day N 格式
  const dayIndexMatch = value.match(/day\s*(\d+)/i)
  if (dayIndexMatch) {
    return Math.max(1, Number(dayIndexMatch[1]) || fallbackDay)
  }

  return fallbackDay
}

function getDisplayTime(item) {
  if (!item) return ''

  // 如果标记为不显示时间，返回空字符串
  if (item.hideTime) return ''

  if (item.type === 'local-transport') {
    const transportClock = normalizeClock(item.sortClock || item.timeNode)
    return transportClock === '--:--' ? '' : transportClock
  }

  if (item.type === 'food') {
    const meal = item.data
    const direct = normalizeClock(meal?.meal_clock || meal?.meal_time || item.timeNode)
    if (direct !== '--:--') return direct
    if (meal?.meal_type === 'breakfast' || meal?.period_label === '早餐') return '08:00'
    if (meal?.meal_type === 'lunch' || meal?.period_label === '午餐') return '12:30'
    if (meal?.meal_type === 'dinner' || meal?.period_label === '晚餐') return '18:30'
  }

  const normalized = normalizeClock(item.timeNode)
  return normalized === '--:--' ? '' : normalized
}

function extractClock(value) {
  return normalizeClock(value)
}

function normalizeClock(value) {
  const text = String(value || '')
  // 支持 "4.18 18:00" 或 "18:00" 格式
  const match = text.match(/(\d{1,2}):(\d{2})/)
  if (!match) return '--:--'
  return `${String(Number(match[1])).padStart(2, '0')}:${match[2]}`
}

function extractDateFromDateTime(value) {
  const text = String(value || '')
  // 从 "4.18 18:00" 提取 "4.18"
  const match = text.match(/(\d{1,2}\.\d{1,2})/)
  return match ? match[1] : null
}

function clockToMinutes(value) {
  const normalized = normalizeClock(value)
  if (normalized === '--:--') return Number.MAX_SAFE_INTEGER
  const [hour, minute] = normalized.split(':').map(Number)
  return hour * 60 + minute
}

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function getEarliestPeriodMinutes(period) {
  if (!period?.items?.length) return Number.MAX_SAFE_INTEGER

  return period.items.reduce((min, item) => {
    const minutes = getSortMinutes(item)
    return Math.min(min, minutes)
  }, Number.MAX_SAFE_INTEGER)
}

function getSortMinutes(item) {
  if (!item) return Number.MAX_SAFE_INTEGER
  
  let candidate = item.timeNode
  if (item.type === 'local-transport') {
    candidate = item.sortClock || item.timeNode
  }
  
  return clockToMinutes(candidate)
}

function getPeriodGroupRank(label) {
  switch (label) {
    case '早餐':
      return 1
    case '上午':
      return 2
    case '午餐':
      return 3
    case '下午':
      return 4
    case '晚餐':
      return 5
    case '晚上':
      return 6
    default:
      return 99
  }
}

function getPeriodRank(item) {
  if (!item) return 99

  if (item.type === 'food') {
    const meal = item.data || {}
    if (meal.meal_type === 'breakfast' || meal.period_label === '早餐') return 1
    if (meal.meal_type === 'lunch' || meal.period_label === '午餐') return 3
    if (meal.meal_type === 'dinner' || meal.period_label === '晚餐') return 5
  }

  return getPeriodGroupRank(inferPeriodByClock(item?.sortClock || getDisplayTime(item)))
}