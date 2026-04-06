import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || '/api/v1'

export const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      setAuthToken(null)
      localStorage.removeItem('attendance_token')
      localStorage.removeItem('attendance_user')
      if (!err.config?.url?.includes('/auth/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export interface Student {
  id: number
  student_id: string
  full_name: string
  email: string | null
  photo_url: string | null
  has_face_encoding: boolean
  is_active: boolean
  created_at: string
}

export interface AttendanceSession {
  id: number
  name: string
  session_date: string
  started_at: string | null
  ended_at: string | null
  created_by_id: number
  created_at: string
}

export interface AttendanceMark {
  id: number
  session_id: number
  student_id: number
  status: string
  marked_at: string
  marked_by_face: boolean
  notes: string | null
  student_name: string | null
  student_roll: string | null
}

export interface DailyReport {
  date: string
  total_sessions: number
  total_present: number
  total_absent: number
  total_late: number
  total_excused: number
  attendance_rate: number
}

export interface SessionSummary {
  session_id: number
  session_name: string
  session_date: string
  present_count: number
  absent_count: number
  late_count: number
  excused_count: number
  total_students: number
  attendance_rate: number
}

export interface StudentAttendanceSummary {
  student_id: number
  student_roll: string
  student_name: string
  total_present: number
  total_absent: number
  total_sessions: number
  attendance_percentage: number
}

/** Dashboard records (SQLite attendance_db) */
export interface AttendanceRecord {
  id: number
  student_name: string
  date: string
  time: string
  created_at: string
}

export interface MonthlyStat {
  student_name: string
  days_present: number
  total_days: number
  percentage: number
}
