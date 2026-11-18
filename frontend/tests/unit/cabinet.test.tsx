import { QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { queryClient } from '../../src/app/api'
import { App } from '../../src/app/router'
import { certificate, dashboard, day, exams, lesson, me, notification, page, request, startsAt, statement, study } from './fixtures'

type Endpoint = (url: URL, init?: RequestInit) => Response | Promise<Response>
type Overrides = Record<string, Endpoint>

function error(status: number, code: string, message: string) {
  return Response.json({ error: { code, message, request_id: 'req-test' } }, { status })
}

const defaultEndpoints: Overrides = {
  'GET /auth/me': () => Response.json(me),
  'GET /auth/csrf': () => Response.json({ csrf_token: 'fixture-csrf' }),
  'GET /dashboard': () => Response.json(dashboard),
  'GET /profile': () => Response.json(me.student),
  'GET /schedule': url => Response.json({
    view: url.searchParams.get('view') ?? 'today', timezone: 'Europe/Moscow',
    range: { start_date: day, end_date: day }, items: [lesson],
  }),
  'GET /study': () => Response.json(study),
  'GET /exams': () => Response.json({ items: exams }),
  'GET /request-types': () => Response.json({ items: [certificate, statement] }),
  'GET /requests': () => Response.json(page([request])),
  'GET /requests/request-a': () => Response.json(request),
  'GET /notifications': () => Response.json({ ...page([notification]), unread_count: 1 }),
}

function open(path: string, overrides: Overrides = {}) {
  const endpoints = { ...defaultEndpoints, ...overrides }
  const fetchStub = vi.fn((input: string, init?: RequestInit) => {
    const url = new URL(input, 'http://puls.test')
    const key = (init?.method ?? 'GET') + ' ' + url.pathname.replace(/^\/api\/v1/, '')
    const endpoint = endpoints[key]
    if (!endpoint) return Promise.resolve(error(404, 'NOT_FOUND', 'Запись не найдена'))
    return Promise.resolve(endpoint(url, init))
  })
  vi.stubGlobal('fetch', fetchStub)
  render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={[path]}><App /></MemoryRouter></QueryClientProvider>)
  return fetchStub
}

const heading = (name: string) => screen.findByRole('heading', { name })

