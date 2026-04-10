import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '../api/client'
import RatingStars from '../components/RatingStars'
import VersionBadge from '../components/VersionBadge'
import { useAuthStore } from '../stores/auth'
import { Skill } from '../types'

export default function SkillDetailPage() {
  const { namespace, slug } = useParams<{ namespace: string; slug: string }>()
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null)
  const { isAuthenticated } = useAuthStore()
  const queryClient = useQueryClient()

  const { data: skill, isLoading } = useQuery({
    queryKey: ['skill', namespace, slug],
    queryFn: async () => {
      const response = await api.get(`/skills/${namespace}/${slug}`)
      return response.data as Skill
    },
  })

  const ratingMutation = useMutation({
    mutationFn: async (rating: number) => {
      await api.post(`/skills/${namespace}/${slug}/rate`, { rating })
    },
    onSuccess: () => {
      toast.success('Rating saved!')
      queryClient.invalidateQueries({ queryKey: ['skill', namespace, slug] })
    },
    onError: () => {
      toast.error('Failed to rate skill')
    },
  })

  const downloadMutation = useMutation({
    mutationFn: async () => {
      const params = selectedVersion ? `?version=${selectedVersion}` : ''
      const response = await api.get(`/skills/${namespace}/${slug}/download${params}`)
      return response.data as { url: string }
    },
    onSuccess: (data) => {
      window.open(data.url, '_blank')
    },
    onError: () => {
      toast.error('Failed to download')
    },
  })

  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>
  }

  if (!skill) {
    return <div className="text-center py-12">Skill not found</div>
  }

  return (
    <div>
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">
                {namespace}/{skill.name}
              </h1>
              <VersionBadge tag={skill.tags} />
            </div>
            <p className="text-gray-600 mb-4">{skill.description}</p>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <span>v{skill.version}</span>
              <span className="flex items-center gap-1">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {skill.download_count} downloads
              </span>
              <span className="flex items-center gap-1">
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
                {skill.rating_avg} ({skill.rating_count} ratings)
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 flex gap-4">
          {skill.versions && skill.versions.length > 0 && (
            <select
              value={selectedVersion || skill.version}
              onChange={(e) => setSelectedVersion(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md"
            >
              {skill.versions.map((v) => (
                <option key={v.id} value={v.version}>
                  v{v.version}
                </option>
              ))}
            </select>
          )}
          <button
            onClick={() => downloadMutation.mutate()}
            className="bg-primary-600 text-white px-6 py-2 rounded-md hover:bg-primary-700"
          >
            Download
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">README</h2>
            <div className="prose max-w-none">
              {skill.readme ? (
                <pre className="whitespace-pre-wrap text-sm">{skill.readme}</pre>
              ) : (
                <p className="text-gray-500">No README available</p>
              )}
            </div>
          </div>
        </div>

        <div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Rate this skill</h3>
            {isAuthenticated ? (
              <RatingStars
                value={0}
                onChange={(rating) => ratingMutation.mutate(rating)}
              />
            ) : (
              <p className="text-sm text-gray-500">
                <Link to="/login" className="text-primary-600">Login</Link> to rate
              </p>
            )}
          </div>

          {skill.manifest && (
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <h3 className="text-lg font-semibold mb-4">Manifest</h3>
              <dl className="space-y-2 text-sm">
                {Object.entries(skill.manifest).map(([key, value]) => (
                  <div key={key} className="flex">
                    <dt className="font-medium text-gray-700 w-32">{key}:</dt>
                    <dd className="text-gray-600">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
