import { Link } from 'react-router-dom'
import { Skill } from '../types'

interface SkillCardProps {
  skill: Skill
}

export default function SkillCard({ skill }: SkillCardProps) {
  const tagColors: Record<string, string> = {
    latest: 'bg-green-100 text-green-800',
    stable: 'bg-blue-100 text-blue-800',
    beta: 'bg-yellow-100 text-yellow-800',
  }

  return (
    <Link
      to={`/skills/${skill.namespace_slug}/${skill.slug}`}
      className="block bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4 border border-gray-200"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-medium text-gray-900 truncate">
              {skill.namespace_slug}/{skill.name}
            </h3>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                tagColors[skill.tags] || 'bg-gray-100 text-gray-800'
              }`}
            >
              {skill.tags}
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">
            {skill.description || 'No description'}
          </p>
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
        <span>v{skill.version}</span>
        <div className="flex items-center space-x-4">
          <span className="flex items-center">
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {skill.download_count}
          </span>
          <span className="flex items-center">
            <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            {skill.rating_avg} ({skill.rating_count})
          </span>
        </div>
      </div>
    </Link>
  )
}
