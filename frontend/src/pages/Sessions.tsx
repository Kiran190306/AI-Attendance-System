import { useEffect, useState } from 'react'
import { api, type AttendanceSession } from '../services/api'
import { format } from 'date-fns'
import styles from './Sessions.module.css'

export default function Sessions() {
  const [sessions, setSessions] = useState<AttendanceSession[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', session_date: format(new Date(), 'yyyy-MM-dd') })
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    api.get<AttendanceSession[]>('/attendance/sessions').then(({ data }) => {
      setSessions(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const createSession = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/attendance/sessions', form)
      setShowForm(false)
      setForm({ name: '', session_date: format(new Date(), 'yyyy-MM-dd') })
      load()
    } catch (err: unknown) {
      const d = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: string } } }).response?.data
        : null
      setError(d?.error ?? 'Failed to create session')
    }
  }

  const startSession = async (id: number) => {
    try {
      await api.post(`/attendance/sessions/${id}/start`)
      load()
    } catch {
      // ignore
    }
  }

  const endSession = async (id: number) => {
    try {
      await api.post(`/attendance/sessions/${id}/end`)
      load()
    } catch {
      // ignore
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Attendance Sessions</h1>
        <button type="button" onClick={() => setShowForm(true)} className={styles.btnPrimary}>
          New Session
        </button>
      </div>

      {showForm && (
        <div className={styles.modal}>
          <div className={styles.formCard}>
            <h2>New Session</h2>
            <form onSubmit={createSession}>
              {error && <div className={styles.error}>{error}</div>}
              <label>
                Name *
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Math 101 - Morning"
                  required
                />
              </label>
              <label>
                Date *
                <input
                  type="date"
                  value={form.session_date}
                  onChange={(e) => setForm((f) => ({ ...f, session_date: e.target.value }))}
                  required
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
        <div className={styles.grid}>
          {sessions.map((s) => (
            <div key={s.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <strong>{s.name}</strong>
                <span className={styles.date}>{format(new Date(s.session_date), 'MMM d, yyyy')}</span>
              </div>
              <div className={styles.cardMeta}>
                {s.started_at ? (
                  <span className={styles.badge}>Started</span>
                ) : (
                  <span className={styles.badgeMuted}>Not started</span>
                )}
                {s.ended_at && <span className={styles.badge}>Ended</span>}
              </div>
              <div className={styles.cardActions}>
                {!s.started_at && (
                  <button type="button" onClick={() => startSession(s.id)} className={styles.btnSmall}>
                    Start
                  </button>
                )}
                {s.started_at && !s.ended_at && (
                  <button type="button" onClick={() => endSession(s.id)} className={styles.btnSmall}>
                    End
                  </button>
                )}
                <a href={`/live?session=${s.id}`} className={styles.btnSmall}>
                  Mark
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
      {!loading && sessions.length === 0 && (
        <p className={styles.muted}>No sessions yet. Create one to start taking attendance.</p>
      )}
    </div>
  )
}
