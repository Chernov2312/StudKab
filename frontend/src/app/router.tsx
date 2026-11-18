import { useMutation, useQuery } from '@tanstack/react-query'
import { Bell, CalendarDays, ChevronRight, FileText, GraduationCap, House, Info, LogOut, Menu, UserRound } from 'lucide-react'
import { Link, Navigate, NavLink, Outlet, Route, Routes, useNavigate } from 'react-router-dom'
import { Brand, ErrorState, Heading, Loading, notice } from '../components/ui'
import { DashboardPage } from '../pages/dashboard'
import { LoginPage } from '../pages/login'
import { NotificationsPage } from '../pages/notifications'
import { ProfilePage } from '../pages/profile'
import { NewRequestPage, RequestDetailsPage, RequestsPage } from '../pages/requests'
import { SchedulePage } from '../pages/schedule'
import { StudyPage } from '../pages/study'
import { mutate, queryClient } from './api'
import type { Me } from './contracts'
import { dashboardQuery, sessionQuery } from './queries'

const mainLinks = [
  { to: '/app', label: 'Главная', icon: House, end: true },
  { to: '/app/schedule', label: 'Расписание', icon: CalendarDays },
  { to: '/app/study', label: 'Учёба', icon: GraduationCap },
  { to: '/app/requests', label: 'Заявки', icon: FileText },
]
const secondaryLinks = [
  { to: '/app/notifications', label: 'Уведомления', icon: Bell },
  { to: '/app/profile', label: 'Профиль', icon: UserRound },
  { to: '/app/about', label: 'О проекте', icon: Info },
]

function LogoutButton() {
  const navigate = useNavigate()
  const logout = useMutation({
    mutationFn: () => mutate<void>('/auth/logout'),
    onSuccess: async () => {
      await queryClient.cancelQueries()
      queryClient.setQueryData(sessionQuery.queryKey, null)
      queryClient.removeQueries({ predicate: query => query.queryKey[0] !== sessionQuery.queryKey[0] })
      queryClient.getMutationCache().clear()
      navigate('/login', { replace: true })
    }
  })
  return <div>
    <button className="button secondary" onClick={() => logout.mutate()} disabled={logout.isPending}>
      <LogOut size={17} aria-hidden="true" />{logout.isPending ? 'Выходим…' : 'Выйти'}
    </button>
    {logout.error && <p className="form-error" role="alert">{logout.error.message || 'Не удалось выйти. Повторите попытку.'}</p>}
  </div>
}

function Shell({ session }: { session: Me }) {
  const count = useQuery(dashboardQuery).data?.unread_notifications_count ?? 0
  const name = session.student?.full_name ?? session.user.username
  return <div className="workspace">
    <a className="skip-link" href="#content">Перейти к содержимому</a>
    <aside className="sidebar">
      <Link className="brand-link" to="/app"><Brand /></Link>
      <nav aria-label="Разделы кабинета">
        {[...mainLinks, ...secondaryLinks].map(({ to, label, icon: Icon, ...props }) =>
          <NavLink key={to} to={to} {...props}><Icon size={20} aria-hidden="true" /><span>{label}</span></NavLink>)}
      </nav>
      <div className="sidebar-account">
        <Link to="/app/profile" className="account"><span className="avatar" aria-hidden="true">{name.split(' ').slice(0, 2).map(part => part[0]).join('')}</span>
          <span>{name}<small>{session.student?.group.name}</small></span>
        </Link>
        <LogoutButton />
      </div>
    </aside>
    <div className="workspace-body">
      <header className="topbar">
        <div className="topbar-inner">
          <Link className="mobile-brand brand-link" to="/app"><Brand /></Link>
          <span className="topbar-label">Конкурсный прототип</span>
          <Link className="icon-button bell" to="/app/notifications" aria-label={count ? 'Уведомления, непрочитанных: ' + count : 'Уведомления'}>
            <Bell size={21} aria-hidden="true" />{count > 0 && <span aria-hidden="true">{count > 99 ? '99+' : count}</span>}
          </Link>
        </div>
      </header>
      <main className="content" id="content" tabIndex={-1}><Outlet /></main>
      <footer>{notice}</footer>
    </div>
    <nav className="bottom-nav" aria-label="Мобильная навигация">
      {[...mainLinks, { to: '/app/more', label: 'Ещё', icon: Menu }].map(({ to, label, icon: Icon, ...props }) =>
        <NavLink to={to} key={to} {...props}><Icon size={21} aria-hidden="true" /><span>{label}</span></NavLink>)}
    </nav>
  </div>
}

function More() {
  return <><Heading title="Ещё" /><div className="stack">
    {secondaryLinks.map(({ to, label, icon: Icon }) =>
      <Link className="card list-link" to={to} key={to}><Icon size={20} aria-hidden="true" />{label}<ChevronRight size={19} aria-hidden="true" /></Link>)}
    <LogoutButton />
  </div></>
}

function About() {
  return <><Heading title="О проекте" /><article className="card">
    <p className="strong">{notice}</p>
    <p>«Пульс» объединяет расписание, оценки, сессию и заявки в учебном кабинете. Демонстрационные заявки показывают, как может работать обращение в деканат.</p>
  </article></>
}

export function App() {
  const session = useQuery(sessionQuery)
  if (session.isPending) return <Loading label="Проверяем вход…" />
  if (session.error) return <ErrorState error={session.error} retry={session.refetch} />
  const active = session.data
  return <Routes>
    <Route path="/" element={<Navigate to={active ? '/app' : '/login'} replace />} />
    <Route path="/login" element={active ? <Navigate to="/app" replace /> : <LoginPage />} />
    <Route path="/profile" element={<Navigate to="/app/profile" replace />} />
    <Route path="/app" element={active ? <Shell session={active} /> : <Navigate to="/login" replace />}>
      <Route index element={<DashboardPage />} />
      <Route path="schedule" element={<SchedulePage />} />
      <Route path="study" element={<StudyPage />} />
      <Route path="requests" element={<RequestsPage />} />
      <Route path="requests/new" element={<NewRequestPage />} />
      <Route path="requests/:requestId" element={<RequestDetailsPage />} />
      <Route path="notifications" element={<NotificationsPage />} />
      <Route path="profile" element={<ProfilePage />} />
      <Route path="more" element={<More />} />
      <Route path="about" element={<About />} />
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
}
