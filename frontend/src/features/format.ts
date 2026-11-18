import type { Assessment, LessonStatus, NotificationKind, RequestStatus, Target } from '../app/contracts'

const timeZone = 'Europe/Moscow'
const formatDate = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'long', timeZone })
const formatTime = new Intl.DateTimeFormat('ru-RU', { timeStyle: 'short', timeZone })
const formatDay = new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long', timeZone })
const formDay = new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: '2-digit', day: '2-digit', timeZone })

export function dayKey(value = new Date()) {
  return formDay.format(value)
}

export function dateLabel(value: string) {
  return formatDate.format(new Date(value))
}

export function dayLabel(value: string) {
  return formatDay.format(new Date(value))
}

export function timeLabel(value: string) {
  return formatTime.format(new Date(value))
}

export function targetHref(target: Target) {
  const id = encodeURIComponent(target.id)
  switch (target.type) {
    case 'schedule': return '/app/schedule?lesson=' + id + '#lesson-' + id
    case 'exam': return '/app/study?tab=exams#exam-' + id
    case 'request': return '/app/requests/' + id
  }
}

export const requestStatus: Record<RequestStatus, string> = {
  new: 'Новая', in_progress: 'В работе', ready: 'Готова', rejected: 'Отклонена',
}
export const lessonStatus: Record<LessonStatus, string> = {
  scheduled: 'По расписанию', moved: 'Перенесено', cancelled: 'Отменено',
}
export const assessmentLabel: Record<Assessment, string> = { exam: 'Экзамен', pass_fail: 'Зачёт' }
export const notificationLabel: Record<NotificationKind, string> = {
  schedule_change: 'Расписание', application_status: 'Заявки', deadline: 'Сессия', announcement: 'Объявления',
}
export const fieldLabels: Record<string, string> = {
  purpose: 'Цель', delivery_method: 'Получение', topic: 'Тема',
}
export const optionLabels: Record<string, string> = {
  work: 'Для работы или практики', bank: 'Для банка', other: 'Другое',
  digital: 'В электронном виде', pickup: 'Забрать лично', study: 'Учёба', documents: 'Документы',
}
