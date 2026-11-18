import { describe, expect, it } from 'vitest'
import { dayKey, targetHref, timeLabel } from '../../src/features/format'

describe('Московское время', () => {
  it('переключает учебный день в полночь Москвы', () => {
    expect(dayKey(new Date('2026-11-18T20:59:00Z'))).toBe('2026-11-18')
    expect(dayKey(new Date('2026-11-18T21:01:00Z'))).toBe('2026-11-19')
    expect(timeLabel('2026-11-18T21:01:00Z')).toBe('00:01')
  })
})

describe('ссылки на учебные записи', () => {
  it('открывает занятие, событие сессии и заявку', () => {
    expect(targetHref({ type: 'schedule', id: 'example' })).toBe('/app/schedule?lesson=example#lesson-example')
    expect(targetHref({ type: 'exam', id: 'example' })).toBe('/app/study?tab=exams#exam-example')
    expect(targetHref({ type: 'request', id: 'example' })).toBe('/app/requests/example')
  })
})
