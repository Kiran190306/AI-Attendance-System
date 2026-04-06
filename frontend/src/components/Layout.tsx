import { Outlet, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Layout.module.css'

export default function Layout() {
  const { user, logout, isAdmin } = useAuth()

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <span className={styles.brandIcon}>◉</span>
          <span>AI Attendance</span>
        </div>
        <nav className={styles.nav}>
          <NavLink end to="/" className={({ isActive }) => (isActive ? styles.navActive : '')}>
            Dashboard
          </NavLink>
          <NavLink to="/students" className={({ isActive }) => (isActive ? styles.navActive : '')}>
            Students
          </NavLink>
          <NavLink to="/sessions" className={({ isActive }) => (isActive ? styles.navActive : '')}>
            Sessions
          </NavLink>
          <NavLink to="/live" className={({ isActive }) => (isActive ? styles.navActive : '')}>
            Live Mark
          </NavLink>
          <NavLink to="/reports" className={({ isActive }) => (isActive ? styles.navActive : '')}>
            Reports
          </NavLink>
          <NavLink to="/records" className={({ isActive }) => (isActive ? styles.navActive : '')}>
            Records
          </NavLink>
          {isAdmin && (
            <NavLink to="/users/new" className={({ isActive }) => (isActive ? styles.navActive : '')}>
              Add User
            </NavLink>
          )}
        </nav>
        <div className={styles.user}>
          <span className={styles.userName}>{user?.full_name}</span>
          <span className={styles.userRole}>{user?.role}</span>
          <button type="button" onClick={logout} className={styles.logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
