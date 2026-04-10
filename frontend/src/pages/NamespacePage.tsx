import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import NamespaceMemberList from '../components/NamespaceMemberList'
import SkillCard from '../components/SkillCard'
import { useAuthStore } from '../stores/auth'
import { Namespace, Skill } from '../types'

export default function NamespacePage() {
  const { slug } = useParams<{ slug: string }>()
  const { user } = useAuthStore()

  const { data: namespace, isLoading: nsLoading } = useQuery({
    queryKey: ['namespace', slug],
    queryFn: async () => {
      const response = await api.get(`/namespaces/${slug}`)
      return response.data as Namespace
    },
  })

  const { data: skills, isLoading: skillsLoading } = useQuery({
    queryKey: ['namespace-skills', slug],
    queryFn: async () => {
      const response = await api.get(`/skills?namespace=${slug}`)
      return response.data as Skill[]
    },
  })

  if (nsLoading) {
    return <div className="text-center py-12">Loading...</div>
  }

  if (!namespace) {
    return <div className="text-center py-12">Namespace not found</div>
  }

  const isOwner = user?.id === namespace.owner_id
  const isAdmin = isOwner || user?.is_admin

  return (
    <div>
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{namespace.name}</h1>
            <p className="text-gray-600 mt-2">{namespace.description}</p>
            <div className="mt-2 flex items-center gap-2">
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                namespace.visibility === 'public'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {namespace.visibility}
              </span>
            </div>
          </div>
          {isAdmin && (
            <Link
              to={`/namespace/${slug}/settings`}
              className="text-primary-600 hover:text-primary-700"
            >
              Settings
            </Link>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <h2 className="text-xl font-semibold mb-4">Skills</h2>
          {skillsLoading ? (
            <div className="text-center py-8">Loading...</div>
          ) : skills?.length ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {skills.map((skill) => (
                <SkillCard key={skill.id} skill={skill} />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No skills in this namespace yet.
            </div>
          )}
        </div>

        <div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Members</h3>
            <NamespaceMemberList namespaceSlug={slug!} isAdmin={isAdmin} />
          </div>
        </div>
      </div>
    </div>
  )
}
