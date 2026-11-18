import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { api } from '../app/api'
import type { Exam, Study } from '../app/contracts'
import { AnchorCard, Badge, Empty, Heading, QueryView } from '../components/ui'
import { assessmentLabel, dateLabel, timeLabel } from '../features/format'

const labels = { pending: 'Ожидается', planned: 'Запланировано', passed: 'Сдано', failed: 'Не сдано' }

function StudyOverview() {
  const query = useQuery({ queryKey: ['study'], queryFn: ({ signal }) => api<Study>('/study', { signal }) })
  return <QueryView query={query}>{data => data.courses.length === 0 ? <Empty title="Дисциплин пока нет" /> :
    <div className="stack">
      <section className="card summary"><h2>Сдано {data.summary.passed} из {data.summary.total}</h2><p>Ожидают результата: {data.summary.pending}</p>
        <progress max={Math.max(data.summary.total, 1)} value={data.summary.passed} aria-label="Сданные дисциплины" /></section>
      {data.courses.map(course => <article className="card" key={course.offering_id}>
        <div className="list-heading"><h2>{course.title}</h2><Badge tone={course.result === 'passed' ? 'green' : course.result === 'failed' ? 'red' : 'quiet'}>{labels[course.result]}</Badge></div>
        <p>{assessmentLabel[course.assessment_type]}{course.final_grade !== null && ' · Итог: ' + course.final_grade}</p>
        {course.grades.length === 0 ? <p>Пока нет оценок</p> :
          <ul className="grade-list">{course.grades.map(grade => <li key={grade.id}><strong>{grade.value}</strong> <span>{grade.kind === 'final' ? 'Итоговая' : 'Текущая'} · {dateLabel(grade.graded_at)}</span></li>)}</ul>}
      </article>)}
    </div>
  }</QueryView>
}

function ExamList() {
  const query = useQuery({ queryKey: ['exams'], queryFn: ({ signal }) => api<{ items: Exam[] }>('/exams', { signal }) })
  return <QueryView query={query}>{({ items }) => items.length === 0 ? <Empty title="На этот учебный период событий нет" /> :
    <div className="stack">{items.map(exam => <AnchorCard key={exam.id} id={'exam-' + exam.id}>
      <div className="list-heading"><h2>{exam.course_title}</h2><Badge tone={exam.status === 'passed' ? 'green' : exam.status === 'failed' ? 'red' : 'quiet'}>{labels[exam.status]}</Badge></div>
      <p>{assessmentLabel[exam.type]} · {dateLabel(exam.scheduled_at)}, {timeLabel(exam.scheduled_at)} · ауд. {exam.room}</p>
      {exam.grade !== null && <p>Итог: {exam.grade}</p>}
    </AnchorCard>)}</div>
  }</QueryView>
}

export function StudyPage() {
  const [params, setParams] = useSearchParams()
  const exams = params.get('tab') === 'exams'
  return <><Heading title="Учёба" description="Успеваемость и события сессии" />
    <div className="toolbar"><div className="switcher" role="group" aria-label="Раздел учёбы">
      <button aria-pressed={!exams} onClick={() => setParams({})}>Оценки</button>
      <button aria-pressed={exams} onClick={() => setParams({ tab: 'exams' })}>Сессия</button>
    </div></div>
    {exams ? <ExamList /> : <StudyOverview />}
  </>
}
