import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, type AttendanceSession, type AttendanceMark } from '../services/api'
import styles from './LiveAttendance.module.css'

const videoConstraints = { width: 640, height: 480, facingMode: 'user' }

export default function LiveAttendance() {
  const [searchParams] = useSearchParams()
  const sessionIdParam = searchParams.get('session')
  const [sessions, setSessions] = useState<AttendanceSession[]>([])
  const [sessionId, setSessionId] = useState<number | null>(sessionIdParam ? parseInt(sessionIdParam, 10) : null)
  const [marks, setMarks] = useState<AttendanceMark[]>([])
  const [loading, setLoading] = useState(true)
  const [capturing, setCapturing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [faceAvailable, setFaceAvailable] = useState<boolean | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  useEffect(() => {
    api.get<AttendanceSession[]>('/attendance/sessions').then(({ data }) => setSessions(data))
    api.get<{ available: boolean }>('/face/status').then(({ data }) => setFaceAvailable(data.available))
  }, [])

  useEffect(() => {
    if (!sessionId) {
      setLoading(false)
      return
    }
    setLoading(true)
    api.get<AttendanceMark[]>(`/attendance/sessions/${sessionId}/marks`).then(({ data }) => {
      setMarks(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [sessionId])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: videoConstraints })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream
      setCapturing(true)
    } catch {
      setMessage('Camera access denied or not available.')
    }
  }

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setCapturing(false)
  }

  const captureAndMark = async () => {
    if (!sessionId || !videoRef.current || !faceAvailable) {
      setMessage('Select a session and ensure face recognition is available.')
      return
    }
    const video = videoRef.current
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
    const base64 = dataUrl.split(',')[1]
    if (!base64) {
      setMessage('Failed to capture image.')
      return
    }
    setMessage('Recognizing…')
    try {
      await api.post('/face/mark', { session_id: sessionId, image_data: base64 })
      setMessage('Marked successfully!')
      const { data } = await api.get<AttendanceMark[]>(`/attendance/sessions/${sessionId}/marks`)
      setMarks(data)
      setTimeout(() => setMessage(null), 2000)
    } catch (err: unknown) {
      const d = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: string } } }).response?.data
        : null
      setMessage(d?.error ?? 'Recognition failed.')
    }
  }

  return (
    <div className={styles.page}>
      <h1>Live Attendance (Face)</h1>
      <p className={styles.subtitle}>
        Select a session, start camera, and mark attendance by face.
      </p>

      <div className={styles.toolbar}>
        <label>
          Session
          <select
            value={sessionId ?? ''}
            onChange={(e) => setSessionId(e.target.value ? parseInt(e.target.value, 10) : null)}
          >
            <option value="">— Select —</option>
            {sessions.filter((s) => s.started_at && !s.ended_at).map((s) => (
              <option key={s.id} value={s.id}>{s.name} ({new Date(s.session_date).toLocaleDateString()})</option>
            ))}
          </select>
        </label>
        {faceAvailable === false && (
          <span className={styles.warn}>Face recognition is not available on the server.</span>
        )}
      </div>

      <div className={styles.main}>
        <div className={styles.cameraSection}>
          <div className={styles.videoWrap}>
            {!capturing ? (
              <div className={styles.placeholder}>Camera off</div>
            ) : (
              <video ref={videoRef} autoPlay playsInline muted className={styles.video} />
            )}
          </div>
          <div className={styles.cameraActions}>
            {!capturing ? (
              <button type="button" onClick={startCamera} className={styles.btnPrimary}>
                Start camera
              </button>
            ) : (
              <>
                <button type="button" onClick={captureAndMark} className={styles.btnPrimary} disabled={!sessionId}>
                  Mark by face
                </button>
                <button type="button" onClick={stopCamera}>Stop camera</button>
              </>
            )}
          </div>
          {message && <p className={styles.message}>{message}</p>}
        </div>

        <div className={styles.marksSection}>
          <h2>Marked ({marks.length})</h2>
          {loading ? (
            <p className={styles.muted}>Loading…</p>
          ) : (
            <ul className={styles.marksList}>
              {marks.map((m) => (
                <li key={m.id}>
                  <span className={styles.markName}>{m.student_name ?? `Student #${m.student_id}`}</span>
                  <span className={styles.markRoll}>{m.student_roll}</span>
                  {m.marked_by_face && <span className={styles.faceBadge}>face</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
