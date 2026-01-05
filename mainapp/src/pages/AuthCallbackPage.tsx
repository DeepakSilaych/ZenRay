import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { handleGoogleCallback } = useAuth()
  const [error, setError] = useState('')

  useEffect(() => {
    const code = searchParams.get('code')
    const errorParam = searchParams.get('error')
    
    if (errorParam) {
      setError('Authentication was cancelled or failed')
      return
    }
    
    if (!code) {
      setError('No authorization code received')
      return
    }
    
    handleGoogleCallback(code)
      .then(() => {
        navigate('/', { replace: true })
      })
      .catch((err) => {
        setError(err.message || 'Authentication failed')
      })
  }, [searchParams, handleGoogleCallback, navigate])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-xray-bg">
        <div className="w-full max-w-md">
          <div className="bg-xray-surface border border-xray-border rounded-lg p-8 text-center">
            <div className="text-red-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h1 className="text-xl font-semibold mb-2">Authentication Failed</h1>
            <p className="text-sm text-xray-muted mb-6">{error}</p>
            <button
              onClick={() => navigate('/login', { replace: true })}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium transition-colors"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-xray-bg">
      <div className="text-center">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-xray-muted">Completing sign in...</p>
      </div>
    </div>
  )
}

