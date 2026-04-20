import { useRef, useEffect, useState } from 'react'

const ITEM_HEIGHT = 40

export function TimePicker({ value, onChange, onClose }) {
  const [hour, setHour] = useState(value ? Number(value.split(':')[0]) : 9)
  const [minute, setMinute] = useState(value ? Number(value.split(':')[1]) : 0)
  const hourScrollRef = useRef(null)
  const minuteScrollRef = useRef(null)

  const hourItems = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
  const minuteItems = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))

  useEffect(() => {
    if (hourScrollRef.current) {
      hourScrollRef.current.scrollTop = hour * ITEM_HEIGHT
    }
  }, [])

  useEffect(() => {
    if (minuteScrollRef.current) {
      minuteScrollRef.current.scrollTop = minute * ITEM_HEIGHT
    }
  }, [])

  const handleHourScroll = (e) => {
    const scrollTop = e.target.scrollTop
    const index = Math.round(scrollTop / ITEM_HEIGHT)
    const newHour = Math.max(0, Math.min(index, 23))
    setHour(newHour)
  }

  const handleMinuteScroll = (e) => {
    const scrollTop = e.target.scrollTop
    const index = Math.round(scrollTop / ITEM_HEIGHT)
    const newMinute = Math.max(0, Math.min(index, 59))
    setMinute(newMinute)
  }

  const confirm = () => {
    onChange(`${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`)
    onClose()
  }

  return (
    <div>
      <div className="flex items-center justify-center gap-4 py-8">
        {/* 小时滚轮 */}
        <div className="relative w-20">
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
            <div className="w-full h-10 border-2 border-red-400 rounded"></div>
          </div>
          <div
            ref={hourScrollRef}
            onScroll={handleHourScroll}
            className="h-40 overflow-y-scroll scrollbar-hide"
            style={{ scrollBehavior: 'smooth' }}
          >
            <div style={{ height: ITEM_HEIGHT }}>
              {hourItems.map((item) => (
                <div
                  key={item}
                  className="h-10 flex items-center justify-center text-lg font-semibold text-gray-600"
                  style={{ height: ITEM_HEIGHT }}
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>

        <span className="text-2xl font-bold text-gray-800">:</span>

        {/* 分钟滚轮 */}
        <div className="relative w-20">
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
            <div className="w-full h-10 border-2 border-red-400 rounded"></div>
          </div>
          <div
            ref={minuteScrollRef}
            onScroll={handleMinuteScroll}
            className="h-40 overflow-y-scroll scrollbar-hide"
            style={{ scrollBehavior: 'smooth' }}
          >
            <div style={{ height: ITEM_HEIGHT }}>
              {minuteItems.map((item) => (
                <div
                  key={item}
                  className="h-10 flex items-center justify-center text-lg font-semibold text-gray-600"
                  style={{ height: ITEM_HEIGHT }}
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <button className="w-full rounded-2xl bg-black py-3 font-medium text-white" onClick={confirm}>
        确认
      </button>
    </div>
  )
}