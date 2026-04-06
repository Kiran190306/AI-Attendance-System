import { useState, useCallback } from 'react'
import { api, type AttendanceRecord, type MonthlyStat } from '../services/api'
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
import styles from './RecordsDashboard.module.css'

const today = format(new Date(), 'yyyy-MM-dd')
const thisMonth = new Date().getMonth() + 1
const thisYear = new Date().getFullYear()

export default function RecordsDashboard() {
  const [records, setRecords] = useState<AttendanceRecord[]>([])
  const [fromDate, setFromDate] = useState(today)
  const [toDate, setToDate] = useState(today)
  const [recordsLoading, setRecordsLoading] = useState(false)

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<AttendanceRecord[]>([])
  const [searchLoading, setSearchLoading] = useState(false)

  const [monthStats, setMonthStats] = useState<MonthlyStat[]>([])
  const [chartYear, setChartYear] = useState(thisYear)
  const [chartMonth, setChartMonth] = useState(thisMonth)
  const [chartLoading, setChartLoading] = useState(false)

  const loadRecords = useCallback(() => {
    setRecordsLoading(true)
    api
      .get<AttendanceRecord[]>('/records/records', {
        params: { from_date: fromDate, to_date: toDate, limit: 200 },
      })
      .then(({ data }) => {
        setRecords(data)
        setRecordsLoading(false)
      })
      .catch(() => setRecordsLoading(false))
  }, [fromDate, toDate])

  const searchStudent = useCallback(() => {
    if (!searchQuery.trim()) return
    setSearchLoading(true)
    api
      .get<AttendanceRecord[]>('/records/student', { params: { q: searchQuery.trim(), limit: 100 } })
      .then(({ data }) => {
        setSearchResults(data)
        setSearchLoading(false)
      })
      .catch(() => setSearchLoading(false))
  }, [searchQuery])

  const loadMonthlyStats = useCallback(() => {
    setChartLoading(true)
    api
      .get<MonthlyStat[]>('/records/monthly-stats', { params: { year: chartYear, month: chartMonth } })
      .then(({ data }) => {
        setMonthStats(data)
        setChartLoading(false)
      })
      .catch(() => setChartLoading(false))
  }, [chartYear, chartMonth])

  const chartData = monthStats.map((s) => ({
    name: s.student_name.length > 12 ? s.student_name.slice(0, 11) + '…' : s.student_name,
    fullName: s.student_name,
    percentage: s.percentage,
    days: `${s.days_present}/${s.total_days}`,
  }))

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Attendance Dashboard</h1>
      <p className={styles.subtitle}>View records, search by student, and see monthly attendance %</p>

      {/* View records */}
      <section className={styles.section}>
        <h2>View records</h2>
        <div className={styles.filters}>
          <label>
            <span>From</span>
            <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          </label>
          <label>
            <span>To</span>
            <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </label>
          <button type="button" onClick={loadRecords} className={styles.btnPrimary} disabled={recordsLoading}>
            {recordsLoading ? 'Loading…' : 'Load'}
          </button>
        </div>
        <div className={styles.tableWrap}>
          {records.length === 0 && !recordsLoading ? (
            <p className={styles.muted}>Select dates and click Load, or load once to see data.</p>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Student</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>{r.date}</td>
                    <td>{r.time}</td>
                    <td>{r.student_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {/* Search student */}
      <section className={styles.section}>
        <h2>Search student attendance</h2>
        <div className={styles.searchRow}>
          <input
            type="search"
            placeholder="Enter student name…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && searchStudent()}
            className={styles.searchInput}
          />
          <button type="button" onClick={searchStudent} className={styles.btnPrimary} disabled={searchLoading}>
            {searchLoading ? 'Searching…' : 'Search'}
          </button>
        </div>
        {searchResults.length > 0 && (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Student</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((r) => (
                  <tr key={r.id}>
                    <td>{r.date}</td>
                    <td>{r.time}</td>
                    <td>{r.student_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {searchResults.length === 0 && searchLoading === false && searchQuery.trim() !== '' && (
          <p className={styles.muted}>No records found.</p>
        )}
      </section>

      {/* Monthly attendance % chart */}
      <section className={styles.section}>
        <h2>Monthly attendance percentage</h2>
        <div className={styles.filters}>
          <label>
            <span>Year</span>
            <select value={chartYear} onChange={(e) => setChartYear(Number(e.target.value))}>
              {[thisYear, thisYear - 1, thisYear - 2].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Month</span>
            <select value={chartMonth} onChange={(e) => setChartMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>{format(new Date(2000, m - 1), 'MMMM')}</option>
              ))}
            </select>
          </label>
          <button type="button" onClick={loadMonthlyStats} className={styles.btnPrimary} disabled={chartLoading}>
            {chartLoading ? 'Loading…' : 'Load chart'}
          </button>
        </div>
        <div className={styles.chartWrap}>
          {chartLoading ? (
            <p className={styles.muted}>Loading…</p>
          ) : chartData.length === 0 ? (
            <p className={styles.muted}>Select year/month and click Load chart.</p>
          ) : (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} angle={-25} textAnchor="end" />
                <YAxis stroke="var(--text-muted)" fontSize={12} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
                  labelStyle={{ color: 'var(--text)' }}
                  formatter={(value: number) => [`${value}%`, 'Attendance']}
                  labelFormatter={(_, payload) => payload[0]?.payload?.fullName ?? ''}
                />
                <Bar dataKey="percentage" fill="var(--accent)" name="%" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </section>
    </div>
  )
}
