import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import api from '../api/client'
import { useAuthStore } from '../stores/auth'

export default function SettingsPage() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [newTokenName, setNewTokenName] = useState('')

  const { data: tokens, isLoading } = useQuery({
    queryKey: ['api-tokens'],
    queryFn: async () => {
      const response = await api.get('/auth/api-tokens')
      return response.data as Array<{
        id: string
        name: string
        created_at: string
        last_used_at: string | null
      }>
    },
  })

  const createTokenMutation = useMutation({
    mutationFn: async (name: string) => {
      const response = await api.post('/auth/api-tokens', null, { params: { name } })
      return response.data as { id: string; name: string; token: string }
    },
    onSuccess: (data) => {
      toast.success('API token created! Copy it now - you won\'t see it again.')
      setNewTokenName('')
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] })
      // Show the token once
      navigator.clipboard.writeText(data.token)
    },
    onError: () => {
      toast.error('Failed to create token')
    },
  })

  const deleteTokenMutation = useMutation({
    mutationFn: async (tokenId: string) => {
      await api.delete(`/auth/api-tokens/${tokenId}`)
    },
    onSuccess: () => {
      toast.success('Token deleted')
      queryClient.invalidateQueries({ queryKey: ['api-tokens'] })
    },
    onError: () => {
      toast.error('Failed to delete token')
    },
  })

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Profile</h2>
        <dl className="space-y-2">
          <div className="flex">
            <dt className="font-medium text-gray-700 w-32">Username:</dt>
            <dd className="text-gray-600">{user?.username}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-32">Email:</dt>
            <dd className="text-gray-600">{user?.email}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-32">Role:</dt>
            <dd className="text-gray-600">
              {user?.is_admin ? 'Platform Admin' : 'User'}
            </dd>
          </div>
        </dl>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">API Tokens</h2>
        <p className="text-sm text-gray-600 mb-4">
          API tokens allow programmatic access to your account. Keep them secret!
        </p>

        <div className="flex gap-2 mb-6">
          <input
            type="text"
            value={newTokenName}
            onChange={(e) => setNewTokenName(e.target.value)}
            placeholder="Token name (e.g., CI/CD)"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
          />
          <button
            onClick={() => newTokenName && createTokenMutation.mutate(newTokenName)}
            disabled={!newTokenName || createTokenMutation.isPending}
            className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 disabled:opacity-50"
          >
            Create Token
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-4">Loading...</div>
        ) : tokens?.length ? (
          <ul className="divide-y divide-gray-200">
            {tokens.map((token) => (
              <li key={token.id} className="py-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{token.name}</p>
                  <p className="text-sm text-gray-500">
                    Created {new Date(token.created_at).toLocaleDateString()}
                    {token.last_used_at && ` • Last used ${new Date(token.last_used_at).toLocaleDateString()}`}
                  </p>
                </div>
                <button
                  onClick={() => deleteTokenMutation.mutate(token.id)}
                  className="text-red-600 hover:text-red-700"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500 text-center py-4">No API tokens yet.</p>
        )}
      </div>
    </div>
  )
}
