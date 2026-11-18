import type {
  Dashboard, Exam, Lesson, Me, NotificationItem, Page, RequestDetails, RequestType, Study,
} from '../../src/app/contracts'

export const day = '2026-11-18'
export const startsAt = '2026-11-18T10:45:00+03:00'
const earlier = '2026-11-18T09:00:00+03:00'
const endsAt = '2026-11-18T12:15:00+03:00'

export const me: Me = {
  user: { id: 'student-a', username: 'demo.alina', role: 'student' },
  student: {
    full_name: 'Алина Тестова', faculty: 'Факультет цифровых технологий',
    program: 'Информатика', course_year: 2, group: { id: 'group-a', name: 'ИВТ-21' },
  },
}

export const lesson: Lesson = {
  id: 'lesson-a', course: { id: 'course-a', title: 'Алгоритмы' }, lesson_type: 'practice',
  starts_at: startsAt, ends_at: endsAt, room: 'Б-204',
  instructor: { display_name: 'Юлия Вымышленная' }, status: 'moved',
  change: {
    kind: 'moved', changed_at: earlier,
    before: { starts_at: earlier, ends_at: startsAt, room: 'А-101' },
    after: { starts_at: startsAt, ends_at: endsAt, room: 'Б-204' },
  },
}

export const study: Study = {
  summary: { total: 2, passed: 1, pending: 1 },
  courses: [
    {
      offering_id: 'offering-b', title: 'Базы данных', assessment_type: 'pass_fail',
      result: 'passed', final_grade: 'зачёт',
      grades: [{ id: 'grade-b', kind: 'final', value: 'зачёт', graded_at: earlier }],
    },
    {
      offering_id: 'offering-a', title: 'Алгоритмы', assessment_type: 'exam',
      result: 'pending', final_grade: null, grades: [],
    },
  ],
}

export const exams: Exam[] = [{
  id: 'exam-a', offering_id: 'offering-a', course_title: 'Алгоритмы',
  type: 'exam', scheduled_at: '2026-11-20T10:00:00+03:00', room: 'Б-204', status: 'planned', grade: null,
}]

export const dashboard: Dashboard = {
  date: day, timezone: 'Europe/Moscow', greeting_name: 'Алина',
  next_lesson: { id: lesson.id, title: lesson.course.title, starts_at: startsAt, room: lesson.room, status: 'moved' },
  next_exam: { id: exams[0].id, course_title: exams[0].course_title, scheduled_at: exams[0].scheduled_at },
  study: study.summary, active_requests_count: 1, unread_notifications_count: 1,
  focus: [{
    kind: 'schedule_change', title: 'Изменилось расписание', description: 'Перенос практики',
    target: { type: 'schedule', id: lesson.id }, priority: 'high',
  }],
}

export const certificate: RequestType = {
  code: 'STUDY_CERTIFICATE', title: 'Справка об обучении', description: 'Демонстрационный запрос',
  comment_required: false, comment_max_length: 500,
  fields_schema: {
    type: 'object', additionalProperties: false, required: ['purpose', 'delivery_method'],
    properties: {
      purpose: { type: 'string', title: 'Для чего нужна справка', enum: ['work', 'bank', 'other'] },
      delivery_method: { type: 'string', title: 'Способ получения', enum: ['digital', 'pickup'] },
    },
  },
}

export const statement: RequestType = {
  code: 'DEAN_OFFICE_STATEMENT', title: 'Заявление в деканат', description: 'Обращение по учебному вопросу',
  comment_required: true, comment_max_length: 1000,
  fields_schema: {
    type: 'object', additionalProperties: false, required: ['topic'],
    properties: { topic: { type: 'string', title: 'Тема обращения', enum: ['study', 'documents', 'other'] } },
  },
}

export const request: RequestDetails = {
  id: 'request-a', type_code: certificate.code, type_title: certificate.title,
  status: 'new', comment: 'Для практики', fields: { purpose: 'work', delivery_method: 'digital' },
  created_at: earlier, updated_at: startsAt, history: [{
    id: 'event-a', from_status: null, to_status: 'new', note: 'Заявка создана', created_at: earlier,
  }],
}

export const notification: NotificationItem = {
  id: 'notice-a', kind: 'schedule_change', title: 'Пара перенесена', body: 'Новое время 10:45',
  created_at: earlier, read_at: null, target: { type: 'schedule', id: lesson.id },
}

export function page<T>(items: T[], current = 1, total = items.length, hasNext = false): Page<T> {
  return { items, pagination: { page: current, page_size: 20, total, has_next: hasNext } }
}
