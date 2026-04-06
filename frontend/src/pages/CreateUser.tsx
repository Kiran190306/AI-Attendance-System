import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import styles from './CreateUser.module.css'

export default function CreateUser() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'teacher' as 'admin' | 'teacher',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await api.post('/users', form)
      navigate('/')
    } catch (err: unknown) {
      const d = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: string } } }).response?.data
        : null
      setError(d?.error ?? 'Failed to create user')
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <h1>Add User</h1>
      <p className={styles.subtitle}>Create a new teacher or admin account.</p>

      <form onSubmit={handleSubmit} className={styles.form}>
        {error && <div className={styles.error}>{error}</div>}
        <label>
          Email *
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            required
          />
        </label>
        <label>
          Password *
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            required
            minLength={8}
          />
        </label>
        <label>
          Full Name *
          <input
            value={form.full_name}
            onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            required
          />
        </label>
        <label>
          Role
          <select
            value={form.role}
            onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as 'admin' | 'teacher' }))}
          >
            <option value="teacher">Teacher</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <div className={styles.actions}>
          <button type="button" onClick={() => navigate(-1)}>Cancel</button>
          <button type="submit" disabled={loading} className={styles.btnPrimary}>
            {loading ? 'Creating…' : 'Create User'}
          </button>
        </div>
      </form>
    </div>
  )
}
