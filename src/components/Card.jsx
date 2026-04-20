export function Card({ children, className = '', onClick }) {
  return (
    <div
      onClick={onClick}
      className={`
        bg-white rounded-2xl border border-gray-200 p-4
        ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  )
}