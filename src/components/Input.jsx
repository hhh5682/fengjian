export function Input({
  value,
  onChange,
  placeholder = '',
  type = 'text',
  disabled = false,
  readOnly = false,
  onClick,
  onKeyPress,
  className = '',
  icon = null
}) {
  return (
    <div className="relative">
      {icon && <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">{icon}</div>}
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        onClick={onClick}
        onKeyPress={onKeyPress}
        className={`
          w-full px-4 py-3 border border-gray-200 rounded-lg
          focus:outline-none focus:border-black focus:ring-1 focus:ring-black
          disabled:bg-gray-100 disabled:text-gray-400
          ${icon ? 'pl-10' : ''}
          ${className}
        `}
      />
    </div>
  )
}