interface VersionBadgeProps {
  tag: string
}

export default function VersionBadge({ tag }: VersionBadgeProps) {
  const colors: Record<string, string> = {
    latest: 'bg-green-100 text-green-800 border-green-200',
    stable: 'bg-blue-100 text-blue-800 border-blue-200',
    beta: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
        colors[tag] || 'bg-gray-100 text-gray-800 border-gray-200'
      }`}
    >
      {tag}
    </span>
  )
}
