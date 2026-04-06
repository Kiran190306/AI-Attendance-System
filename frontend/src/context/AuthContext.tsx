import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api } from '../services/api'

export interface User {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'teacher'
  is_active: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
  error: string | null
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setError: (err: string | null) => void
  isAdmin: boolean
  isTeacher: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

const TOKEN_KEY = 'attendance_token'
const USER_KEY = 'attendance_user'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem(TOKEN_KEY),
    loading: true,
    error: null,
  })

  const setError = useCallback((error: string | null) => setState((s) => ({ ...s, error })), [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    api.setAuthToken(null)
    setState({ user: null, token: null, loading: false, error: null })
  }, [])

  const loadUser = useCallback(async (token: string) => {
    try {
      api.setAuthToken(token)
      const { data } = await api.get<{ id: number; email: string; full_name: string; role: string; is_active: boolean; created_at: string }>('/auth/me')
      const user: User = { ...data, role: data.role as 'admin' | 'teacher' }
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      setState((s) => ({ ...s, user, loading: false, error: null }))
    } catch {
      logout()
    }
  }, [logout])

  useEffect(() => {
    const token = state.token
    const stored = localStorage.getItem(USER_KEY)
    if (token && stored) {
      try {
        const user = JSON.parse(stored) as User
        setState((s) => ({ ...s, user, loading: false }))
        api.setAuthToken(token)
        return
      } catch {
        localStorage.removeItem(USER_KEY)
      }
      loadUser(token)
    } else {
      setState((s) => ({ ...s, loading: false }))
    }
  }, [state.token, loadUser])

  const login = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const { data } = await api.post<{ access_token: string; user: User }>('/auth/login', { email, password })
      localStorage.setItem(TOKEN_KEY, data.access_token)
      setState((s) => ({ ...s, token: data.access_token, user: data.user, loading: false, error: null }))
      api.setAuthToken(data.access_token)
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: string } } }).response?.data?.error ?? 'Login failed'
        : 'Login failed'
      setState((s) => ({ ...s, loading: false, error: message }))
      throw err
    }
  }, [])

  const value: AuthContextValue = {
    ...state,
    login,
    logout,
    setError,
    isAdmin: state.user?.role === 'admin',
    isTeacher: state.user?.role === 'teacher' || state.user?.role === 'admin',
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
