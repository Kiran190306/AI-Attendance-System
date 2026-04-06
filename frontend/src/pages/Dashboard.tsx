import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type SessionSummary } from '../services/api'
import { format } from 'date-fns'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<SessionSummary[]>('/reports/sessions?limit=5').then(({ data }) => {
      setSessions(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Dashboard</h1>
      <p className={styles.subtitle}>Overview of recent attendance sessions</p>

      <div className={styles.quickLinks}>
        <Link to="/sessions" className={styles.card}>
          <span className={styles.cardIcon}>📋</span>
          <span>Manage Sessions</span>
        </Link>
        <Link to="/live" className={styles.card}>
          <span className={styles.cardIcon}>📷</span>
          <span>Live Face Mark</span>
        </Link>
        <Link to="/reports" className={styles.card}>
          <span className={styles.cardIcon}>📊</span>
          <span>Reports</span>
        </Link>
      </div>

      <section className={styles.section}>
        <h2>Recent Sessions</h2>
        {loading ? (
          <p className={styles.muted}>Loading…</p>
        ) : sessions.length === 0 ? (
          <p className={styles.muted}>No sessions yet. Create one from Sessions.</p>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Session</th>
                <th>Date</th>
                <th>Present</th>
                <th>Rate</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.session_id}>
                  <td>{s.session_name}</td>
                  <td>{format(new Date(s.session_date), 'MMM d, yyyy')}</td>
                  <td>{s.present_count} / {s.total_students}</td>
                  <td><span className={styles.rate}>{s.attendance_rate}%</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
