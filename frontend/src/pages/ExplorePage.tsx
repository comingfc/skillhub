import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import SkillCard from '../components/SkillCard'
import SearchFilters from '../components/SearchFilters'
import { Skill } from '../types'

export default function ExplorePage() {
  const [filters, setFilters] = useState({})
  const [searchQuery, setSearchQuery] = useState('')

  const { data: skills, isLoading } = useQuery({
    queryKey: ['skills', filters],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (filters.namespace) params.append('namespace', filters.namespace)
      if (filters.tags) params.append('tags', filters.tags)
      const response = await api.get(`/skills?${params.toString()}`)
      return response.data as Skill[]
    },
  })

  const { data: searchResults } = useQuery({
    queryKey: ['search', searchQuery],
    queryFn: async () => {
      if (!searchQuery.trim()) return null
      const response = await api.get(`/search?q=${encodeURIComponent(searchQuery)}`)
      return response.data as Skill[]
    },
    enabled: searchQuery.trim().length > 0,
  })

  const displaySkills = searchQuery.trim() ? searchResults : skills

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Explore Skills</h1>
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search skills by name or description..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <svg
            className="absolute right-3 top-3 h-6 w-6 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      <div className="flex gap-8">
        <div className="w-64 flex-shrink-0">
          <SearchFilters
            onFilterChange={(f) => setFilters(f)}
          />
        </div>

        <div className="flex-1">
          {isLoading ? (
            <div className="text-center py-12">Loading...</div>
          ) : displaySkills?.length ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {displaySkills.map((skill) => (
                <SkillCard key={skill.id} skill={skill} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              {searchQuery ? 'No skills found matching your search.' : 'No skills available yet.'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
