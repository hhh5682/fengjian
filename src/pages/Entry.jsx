import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTripStore } from '../store/tripStore'

const API_BASE = 'http://localhost:5000'

export function Entry() {
  const navigate = useNavigate()
  const { tripData, setDepartureTime, setReturnTime } = useTripStore()
  const [user, setUser] = useState(null)
  const [showDatePicker, setShowDatePicker] = useState(false)
  const [showTimePicker, setShowTimePicker] = useState(false)
  const [dateType, setDateType] = useState(null)
  const [timeType, setTimeType] = useState(null)
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selectedHour, setSelectedHour] = useState(9)
  const [selectedMinute, setSelectedMinute] = useState(0)
  const [showUserMenu, setShowUserMenu] = useState(false)

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (userData) {
      setUser(JSON.parse(userData))
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('user')
    navigate('/login')
  }

  const isComplete = tripData.departure && tripData.destination && tripData.departureTime && tripData.returnTime

  const isSameDay = (a, b) =>
    a &&
    b &&
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()

  const getDateBaseForType = (type) => {
    if (type === 'departure') {
      return tripData.departureTime ? new Date(tripData.departureTime) : new Date()
    }

    if (tripData.returnTime) return new Date(tripData.returnTime)
    if (tripData.departureTime) return new Date(tripData.departureTime)
    return new Date()
  }

  const isDateDisabled = (type, year, month, day) => {
    const candidate = new Date(year, month, day)
    candidate.setHours(0, 0, 0, 0)

    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

    if (type === 'departure') {
      return candidate < today
    }

    if (type === 'return') {
      const departure = tripData.departureTime ? new Date(tripData.departureTime) : new Date()
      const departureDay = new Date(departure.getFullYear(), departure.getMonth(), departure.getDate())
      return candidate < departureDay
    }

    return false
  }

  const isTimeDisabled = (type, hour, minute) => {
    const base = getDateBaseForType(type)
    const candidate = new Date(base)
    candidate.setHours(hour, minute, 0, 0)

    if (type === 'departure') {
      return candidate <= new Date()
    }

    if (type === 'return') {
      const departure = tripData.departureTime ? new Date(tripData.departureTime) : null
      if (!departure) return false
      return candidate <= departure
    }

    return false
  }

  const handleDepartureClick = () => {
    navigate('/map', { state: { type: 'departure' } })
  }

  const handleDestinationClick = () => {
    navigate('/map', { state: { type: 'destination' } })
  }

  const openDatePicker = (type) => {
    setDateType(type)

    if (type === 'departure' && tripData.departureTime) {
      setCurrentMonth(new Date(tripData.departureTime))
    } else if (type === 'return' && tripData.returnTime) {
      setCurrentMonth(new Date(tripData.returnTime))
    } else {
      setCurrentMonth(new Date())
    }

    setShowDatePicker(true)
  }

  const openTimePicker = (type) => {
    setTimeType(type)
    if (type === 'departure' && tripData.departureTime) {
      const date = new Date(tripData.departureTime)
      setSelectedHour(date.getHours())
      setSelectedMinute(date.getMinutes())
    } else if (type === 'return' && tripData.returnTime) {
      const date = new Date(tripData.returnTime)
      setSelectedHour(date.getHours())
      setSelectedMinute(date.getMinutes())
    }
    setShowTimePicker(true)
  }

  const handleDateSelect = (day) => {
    if (!day) return
    if (isDateDisabled(dateType, currentMonth.getFullYear(), currentMonth.getMonth(), day)) return

    const baseDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day)
    const existing = getDateBaseForType(dateType)

    baseDate.setHours(existing.getHours(), existing.getMinutes(), 0, 0)

    if (dateType === 'departure') {
      setDepartureTime(baseDate.toISOString())
    } else if (dateType === 'return') {
      setReturnTime(baseDate.toISOString())
    }

    setShowDatePicker(false)
  }

  const handleTimeConfirm = () => {
    if (isTimeDisabled(timeType, selectedHour, selectedMinute)) {
      return
    }

    if (timeType === 'departure') {
      const dateBase = tripData.departureTime ? new Date(tripData.departureTime) : new Date()
      const nextDeparture = new Date(dateBase)
      nextDeparture.setHours(selectedHour, selectedMinute, 0, 0)
      setDepartureTime(nextDeparture.toISOString())
    } else if (timeType === 'return') {
      const dateBase = tripData.returnTime
        ? new Date(tripData.returnTime)
        : tripData.departureTime
          ? new Date(tripData.departureTime)
          : new Date()
      const nextReturn = new Date(dateBase)
      nextReturn.setHours(selectedHour, selectedMinute, 0, 0)
      setReturnTime(nextReturn.toISOString())
    }

    setShowTimePicker(false)
  }

  const handleEnter = () => {
    if (!isComplete) return
    navigate('/loading')
  }

  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
  }

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay()
  }

  const formatDateDisplay = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return `${date.getMonth() + 1} 月 ${date.getDate()} 日`
  }

  const formatTimeDisplay = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }

  return (
    <div className="app-scroll">
      <div className="fj-page fj-page-padding" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div className="fj-top-row" style={{ alignItems: 'flex-start' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <div style={{ height: 34 }} />
            <div
              className="fj-logo"
              style={{
                fontSize: 18,
                letterSpacing: '0.08em',
                lineHeight: 1
              }}
            >
              风间
            </div>
          </div>
          <div style={{ position: 'relative' }}>
            <button
              className="fj-link-btn"
              onClick={() => setShowUserMenu(!showUserMenu)}
              style={{ position: 'relative', zIndex: 10 }}
            >
              👤 我的
            </button>
            {showUserMenu && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  background: '#fff',
                  border: '1px solid #ebebeb',
                  borderRadius: 10,
                  overflow: 'hidden',
                  zIndex: 20,
                  minWidth: 140,
                  boxShadow: '0 4px 12px rgba(0,0,0,.08)'
                }}
              >
                <button
                  onClick={() => {
                    navigate('/profile')
                    setShowUserMenu(false)
                  }}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    background: 'none',
                    border: 'none',
                    textAlign: 'left',
                    fontSize: 13,
                    color: '#111',
                    cursor: 'pointer',
                    borderBottom: '1px solid #f0f0f0'
                  }}
                >
                  我的主页
                </button>
                <button
                  onClick={() => {
                    navigate('/drafts')
                    setShowUserMenu(false)
                  }}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    background: 'none',
                    border: 'none',
                    textAlign: 'left',
                    fontSize: 13,
                    color: '#111',
                    cursor: 'pointer'
                  }}
                >
                  我的草稿箱
                </button>
              </div>
            )}
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div className="fj-field">
            <label className="fj-field-label">从这里出发</label>
            <input
              type="text"
              className="fj-field-input"
              placeholder="出发地"
              value={tripData.departure || ''}
              readOnly
              onClick={handleDepartureClick}
              style={{ cursor: 'pointer' }}
            />
            <div className="fj-field-line">
              <div className="fj-field-line-inner" />
            </div>
          </div>

          <div className="fj-time-row">
            <button className="fj-time-block" onClick={() => openDatePicker('departure')}>
              <span className="fj-time-label">出发时间</span>
              <div className="fj-time-value">{formatDateDisplay(tripData.departureTime)}</div>
              <div className="fj-time-line" />
            </button>
            <button className="fj-time-block" onClick={() => openTimePicker('departure')}>
              <span className="fj-time-label">&nbsp;</span>
              <div className="fj-time-value">{formatTimeDisplay(tripData.departureTime)}</div>
              <div className="fj-time-line" />
            </button>
          </div>

          <div className="fj-field">
            <label className="fj-field-label">目的地</label>
            <input
              type="text"
              className="fj-field-input"
              placeholder="目的地"
              value={tripData.destination || ''}
              readOnly
              onClick={handleDestinationClick}
              style={{ cursor: 'pointer' }}
            />
            <div className="fj-field-line">
              <div className="fj-field-line-inner" />
            </div>
          </div>

          <div className="fj-time-row">
            <button className="fj-time-block" onClick={() => openDatePicker('return')}>
              <span className="fj-time-label">返回时间</span>
              <div className="fj-time-value">{formatDateDisplay(tripData.returnTime)}</div>
              <div className="fj-time-line" />
            </button>
            <button className="fj-time-block" onClick={() => openTimePicker('return')}>
              <span className="fj-time-label">&nbsp;</span>
              <div className="fj-time-value">{formatTimeDisplay(tripData.returnTime)}</div>
              <div className="fj-time-line" />
            </button>
          </div>

          <div className="fj-spacer" />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', paddingBottom: 16 }}>
            <button className="fj-circle-action" onClick={handleEnter} disabled={!isComplete}>
              <span className="fj-circle-arrow">→</span>
            </button>
          </div>
        </div>
      </div>

      {showDatePicker && (
        <div className="fj-modal-overlay" onClick={() => setShowDatePicker(false)}>
          <div className="fj-modal-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="fj-modal-head" style={{ justifyContent: 'center' }}>
              <div className="fj-modal-title">{dateType === 'departure' ? '出发日期' : '返回日期'}</div>
            </div>
            <div style={{ padding: '12px 28px 8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <button
                  style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: '#bbb' }}
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
                >
                  ‹
                </button>
                <div style={{ fontFamily: "'Noto Serif SC', serif", fontSize: 14, fontWeight: 300, color: '#000' }}>
                  {currentMonth.getFullYear()}年{currentMonth.getMonth() + 1}月
                </div>
                <button
                  style={{ background: 'none', border: 'none', fontSize: 18, cursor: 'pointer', color: '#bbb' }}
                  onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
                >
                  ›
                </button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2, padding: '0 20px' }}>
                {['日', '一', '二', '三', '四', '五', '六'].map((d) => (
                  <div key={d} style={{ textAlign: 'center', fontSize: 10, color: '#ccc', padding: '5px 0' }}>
                    {d}
                  </div>
                ))}
                {Array.from({ length: getFirstDayOfMonth(currentMonth) }).map((_, i) => (
                  <div key={`empty-${i}`} />
                ))}
                {Array.from({ length: getDaysInMonth(currentMonth) }).map((_, i) => {
                  const day = i + 1
                  const disabled = isDateDisabled(dateType, currentMonth.getFullYear(), currentMonth.getMonth(), day)

                  return (
                    <button
                      key={day}
                      onClick={() => handleDateSelect(day)}
                      disabled={disabled}
                      style={{
                        aspectRatio: '1',
                        borderRadius: '50%',
                        border: 'none',
                        background: 'transparent',
                        cursor: disabled ? 'not-allowed' : 'pointer',
                        fontSize: 13,
                        fontFamily: "'DM Sans', sans-serif",
                        color: disabled ? '#ddd' : '#333'
                      }}
                    >
                      {day}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {showTimePicker && (
        <div className="fj-modal-overlay" onClick={() => setShowTimePicker(false)}>
          <div className="fj-modal-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="fj-modal-head" style={{ justifyContent: 'center' }}>
              <div className="fj-modal-title">{timeType === 'departure' ? '出发时间' : '返回时间'}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '14px 28px 0', gap: 8 }}>
              <div style={{ flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: '#ccc', letterSpacing: '0.12em', marginBottom: 5 }}>时</div>
                <select
                  value={selectedHour}
                  onChange={(e) => setSelectedHour(Number(e.target.value))}
                  style={{
                    width: '100%',
                    padding: 8,
                    fontSize: 18,
                    border: '1px solid #ddd',
                    borderRadius: 8,
                    fontFamily: "'DM Sans', sans-serif"
                  }}
                >
                  {Array.from({ length: 24 }).map((_, i) => {
                    const hourDisabled = Array.from({ length: 60 }).every((__, m) => isTimeDisabled(timeType, i, m))
                    return (
                      <option key={i} value={i} disabled={hourDisabled}>
                        {String(i).padStart(2, '0')}
                      </option>
                    )
                  })}
                </select>
              </div>
              <div style={{ fontSize: 22, color: '#000' }}>:</div>
              <div style={{ flex: 1, textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: '#ccc', letterSpacing: '0.12em', marginBottom: 5 }}>分</div>
                <select
                  value={selectedMinute}
                  onChange={(e) => setSelectedMinute(Number(e.target.value))}
                  style={{
                    width: '100%',
                    padding: 8,
                    fontSize: 18,
                    border: '1px solid #ddd',
                    borderRadius: 8,
                    fontFamily: "'DM Sans', sans-serif"
                  }}
                >
                  {Array.from({ length: 60 }).map((_, i) => (
                    <option key={i} value={i} disabled={isTimeDisabled(timeType, selectedHour, i)}>
                      {String(i).padStart(2, '0')}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div style={{ padding: '14px 28px', marginTop: 12 }}>
              <button className="fj-primary-btn" onClick={handleTimeConfirm}>
                确认
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}