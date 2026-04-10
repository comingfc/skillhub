import { useState } from 'react'

interface SearchFiltersProps {
  onFilterChange: (filters: { namespace?: string; tags?: string; sort?: string }) => void
}

export default function SearchFilters({ onFilterChange }: SearchFiltersProps) {
  const [namespace, setNamespace] = useState('')
  const [tags, setTags] = useState('')
  const [sort, setSort] = useState('relevance')

  const handleChange = (key: string, value: string) => {
    if (key === 'namespace') setNamespace(value)
    else if (key === 'tags') setTags(value)
    else if (key === 'sort') setSort(value)

    onFilterChange({ namespace: namespace || undefined, tags: tags || undefined, sort })
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-sm font-medium text-gray-900 mb-4">Filters</h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">Namespace</label>
          <input
            type="text"
            value={namespace}
            onChange={(e) => handleChange('namespace', e.target.value)}
            placeholder="Filter by namespace"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">Tags</label>
          <select
            value={tags}
            onChange={(e) => handleChange('tags', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="">All tags</option>
            <option value="latest">Latest</option>
            <option value="stable">Stable</option>
            <option value="beta">Beta</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">Sort by</label>
          <select
            value={sort}
            onChange={(e) => handleChange('sort', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="relevance">Relevance</option>
            <option value="downloads">Most Downloads</option>
            <option value="rating">Highest Rated</option>
            <option value="recent">Most Recent</option>
          </select>
        </div>
      </div>
    </div>
  )
}
