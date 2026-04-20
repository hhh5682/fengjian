import { addMonths, eachDayOfInterval, endOfMonth, format, getDay, isBefore, startOfDay, startOfMonth } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { useMemo, useState } from 'react'

export function DatePicker({ value, onChange, onClose }) {
  const [currentMonth, setCurrentMonth] = useState(value ? new Date(value) : new Date())
  const today = startOfDay(new Date())

  const days = useMemo(() => {
    const start = startOfMonth(currentMonth)
    const end = endOfMonth(currentMonth)
    const prefix = Array.from({ length: getDay(start) }, () => null)
    return [...prefix, ...eachDayOfInterval({ start, end })]
  }, [currentMonth])

  const pick = (day) => {
    if (!day || isBefore(startOfDay(day), today)) return
    const previous = value ? new Date(value) : new Date()
    day.setHours(previous.getHours(), previous.getMinutes(), 0, 0)
    onChange(day.toISOString())
    onClose()
  }

  return (
    <div>
      <div className="mb-5 flex items-center justify-between">
        <button className="rounded-full bg-gray-100 px-4 py-2" onClick={() => setCurrentMonth(addMonths(currentMonth, -1))}>
          ←
        </button>
        <div className="font-semibold">{format(currentMonth, 'yyyy年 MMMM', { locale: zhCN })}</div>
        <button className="rounded-full bg-gray-100 px-4 py-2" onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}>
          →
        </button>
      </div>
      <div className="grid grid-cols-7 gap-2 text-center text-sm">
        {['日', '一', '二', '三', '四', '五', '六'].map((d) => (
          <div key={d} className="py-2 text-gray-400">
            {d}
          </div>
        ))}
        {days.map((day, index) => {
          const disabled = !day || isBefore(startOfDay(day), today)
          const selected = value && day && format(new Date(value), 'yyyy-MM-dd') === format(day, 'yyyy-MM-dd')
          return (
            <button
              key={day ? day.toISOString() : `empty-${index}`}
              disabled={disabled}
              onClick={() => pick(day)}
              className={`aspect-square rounded-2xl ${selected ? 'bg-black text-white' : disabled ? 'text-gray-200' : 'hover:bg-gray-100'}`}
            >
              {day ? day.getDate() : ''}
            </button>
          )
        })}
      </div>
    </div>
  )
}