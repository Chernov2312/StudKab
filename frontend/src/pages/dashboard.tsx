import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight, CalendarDays, Clock3, FileText, GraduationCap, Plus, Target as TargetIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { dashboardQuery } from '../app/queries'
import { Badge, Heading, QueryView, TextLink } from '../components/ui'
import { dateLabel, dayLabel, targetHref, timeLabel } from '../features/format'

export function DashboardPage() {
  const query = useQuery(dashboardQuery)
  return <QueryView query={query}>{data => <div className="dashboard">
    <Heading title="Мой день" description={dayLabel(data.date)}
      action={<Link className="button primary" to="/app/requests/new"><Plus size={19} aria-hidden="true" />Новая заявка</Link>} />
    <div className="dash-columns">
      <div className="stack">
        <section className="hero">
          <p className="hero-kicker"><Clock3 size={16} aria-hidden="true" /> Следующее занятие</p>
          <h2>Привет, {data.greeting_name}!</h2>
          {data.next_lesson ? <>
            <h3>{data.next_lesson.title}</h3>
            <p>{timeLabel(data.next_lesson.starts_at)} · ауд. {data.next_lesson.room}</p>
            <TextLink to={targetHref({ type: 'schedule', id: data.next_lesson.id })}>Открыть занятие</TextLink>
          </> : <><p>Сегодня больше нет занятий по расписанию.</p><TextLink to="/app/schedule">Открыть расписание</TextLink></>}
          <CalendarDays className="hero-symbol" size={125} strokeWidth={1} aria-hidden="true" />
        </section>
        <div className="mini-grid">
          <section className="card dashboard-card">
            <span className="tile-icon"><GraduationCap size={21} aria-hidden="true" /></span>
            <h2>Успеваемость</h2><p className="metric">{data.study.passed} <small>из {data.study.total}</small></p>
            <p>{data.study.total ? 'Дисциплин сдано' : 'Дисциплин пока нет'}</p>
            <TextLink to="/app/study">К оценкам</TextLink>
          </section>
          <section className="card dashboard-card">
            <span className="tile-icon amber"><FileText size={21} aria-hidden="true" /></span>
            <h2>Активные заявки</h2><p className="metric">{data.active_requests_count}</p>
            <p>{data.active_requests_count ? 'Новые и в работе' : 'Активных заявок нет'}</p>
            <TextLink to="/app/requests">Мои заявки</TextLink>
          </section>
        </div>
        <section className="card exam-preview">
          <span className="tile-icon"><CalendarDays size={21} aria-hidden="true" /></span>
          <div><h2>Ближайшая аттестация</h2>
            {data.next_exam ? <p>{data.next_exam.course_title} · {dateLabel(data.next_exam.scheduled_at)}, {timeLabel(data.next_exam.scheduled_at)}</p> : <p>Запланированных событий нет.</p>}
          </div>
          <TextLink to={data.next_exam ? targetHref({ type: 'exam', id: data.next_exam.id }) : '/app/study?tab=exams'}>Сессия</TextLink>
        </section>
      </div>
      <aside className="card focus-panel">
        <div className="focus-title"><span className="tile-icon"><TargetIcon size={19} aria-hidden="true" /></span><h2>В фокусе</h2></div>
        {data.focus.length === 0 && <p>На сегодня ничего срочного.</p>}
        {data.focus.map(item => <Link className="focus-item" to={targetHref(item.target)} key={item.kind + item.target.id}>
          <span className="focus-copy">{item.priority === 'high' && <Badge tone="warm">Важно</Badge>}
            <strong>{item.title}</strong><span>{item.description}</span>
          </span><ArrowUpRight size={18} aria-hidden="true" />
        </Link>)}
        <TextLink to="/app/notifications">Уведомления{data.unread_notifications_count > 0 ? ' · ' + data.unread_notifications_count : ''}</TextLink>
      </aside>
    </div>
  </div>}</QueryView>
}
