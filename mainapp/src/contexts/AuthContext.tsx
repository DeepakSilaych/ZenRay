import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export interface User {
  user_id: string
  email: string
  name?: string
  picture?: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loginWithGoogle: () => Promise<void>
  handleGoogleCallback: (code: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Load auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('auth_user')
    
    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
    setLoading(false)
  }, [])

  const loginWithGoogle = async () => {
    const res = await fetch('/api/auth/google/url')
    
    if (!res.ok) {
      throw new Error('Failed to get Google auth URL')
    }
    
    const data = await res.json()
    window.location.href = data.url
  }

  const handleGoogleCallback = async (code: string) => {
    const res = await fetch(`/api/auth/google/callback?code=${encodeURIComponent(code)}`, {
      method: 'POST',
    })
    
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Authentication failed' }))
      throw new Error(error.detail || 'Authentication failed')
    }
    
    const data = await res.json()
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('auth_token', data.access_token)
    localStorage.setItem('auth_user', JSON.stringify(data.user))
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  return (
    <AuthContext.Provider value={{ user, token, loginWithGoogle, handleGoogleCallback, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
