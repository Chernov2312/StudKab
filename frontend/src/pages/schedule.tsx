import { useQuery } from '@tanstack/react-query'
import { CalendarDays, MapPin, UserRound } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../app/api'
import type { Lesson, LessonSlot, Schedule } from '../app/contracts'
import { AnchorCard, Badge, Empty, Heading, QueryView } from '../components/ui'
import { dateLabel, dayKey, dayLabel, lessonStatus, timeLabel } from '../features/format'

const lessonTypes = { lecture: 'Лекция', practice: 'Практика', lab: 'Лабораторная', seminar: 'Семинар' }
const slotLabel = (slot: LessonSlot) => dateLabel(slot.starts_at) + ', ' + timeLabel(slot.starts_at) + '–' + timeLabel(slot.ends_at) + ' · ауд. ' + slot.room

function LessonCard({ item }: { item: Lesson }) {
  return <AnchorCard id={'lesson-' + item.id}>
    <div className="list-heading"><div className="lesson-time">{timeLabel(item.starts_at)}–{timeLabel(item.ends_at)}</div>
      <Badge tone={item.status === 'moved' ? 'warm' : item.status === 'cancelled' ? 'red' : 'quiet'}>{lessonStatus[item.status]}</Badge></div>
    <h3>{item.course.title}</h3>
    <div className="meta"><span>{lessonTypes[item.lesson_type]}</span><span><MapPin size={16} aria-hidden="true" />{item.room}</span>
      <span><UserRound size={16} aria-hidden="true" />{item.instructor.display_name}</span></div>
    {item.change && <div className="lesson-change">
      <p><strong>Было</strong> {slotLabel(item.change.before)}</p>
      {item.change.after && <p><strong>Стало</strong> {slotLabel(item.change.after)}</p>}
      <small>Обновлено {dateLabel(item.change.changed_at)}, {timeLabel(item.change.changed_at)}</small>
    </div>}
  </AnchorCard>
}

export function SchedulePage() {
  const [params, setParams] = useSearchParams()
  const view = params.get('view') === 'week' ? 'week' : 'today'
  const lesson = params.get('lesson')
  const day = params.get('date') || ''
  const apiParams = new URLSearchParams({ view })
  if (lesson) apiParams.set('lesson_id', lesson)
  else if (day) apiParams.set('date', day)
  const query = useQuery({
    queryKey: ['schedule', apiParams.toString()],
    queryFn: ({ signal }) => api<Schedule>('/schedule?' + apiParams, { signal }),
  })
  return <>
    <Heading title="Расписание" description="Занятия и изменения вашей группы" />
    <div className="toolbar">
      <div className="switcher" role="group" aria-label="Период расписания">
        <button aria-pressed={view === 'today'} onClick={() => setParams({})}>Сегодня</button>
        <button aria-pressed={view === 'week'} onClick={() => setParams({ view: 'week', ...(day ? { date: day } : {}) })}>Неделя</button>
      </div>
      <label className="inline-field"><CalendarDays size={17} aria-hidden="true" /><span className="sr-only">Дата расписания</span>
        <input type="date" value={day || query.data?.range.start_date || dayKey()} onChange={event => setParams({ view, date: event.target.value })} />
      </label>
    </div>
    <QueryView query={query} back="/app/schedule">{data => {
      const groups = new Map<string, Lesson[]>()
      for (const item of data.items) {
        const key = dayKey(new Date(item.starts_at))
        const current = groups.get(key) ?? []
        current.push(item)
        groups.set(key, current)
      }
      return <div className="stack">
        {view === 'week' && <p className="section-caption">{dateLabel(data.range.start_date)} — {dateLabel(data.range.end_date)}</p>}
        {groups.size === 0 && <Empty title={view === 'today' ? (day && day !== dayKey() ? 'На эту дату занятий нет' : 'Сегодня нет занятий') : 'На этой неделе занятий нет'} />}
        {[...groups].map(([date, items]) => <section className="stack lesson-group" key={date}><h2>{dayLabel(date)}</h2>{items.map(item => <LessonCard key={item.id} item={item} />)}</section>)}
      </div>
    }}</QueryView>
  </>
}
