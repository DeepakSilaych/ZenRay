import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { createApiKey, listApiKeys, deleteApiKey, ApiKey } from '../api'

export default function ApiKeysPage() {
  const { user } = useAuth()
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [creating, setCreating] = useState(false)
  const [newKey, setNewKey] = useState<string | null>(null)

  useEffect(() => {
    loadKeys()
  }, [])

  const loadKeys = async () => {
    try {
      setLoading(true)
      const data = await listApiKeys()
      setKeys(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API keys')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newKeyName.trim()) return
    
    try {
      setCreating(true)
      setError('')
      const result = await createApiKey(newKeyName)
      setNewKey(result.api_key)
      setNewKeyName('')
      setShowCreateForm(false)
      await loadKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API key')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (keyId: string) => {
    if (!confirm('Are you sure you want to delete this API key? It will stop working immediately.')) {
      return
    }
    
    try {
      await deleteApiKey(keyId)
      await loadKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete API key')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    alert('Copied to clipboard!')
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-xray-muted">Please sign in to manage API keys.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold mb-1">API Keys</h1>
          <p className="text-sm text-xray-muted">
            Manage API keys for programmatic access to ZenRay
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium transition-colors"
        >
          Create API Key
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm">
          {error}
        </div>
      )}

      {newKey && (
        <div className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded">
          <p className="text-sm font-medium mb-2 text-green-400">
            API Key Created! Copy it now - you won't be able to see it again.
          </p>
          <div className="flex items-center gap-2">
            <code className="flex-1 px-3 py-2 bg-xray-elevated border border-xray-border rounded text-sm font-mono">
              {newKey}
            </code>
            <button
              onClick={() => copyToClipboard(newKey)}
              className="px-3 py-2 bg-xray-elevated border border-xray-border rounded hover:bg-xray-border transition-colors"
            >
              Copy
            </button>
            <button
              onClick={() => setNewKey(null)}
              className="px-3 py-2 bg-xray-elevated border border-xray-border rounded hover:bg-xray-border transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {showCreateForm && (
        <div className="mb-6 p-4 bg-xray-elevated border border-xray-border rounded">
          <form onSubmit={handleCreate} className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1.5">Key Name</label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                required
                className="w-full px-3 py-2 bg-xray-background border border-xray-border rounded text-xray-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Production API Key"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={creating}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded font-medium transition-colors"
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false)
                  setNewKeyName('')
                }}
                className="px-4 py-2 bg-xray-elevated border border-xray-border rounded hover:bg-xray-border transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-xray-muted">Loading...</div>
      ) : keys.length === 0 ? (
        <div className="text-center py-12 text-xray-muted">
          No API keys yet. Create one to get started.
        </div>
      ) : (
        <div className="bg-xray-surface border border-xray-border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-xray-elevated border-b border-xray-border">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium">Name</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Created</th>
                <th className="text-left px-4 py-3 text-sm font-medium">Last Used</th>
                <th className="text-right px-4 py-3 text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-xray-border">
              {keys.map((key) => (
                <tr key={key.key_id}>
                  <td className="px-4 py-3 text-sm">{key.key_name}</td>
                  <td className="px-4 py-3 text-sm text-xray-muted">
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-xray-muted">
                    {key.last_used_at
                      ? new Date(key.last_used_at).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(key.key_id)}
                      className="text-red-400 hover:text-red-300 text-sm"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

