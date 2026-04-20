export function Button({ 
  children, 
  disabled = false, 
  onClick, 
  className = '',
  variant = 'primary',
  size = 'md'
}) {
  const baseStyles = 'font-medium rounded-lg transition-all duration-200 cursor-pointer'
  
  const variants = {
    primary: disabled 
      ? 'bg-gray-300 text-gray-500' 
      : 'bg-black text-white hover:bg-gray-800',
    secondary: 'bg-gray-100 text-black hover:bg-gray-200',
    ghost: 'bg-transparent text-black hover:bg-gray-100'
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-base',
    lg: 'px-6 py-3 text-lg'
  }

  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {children}
    </button>
  )
}