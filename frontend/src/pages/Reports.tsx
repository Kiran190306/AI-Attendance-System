import { useEffect, useState } from 'react'
import { api, type DailyReport, type SessionSummary, type StudentAttendanceSummary } from '../services/api'
import { format } from 'date-fns'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import styles from './Reports.module.css'

type Tab = 'daily' | 'sessions' | 'students'

export default function Reports() {
  const [tab, setTab] = useState<Tab>('daily')
  const [daily, setDaily] = useState<DailyReport[]>([])
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [students, setStudents] = useState<StudentAttendanceSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    if (tab === 'daily') {
      api.get<DailyReport[]>('/reports/daily?days=14').then(({ data }) => {
        setDaily(data)
        setLoading(false)
      }).catch(() => setLoading(false))
    } else if (tab === 'sessions') {
      api.get<SessionSummary[]>('/reports/sessions?limit=20').then(({ data }) => {
        setSessions(data)
        setLoading(false)
      }).catch(() => setLoading(false))
    } else {
      api.get<StudentAttendanceSummary[]>('/reports/students?limit=50').then(({ data }) => {
        setStudents(data)
        setLoading(false)
      }).catch(() => setLoading(false))
    }
  }, [tab])

  const chartData = daily.slice(0, 14).reverse().map((d) => ({
    date: format(new Date(d.date), 'MM/dd'),
    rate: d.attendance_rate,
    present: d.total_present,
  }))

  return (
    <div className={styles.page}>
      <h1>Reports & Analytics</h1>
      <p className={styles.subtitle}>Attendance overview and trends</p>

      <div className={styles.tabs}>
        {(['daily', 'sessions', 'students'] as const).map((t) => (
          <button
            key={t}
            type="button"
            className={tab === t ? styles.tabActive : ''}
            onClick={() => setTab(t)}
          >
            {t === 'daily' && 'Daily'}
            {t === 'sessions' && 'By Session'}
            {t === 'students' && 'By Student'}
          </button>
        ))}
      </div>

      {tab === 'daily' && (
        <>
          <div className={styles.chartWrap}>
            <h2>Attendance rate (last 14 days)</h2>
            {loading ? (
              <p className={styles.muted}>Loading…</p>
            ) : chartData.length === 0 ? (
              <p className={styles.muted}>No data</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
                    labelStyle={{ color: 'var(--text)' }}
                  />
                  <Bar dataKey="rate" fill="var(--accent)" name="Rate %" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
          {!loading && daily.length > 0 && (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Sessions</th>
                  <th>Present</th>
                  <th>Absent</th>
                  <th>Rate</th>
                </tr>
              </thead>
              <tbody>
                {daily.map((r) => (
                  <tr key={r.date}>
                    <td>{format(new Date(r.date), 'MMM d, yyyy')}</td>
                    <td>{r.total_sessions}</td>
                    <td>{r.total_present}</td>
                    <td>{r.total_absent}</td>
                    <td><span className={styles.rate}>{r.attendance_rate}%</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {tab === 'sessions' && (
        <>
          {loading ? (
            <p className={styles.muted}>Loading…</p>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Session</th>
                  <th>Date</th>
                  <th>Present</th>
                  <th>Absent</th>
                  <th>Total</th>
                  <th>Rate</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.session_id}>
                    <td>{s.session_name}</td>
                    <td>{format(new Date(s.session_date), 'MMM d, yyyy')}</td>
                    <td>{s.present_count}</td>
                    <td>{s.absent_count}</td>
                    <td>{s.total_students}</td>
                    <td><span className={styles.rate}>{s.attendance_rate}%</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!loading && sessions.length === 0 && <p className={styles.muted}>No sessions.</p>}
        </>
      )}

      {tab === 'students' && (
        <>
          {loading ? (
            <p className={styles.muted}>Loading…</p>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Roll</th>
                  <th>Name</th>
                  <th>Present</th>
                  <th>Absent</th>
                  <th>Sessions</th>
                  <th>%</th>
                </tr>
              </thead>
              <tbody>
                {students.map((s) => (
                  <tr key={s.student_id}>
                    <td><code>{s.student_roll}</code></td>
                    <td>{s.student_name}</td>
                    <td>{s.total_present}</td>
                    <td>{s.total_absent}</td>
                    <td>{s.total_sessions}</td>
                    <td><span className={styles.rate}>{s.attendance_percentage}%</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!loading && students.length === 0 && <p className={styles.muted}>No data.</p>}
        </>
      )}
    </div>
  )
}
