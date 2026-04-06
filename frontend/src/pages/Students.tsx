import { useEffect, useState } from 'react'
import { api, type Student } from '../services/api'
import styles from './Students.module.css'

export default function Students() {
  const [students, setStudents] = useState<Student[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ student_id: '', full_name: '', email: '' })
  const [submitError, setSubmitError] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    api.get<Student[]>(`/students?${params}`).then(({ data }) => {
      setStudents(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [search])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError(null)
    try {
      await api.post('/students', form)
      setForm({ student_id: '', full_name: '', email: '' })
      setShowForm(false)
      load()
    } catch (err: unknown) {
      const d = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: string } } }).response?.data
        : null
      setSubmitError(d?.error ?? 'Failed to create student')
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Students</h1>
        <div className={styles.actions}>
          <input
            type="search"
            placeholder="Search…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={styles.search}
          />
          <button type="button" onClick={() => setShowForm(true)} className={styles.btnPrimary}>
            Add Student
          </button>
        </div>
      </div>

      {showForm && (
        <div className={styles.modal}>
          <div className={styles.formCard}>
            <h2>New Student</h2>
            <form onSubmit={handleCreate}>
              {submitError && <div className={styles.error}>{submitError}</div>}
              <label>
                Student ID *
                <input
                  value={form.student_id}
                  onChange={(e) => setForm((f) => ({ ...f, student_id: e.target.value }))}
                  required
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
                Email
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                />
              </label>
              <div className={styles.formActions}>
                <button type="button" onClick={() => setShowForm(false)}>Cancel</button>
                <button type="submit" className={styles.btnPrimary}>Create</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <p className={styles.muted}>Loading…</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Face</th>
            </tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id}>
                <td><code>{s.student_id}</code></td>
                <td>{s.full_name}</td>
                <td>{s.email ?? '—'}</td>
                <td>{s.has_face_encoding ? '✓' : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && students.length === 0 && (
        <p className={styles.muted}>No students found.</p>
      )}
    </div>
  )
}
