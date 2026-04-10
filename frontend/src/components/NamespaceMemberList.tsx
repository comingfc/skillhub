import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import { NamespaceMember } from '../types'

interface NamespaceMemberListProps {
  namespaceSlug: string
  isAdmin: boolean
}

export default function NamespaceMemberList({ namespaceSlug, isAdmin }: NamespaceMemberListProps) {
  const { data: members, isLoading } = useQuery({
    queryKey: ['namespace-members', namespaceSlug],
    queryFn: async () => {
      const response = await api.get(`/namespaces/${namespaceSlug}/members`)
      return response.data as NamespaceMember[]
    },
  })

  if (isLoading) {
    return <div className="text-center py-4">Loading...</div>
  }

  if (!members?.length) {
    return <p className="text-gray-500">No members yet.</p>
  }

  const roleColors: Record<string, string> = {
    owner: 'bg-purple-100 text-purple-800',
    admin: 'bg-blue-100 text-blue-800',
    member: 'bg-gray-100 text-gray-800',
  }

  return (
    <ul className="divide-y divide-gray-200">
      {members.map((member) => (
        <li key={member.id} className="py-4 flex items-center justify-between">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
              <span className="text-primary-600 font-medium">
                {member.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">{member.username}</p>
              <p className="text-sm text-gray-500">{member.email}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                roleColors[member.role] || 'bg-gray-100 text-gray-800'
              }`}
            >
              {member.role}
            </span>
            {isAdmin && member.role !== 'owner' && (
              <button className="text-gray-400 hover:text-red-500">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </li>
      ))}
    </ul>
  )
}
