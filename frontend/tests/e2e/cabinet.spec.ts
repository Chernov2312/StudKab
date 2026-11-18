import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import { join } from 'node:path'

const noticeTitles: Record<string, string> = {
  'mobile-360': 'Скоро экзамен',
  'mobile-390': 'Пара перенесена',
  desktop: 'Пара отменена',
}

async function signIn(page: Page, account: 'alina' | 'mark') {
  const secret = process.env[account === 'alina' ? 'DEMO_ALINA_PASSWORD' : 'DEMO_MARK_PASSWORD']
  if (!secret) throw new Error('Задайте оба демонстрационных пароля в окружении Playwright.')
  await page.getByLabel('Логин').fill('demo.' + account)
  await page.getByLabel('Пароль').fill(secret)
  await page.getByRole('button', { name: 'Войти', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Мой день' })).toBeVisible()
}

async function logout(page: Page) {
  const more = page.getByRole('link', { name: 'Ещё', exact: true })
  if (await more.isVisible()) await more.click()
  await page.getByRole('button', { name: 'Выйти', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Вход в кабинет' })).toBeVisible()
}

async function fitsViewport(page: Page) {
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
}

test('кабинет A и B, перенос, учёба, заявка, уведомление и выход', async ({ page }, testInfo) => {
  const evidence = process.env.EVIDENCE_DIR
  const capture = async (name: string) => {
    if (!evidence) return
    await mkdir(evidence, { recursive: true })
    await page.screenshot({ path: join(evidence, testInfo.project.name + '-' + name + '.png'), fullPage: true })
  }
  await page.goto('/app/profile')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByRole('heading', { name: 'Вход в кабинет' })).toBeVisible()
  await page.keyboard.press('Tab')
  await expect(page.getByLabel('Логин')).toBeFocused()
  await fitsViewport(page)
  await capture('login')
  await signIn(page, 'alina')
  await expect(page.getByText('Привет, Алина!')).toBeVisible()
  await fitsViewport(page)
  await capture('dashboard')
  if (testInfo.project.name === 'desktop') {
    await page.setViewportSize({ width: 768, height: 900 })
    await fitsViewport(page)
    await capture('dashboard-tablet')
    await page.setViewportSize({ width: 1440, height: 900 })
  }
  await page.getByRole('link', { name: /Занятие перенесено/ }).click()
  await expect(page).toHaveURL(/lesson=/)
  await expect(page.locator('.selected-card').getByText('Перенесено', { exact: true })).toBeVisible()

  const more = page.getByRole('link', { name: 'Ещё', exact: true })
  if (await more.isVisible()) await more.click()
  await page.getByRole('link', { name: 'Профиль', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Алина Тестова' })).toBeVisible()
  await fitsViewport(page)
  await page.getByRole('link', { name: 'Расписание', exact: true }).click()
  await expect(page.getByText('Перенесено', { exact: true })).toBeVisible()
  await expect(page.getByText('Отменено', { exact: true })).toBeVisible()
  await expect(page.getByText('Стало', { exact: true })).toBeVisible()
  await fitsViewport(page)
  await capture('schedule')
  await page.getByRole('button', { name: 'Неделя' }).click()
  await expect(page.getByRole('button', { name: 'Неделя' })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByText('Перенесено', { exact: true })).toBeVisible()
  await page.getByRole('link', { name: 'Учёба', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Сдано 1 из 2' })).toBeVisible()
  await page.getByRole('button', { name: 'Сессия', exact: true }).click()
  await expect(page.getByText('Запланировано', { exact: true })).toBeVisible()
  await fitsViewport(page)

  await page.getByRole('link', { name: 'Заявки', exact: true }).click()
  await page.getByRole('link', { name: 'Новая заявка' }).click()
  await page.getByLabel('Для чего нужна справка').selectOption('work')
  await page.getByLabel('Способ получения').selectOption('digital')
  const comment = 'Демонстрационная заявка: ' + testInfo.project.name
  await page.getByLabel('Комментарий').fill(comment)
  await fitsViewport(page)
  await page.getByRole('button', { name: 'Отправить заявку' }).click()
  await expect(page.getByText('Заявка отправлена')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'История заявки' })).toBeVisible()
  const requestUrl = page.url()
  await page.reload()
  await expect(page.getByText(comment)).toBeVisible()
  await expect(page.getByText('Заявка создана', { exact: true })).toBeVisible()
  await fitsViewport(page)
  await capture('request')

  await page.locator('.topbar').getByRole('link', { name: /Уведомления/ }).click()
  await expect(page.getByRole('heading', { name: 'Уведомления' })).toBeVisible()
  const title = noticeTitles[testInfo.project.name]
  const notification = page.getByRole('article').filter({ has: page.getByRole('heading', { name: title, exact: true }) })
  await expect(notification).toBeVisible()
  const read = notification.getByRole('button', { name: 'Отметить прочитанным' })
  if (await read.isVisible()) await read.click()
  await expect(notification.getByText('Прочитано', { exact: true })).toBeVisible()
  await fitsViewport(page)
  await logout(page)
  await signIn(page, 'alina')
  await page.locator('.topbar').getByRole('link', { name: /Уведомления/ }).click()
  await expect(notification.getByText('Прочитано', { exact: true })).toBeVisible()
  await logout(page)

  await signIn(page, 'mark')
  await expect(page.getByText('Привет, Марк!')).toBeVisible()
  await page.getByRole('link', { name: 'Расписание', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Математическое моделирование' })).toBeVisible()
  await page.goto(requestUrl)
  await expect(page.getByRole('heading', { name: 'Запись не найдена' })).toBeVisible()
  await expect(page.getByText(comment)).toHaveCount(0)
  await fitsViewport(page)
  await logout(page)
})

test('сообщение при неверном входе, повтор после ошибки и переход при истечении сессии', { tag: '@desktop' }, async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Логин').fill('demo.unknown')
  await page.getByLabel('Пароль').fill(crypto.randomUUID())
  await page.getByRole('button', { name: 'Войти', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Неверный логин или пароль')
  await signIn(page, 'mark')
  const studyUrl = '**/api/v1/study'
  await page.route(studyUrl, route => route.fulfill({ status: 503, json: { error: {
    code: 'SERVICE_UNAVAILABLE', message: 'Сервис временно недоступен', request_id: 'req-test',
  } } }), { times: 1 })
  await page.getByRole('link', { name: 'Учёба', exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await page.getByRole('button', { name: 'Повторить' }).click()
  await expect(page.getByRole('heading', { name: 'Сдано 0 из 2' })).toBeVisible()

  await page.route('**/api/v1/schedule?*', async route => {
    await page.context().clearCookies()
    await route.fulfill({ status: 401, json: { error: {
      code: 'UNAUTHORIZED', message: 'Войдите в кабинет', request_id: 'req-test',
    } } })
  })
  await page.getByRole('link', { name: 'Расписание', exact: true }).click()
  await expect(page.getByText('Сессия завершилась. Войдите снова.')).toBeVisible()
  await expect(page.getByText('Марк Примеров')).toHaveCount(0)
})

test('мобильная форма заявления валидирует комментарий и сохраняет историю', { tag: '@mobile-360' }, async ({ page }) => {
  await page.goto('/login')
  await signIn(page, 'mark')
  await page.getByRole('link', { name: 'Новая заявка', exact: true }).click()
  await page.getByLabel('Тип заявки').selectOption('DEAN_OFFICE_STATEMENT')
  await page.getByLabel('Тема обращения').selectOption('study')
  const comment = page.getByLabel('Комментарий')
  await comment.fill('   ')
  await page.getByRole('button', { name: 'Отправить заявку' }).click()
  await expect(page.getByRole('alert')).toContainText('Добавьте комментарий')
  await expect(page.getByLabel('Тема обращения')).toHaveValue('study')
  const explanation = 'Уточнение по демонстрационному учебному плану'
  await comment.fill(explanation)
  await page.getByRole('button', { name: 'Отправить заявку' }).click()
  await expect(page.getByText('Заявка отправлена')).toBeVisible()
  await expect(page.getByText(explanation)).toBeVisible()
  await expect(page.getByText('Заявка создана', { exact: true })).toBeVisible()
  await fitsViewport(page)
  await page.reload()
  await expect(page.getByText(explanation)).toBeVisible()
  await logout(page)
})
