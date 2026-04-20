export function Timeline({ items = [] }) {
  return (
    <div>
      {items.map((item, index) => (
        <div key={index} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="h-4 w-4 rounded-full bg-black ring-4 ring-white" />
            {index < items.length - 1 && <div className="my-2 w-px flex-1 bg-gray-300" />}
          </div>
          <div className="min-w-0 flex-1 pb-6">{item}</div>
        </div>
      ))}
    </div>
  )
}