export type Profile = {
  full_name: string
  faculty: string
  program: string
  course_year: number
  group: { id: string; name: string }
}

export type User = { id: string; username: string; role: 'student' | 'staff' }
export type Me = { user: User; student: Profile | null }
export type LoginResult = { user: User; session: { expires_at: string } }
export type Target = { type: 'schedule' | 'exam' | 'request'; id: string }
export type LessonStatus = 'scheduled' | 'moved' | 'cancelled'
export type LessonSlot = { starts_at: string; ends_at: string; room: string }
export type Lesson = LessonSlot & {
  id: string
  course: { id: string; title: string }
  lesson_type: 'lecture' | 'practice' | 'lab' | 'seminar'
  instructor: { display_name: string }
  status: LessonStatus
  change: {
    kind: 'moved' | 'cancelled'
    changed_at: string
    before: LessonSlot
    after: LessonSlot | null
  } | null
}
export type Schedule = {
  view: 'today' | 'week'
  timezone: 'Europe/Moscow'
  range: { start_date: string; end_date: string }
  items: Lesson[]
}

export type Summary = { passed: number; total: number; pending: number }
export type Assessment = 'exam' | 'pass_fail'
export type CourseResult = {
  offering_id: string
  title: string
  assessment_type: Assessment
  result: 'pending' | 'passed' | 'failed'
  final_grade: string | null
  grades: { id: string; kind: 'current' | 'final'; value: string; graded_at: string }[]
}
export type Study = { summary: Summary; courses: CourseResult[] }
export type Exam = {
  id: string
  offering_id: string
  course_title: string
  type: Assessment
  scheduled_at: string
  room: string
  status: 'planned' | 'passed' | 'failed'
  grade: string | null
}

export type RequestStatus = 'new' | 'in_progress' | 'ready' | 'rejected'
export type RequestType = {
  code: string
  title: string
  description: string
  fields_schema: {
    type: 'object'
    properties: Record<string, { type: 'string'; title: string; enum: string[] }>
    required: string[]
    additionalProperties: false
  }
  comment_required: boolean
  comment_max_length: number
}
export type RequestInput = { type_code: string; fields: Record<string, string>; comment: string | null }
export type RequestItem = {
  id: string
  type_code: string
  type_title: string
  status: RequestStatus
  created_at: string
  updated_at: string
}
export type RequestDetails = RequestItem & {
  fields: Record<string, string>
  comment: string | null
  history: {
    id: string
    from_status: RequestStatus | null
    to_status: RequestStatus
    note: string
    created_at: string
  }[]
}
export type Pagination = { page: number; page_size: number; total: number; has_next: boolean }
export type Page<T> = { items: T[]; pagination: Pagination }
export type NotificationKind = 'schedule_change' | 'application_status' | 'deadline' | 'announcement'
export type NotificationItem = {
  id: string
  kind: NotificationKind
  title: string
  body: string
  created_at: string
  read_at: string | null
  target: Target | null
}
export type Notifications = Page<NotificationItem> & { unread_count: number }
export type Dashboard = {
  date: string
  timezone: 'Europe/Moscow'
  greeting_name: string
  next_lesson: { id: string; title: string; starts_at: string; room: string; status: LessonStatus } | null
  study: Summary
  active_requests_count: number
  unread_notifications_count: number
  next_exam: { id: string; course_title: string; scheduled_at: string } | null
  focus: { kind: NotificationKind; title: string; description: string; target: Target; priority: 'high' | 'normal' }[]
}
