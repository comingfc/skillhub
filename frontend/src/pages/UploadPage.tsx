import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useQuery } from '@tanstack/react-query'
import { Namespace } from '../types'

interface UploadForm {
  name: string
  slug: string
  version: string
  description: string
  tags: string
  namespace_slug: string
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [manifest, setManifest] = useState<Record<string, unknown>>({})
  const [isUploading, setIsUploading] = useState(false)

  const { register, handleSubmit, watch } = useForm<UploadForm>({
    defaultValues: {
      tags: 'beta',
      version: '1.0.0',
    },
  })

  const { data: namespaces } = useQuery({
    queryKey: ['namespaces'],
    queryFn: async () => {
      const response = await api.get('/namespaces')
      return response.data as Namespace[]
    },
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const f = acceptedFiles[0]
    setFile(f)

    // Try to read manifest.json from zip
    // For simplicity, we'll accept manifest as JSON input
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/zip': ['.zip'] },
    maxFiles: 1,
  })

  const onSubmit = async (data: UploadForm) => {
    if (!file) {
      toast.error('Please upload a skill package')
      return
    }

    if (!manifest.name || !manifest.version) {
      toast.error('Please provide valid manifest (name and version required)')
      return
    }

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('name', data.name)
      formData.append('slug', data.slug)
      formData.append('version', data.version)
      formData.append('description', data.description || '')
      formData.append('tags', data.tags)
      formData.append('namespace_slug', data.namespace_slug)
      formData.append('manifest', JSON.stringify(manifest))
      formData.append('file', file)

      await api.post('/skills', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      toast.success('Skill published successfully!')
      navigate(`/skills/${data.namespace_slug}/${data.slug}`)
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      toast.error(err.response?.data?.detail || 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Upload Skill Package</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Namespace</h2>
          <select
            {...register('namespace_slug', { required: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">Select namespace</option>
            {namespaces?.map((ns) => (
              <option key={ns.id} value={ns.slug}>
                {ns.name}
              </option>
            ))}
          </select>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Skill Details</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                {...register('name', { required: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="my-skill"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
              <input
                {...register('slug', { required: true, pattern: /^[a-z0-9-]+$/ })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="my-skill"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
              <input
                {...register('version', { required: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="1.0.0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
              <select
                {...register('tags')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="beta">Beta</option>
                <option value="stable">Stable</option>
                <option value="latest">Latest</option>
              </select>
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              {...register('description')}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              placeholder="Describe your skill..."
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Skill Package</h2>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300'
            }`}
          >
            <input {...getInputProps()} />
            {file ? (
              <p className="text-gray-900 font-medium">{file.name}</p>
            ) : (
              <p className="text-gray-600">
                Drag and drop a ZIP file here, or click to select
              </p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Manifest (JSON)</h2>
          <textarea
            value={JSON.stringify(manifest, null, 2)}
            onChange={(e) => {
              try {
                setManifest(JSON.parse(e.target.value))
              } catch {
                // Invalid JSON, ignore
              }
            }}
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
            placeholder='{"name": "my-skill", "version": "1.0.0", "description": "..."}'
          />
        </div>

        <button
          type="submit"
          disabled={isUploading}
          className="w-full bg-primary-600 text-white py-3 rounded-md hover:bg-primary-700 disabled:opacity-50"
        >
          {isUploading ? 'Publishing...' : 'Publish Skill'}
        </button>
      </form>
    </div>
  )
}