afterEach(() => {
  cleanup()
  queryClient.clear()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('Вход и навигация', () => {
  it('направляет гостя на вход, показывает ошибку и открывает кабинет после повторного входа', async () => {
    let authenticated = false
    const submit = vi.fn((_url: URL, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body))
      if (body.username !== me.user.username) return error(401, 'INVALID_CREDENTIALS', 'Неверный логин или пароль')
      authenticated = true
      return Response.json({ user: me.user, session: { expires_at: startsAt } })
    })
    open('/app/requests', {
      'GET /auth/me': () => authenticated ? Response.json(me) : error(401, 'UNAUTHORIZED', 'Войдите'),
      'POST /auth/login': submit,
    })
    expect(await heading('Вход в кабинет')).toBeTruthy()
    expect(screen.getByText(/Все данные вымышлены/)).toBeTruthy()
    const username = screen.getByLabelText('Логин')
    const password = screen.getByLabelText('Пароль')
    fireEvent.change(username, { target: { value: 'demo.other' } })
    fireEvent.change(password, { target: { value: crypto.randomUUID() } })
    fireEvent.click(screen.getByRole('button', { name: 'Войти' }))
    expect((await screen.findByRole('alert')).textContent).toContain('Неверный логин или пароль')
    expect((password as HTMLInputElement).value).toBe('')
    fireEvent.change(username, { target: { value: me.user.username } })
    fireEvent.change(password, { target: { value: crypto.randomUUID() } })
    fireEvent.click(screen.getByRole('button', { name: 'Войти' }))
    expect(await heading('Мой день')).toBeTruthy()
    expect(await heading('Привет, Алина!')).toBeTruthy()
    expect(submit).toHaveBeenCalledTimes(2)
  })

  it('показывает профиль и страницу проекта и очищает данные после выхода', async () => {
    let signedIn = true
    const logout = vi.fn(() => {
      signedIn = false
      return new Response(null, { status: 204 })
    })
    open('/profile', {
      'GET /auth/me': () => signedIn ? Response.json(me) : error(401, 'UNAUTHORIZED', 'Войдите'),
      'POST /auth/logout': logout,
    })
    expect(await heading('Алина Тестова')).toBeTruthy()
    expect(screen.getAllByText('ИВТ-21').length).toBeGreaterThan(0)
    const nav = screen.getByRole('navigation', { name: 'Разделы кабинета' })
    fireEvent.click(within(nav).getByRole('link', { name: 'О проекте' }))
    expect(await heading('О проекте')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Выйти' }))
    expect(await heading('Вход в кабинет')).toBeTruthy()
    expect(queryClient.getQueryData(['profile'])).toBeUndefined()
    expect(logout).toHaveBeenCalledWith(expect.any(URL), expect.objectContaining({
      headers: expect.objectContaining({ 'X-CSRF-Token': 'fixture-csrf' }),
    }))
  })

  it('открывает уведомления из меню «Ещё»', async () => {
    open('/app/more')
    expect(await heading('Ещё')).toBeTruthy()
    const main = screen.getByRole('main')
    fireEvent.click(within(main).getByRole('link', { name: 'Уведомления' }))
    expect(await heading('Уведомления')).toBeTruthy()
  })

  it('показывает причину повторного входа после истечения сессии', async () => {
    open('/login?expired=1', { 'GET /auth/me': () => error(401, 'UNAUTHORIZED', 'Войдите') })
    expect(await heading('Вход в кабинет')).toBeTruthy()
    expect(screen.getByRole('status').textContent).toContain('Сессия завершилась')
  })

  it('показывает пустые блоки главной', async () => {
    open('/', { 'GET /dashboard': () => Response.json({
      ...dashboard, next_lesson: null, next_exam: null, focus: [],
      active_requests_count: 0, unread_notifications_count: 0,
      study: { total: 0, passed: 0, pending: 0 },
    }) })
    expect(await heading('Мой день')).toBeTruthy()
    expect(screen.getByText(/Сегодня больше нет занятий/)).toBeTruthy()
    expect(screen.getByText('Запланированных событий нет.')).toBeTruthy()
    expect(screen.getByText('Активных заявок нет')).toBeTruthy()
    expect(screen.getByText('На сегодня ничего срочного.')).toBeTruthy()
  })
})

describe('Расписание и успеваемость', () => {
  it('показывает старые и новые параметры занятия и загружает выбранную неделю', async () => {
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
    const fetch = open('/app/schedule?lesson=lesson-a#lesson-lesson-a')
    expect(await heading('Алгоритмы')).toBeTruthy()
    expect(screen.getByText('Стало', { exact: true })).toBeTruthy()
    expect(screen.getByText(/А-101/)).toBeTruthy()
    expect(window.HTMLElement.prototype.scrollIntoView).toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Неделя' }))
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/schedule?view=week'), expect.any(Object)))
    const date = screen.getByLabelText('Дата расписания')
    fireEvent.change(date, { target: { value: '2026-11-21' } })
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining('date=2026-11-21'), expect.any(Object)))
  })

  it('показывает загрузку, ошибку, повтор и пустое расписание', async () => {
    let complete!: (response: Response) => void
    const first = new Promise<Response>(resolve => { complete = resolve })
    const schedule = vi.fn<Endpoint>().mockReturnValueOnce(first).mockImplementation(url => Response.json({
      view: url.searchParams.get('view'), timezone: 'Europe/Moscow',
      range: { start_date: day, end_date: day }, items: [],
    }))
    open('/app/schedule', { 'GET /schedule': schedule })
    const loading = await screen.findByText('Загрузка данных…')
    expect(loading.textContent).toContain('Загрузка')
    complete(error(503, 'SERVICE_UNAVAILABLE', 'Сервис временно недоступен'))
    expect((await screen.findByRole('alert')).textContent).toContain('Сервис временно недоступен')
    fireEvent.click(screen.getByRole('button', { name: 'Повторить' }))
    expect(await heading('Сегодня нет занятий')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Неделя' }))
    expect(await heading('На этой неделе занятий нет')).toBeTruthy()
  })

  it('различает отсутствие дисциплин и пустой календарь сессии', async () => {
    open('/app/study', {
      'GET /study': () => Response.json({ summary: { passed: 0, total: 0, pending: 0 }, courses: [] }),
      'GET /exams': () => Response.json({ items: [] }),
    })
    expect(await heading('Дисциплин пока нет')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Сессия' }))
    expect(await heading('На этот учебный период событий нет')).toBeTruthy()
  })

  it('показывает оценки, отсутствие оценок и вкладку сессии', async () => {
    open('/app/study')
    expect(await heading('Сдано 1 из 2')).toBeTruthy()
    expect(screen.getByText('Пока нет оценок')).toBeTruthy()
    expect(screen.getByText('зачёт', { exact: true })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Сессия' }))
    expect(await heading('Алгоритмы')).toBeTruthy()
    expect(screen.getByText('Запланировано')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Оценки' }))
    expect(await heading('Сдано 1 из 2')).toBeTruthy()
  })
})

describe('Заявки и уведомления', () => {
  it('строит поля по справочнику, показывает ошибку отправки и историю новой заявки', async () => {
    const send = vi.fn<Endpoint>().mockReturnValueOnce(Response.json({
      error: {
        code: 'VALIDATION_ERROR', message: 'Проверьте введённые данные', request_id: 'req-test',
        details: [{ field: 'comment', message: 'Добавьте комментарий' }],
      },
    }, { status: 422 })).mockReturnValueOnce(Response.json(request, { status: 201 }))
    open('/app/requests/new', { 'POST /requests': send })
    const type = await screen.findByLabelText('Тип заявки')
    fireEvent.change(type, { target: { value: statement.code } })
    expect(screen.getByLabelText('Тема обращения')).toBeTruthy()
    expect((screen.getByRole('textbox', { name: /Комментарий/ }) as HTMLTextAreaElement).required).toBe(true)
    fireEvent.change(type, { target: { value: certificate.code } })
    fireEvent.change(screen.getByLabelText('Для чего нужна справка'), { target: { value: 'work' } })
    fireEvent.change(screen.getByLabelText('Способ получения'), { target: { value: 'digital' } })
    fireEvent.click(screen.getByRole('button', { name: 'Отправить заявку' }))
    expect((await screen.findByRole('alert')).textContent).toContain('Добавьте комментарий')
    fireEvent.change(screen.getByLabelText(/Комментарий/), { target: { value: request.comment } })
    fireEvent.click(screen.getByRole('button', { name: 'Отправить заявку' }))
    expect(await heading('История заявки')).toBeTruthy()
    expect(screen.getByText('Заявка отправлена')).toBeTruthy()
    expect(screen.getByText('Заявка создана')).toBeTruthy()
    expect(send).toHaveBeenLastCalledWith(expect.any(URL), expect.objectContaining({
      headers: expect.objectContaining({ 'X-CSRF-Token': 'fixture-csrf' }),
      body: JSON.stringify({ type_code: certificate.code, fields: request.fields, comment: request.comment }),
    }))
  })

  it('фильтрует и перелистывает заявки', async () => {
    open('/app/requests', {
      'GET /requests': url => {
        const params = url.searchParams
        if (params.get('status')) return Response.json(page([]))
        return Response.json(page([request], Number(params.get('page')), 21, params.get('page') === '1'))
      },
    })
    expect(await heading('Справка об обучении')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }))
    expect(await screen.findByText('Страница 2')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Назад' }))
    expect(await screen.findByText('Страница 1')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Статус'), { target: { value: 'ready' } })
    expect(await heading('Заявок с таким статусом нет')).toBeTruthy()
  })

  it('показывает одинаковое состояние отсутствующей заявки и рабочий возврат', async () => {
    open('/app/requests/unknown')
    expect(await heading('Запись не найдена')).toBeTruthy()
    fireEvent.click(screen.getByRole('link', { name: 'Вернуться в раздел' }))
    expect(await heading('Справка об обучении')).toBeTruthy()
  })

  it('отмечает уведомление прочитанным, обновляет счётчик и очищает непрочитанное', async () => {
    let read = false
    const mark = vi.fn(() => {
      read = true
      return Response.json({ id: notification.id, read_at: startsAt, is_read: true })
    }).mockReturnValueOnce(error(503, 'SERVICE_UNAVAILABLE', 'Сервис временно недоступен'))
    open('/app/notifications', {
      'GET /notifications': url => Response.json({
        ...page(read && url.searchParams.get('unread_only') === 'true' ? [] : [{
          ...notification, read_at: read ? startsAt : null,
        }]),
        unread_count: read ? 0 : 1,
      }),
      'POST /notifications/notice-a/read': mark,
    })
    expect(await heading('Пара перенесена')).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Открыть' }).getAttribute('href')).toContain('lesson-a')
    fireEvent.click(screen.getByRole('button', { name: 'Отметить прочитанным' }))
    expect((await screen.findByRole('alert')).textContent).toContain('Сервис временно недоступен')
    fireEvent.click(screen.getByRole('button', { name: 'Отметить прочитанным' }))
    expect(await screen.findByText('Прочитано')).toBeTruthy()
    expect(await screen.findByText('Непрочитано: 0')).toBeTruthy()
    expect(mark).toHaveBeenCalledTimes(2)
    fireEvent.click(screen.getByRole('button', { name: 'Непрочитанные' }))
    expect(await heading('Непрочитанных уведомлений нет')).toBeTruthy()
  })
})
