import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import { join } from 'node:path'

const wcagTags = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']

async function checkAccessibility(page: Page, screen: string) {
  const { violations } = await new AxeBuilder({ page }).withTags(wcagTags).analyze()
  const failures = violations.map(({ id, nodes }) => ({
    id,
    elements: nodes.map(({ target, failureSummary }) => ({ target, failureSummary })),
  }))
  expect(failures, 'WCAG A/AA: ' + screen).toEqual([])
}

async function openCabinetWithKeyboard(page: Page, account: 'alina' | 'mark') {
  const password = process.env[account === 'alina' ? 'DEMO_ALINA_PASSWORD' : 'DEMO_MARK_PASSWORD']
  if (!password) throw new Error('Задайте пароли демо-аккаунтов для Playwright.')

  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Вход в кабинет' })).toBeVisible()
  await checkAccessibility(page, 'вход')
  const username = page.getByLabel('Логин')
  const passwordInput = page.getByLabel('Пароль')
  const signIn = page.getByRole('button', { name: 'Войти', exact: true })

  await page.keyboard.press('Tab')
  await expect(username).toBeFocused()
  await expect(username).toHaveCSS('outline-style', 'solid')
  await username.fill('demo.' + account)
  await page.keyboard.press('Tab')
  await expect(passwordInput).toBeFocused()
  await passwordInput.fill(password)
  await page.keyboard.press('Tab')
  await expect(signIn).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('heading', { name: 'Мой день' })).toBeVisible()
}

const screens = [
  ['/app/profile', 'Профиль'],
  ['/app/schedule', 'Расписание'],
  ['/app/study', 'Учёба'],
  ['/app/study?tab=exams', 'Учёба'],
  ['/app/requests', 'Заявки'],
  ['/app/requests/new', 'Новая заявка'],
  ['/app/notifications', 'Уведомления'],
  ['/app/more', 'Ещё'],
  ['/app/about', 'О проекте'],
]

test('клавиатурный вход, переход к содержимому и WCAG A/AA на страницах кабинета', async ({ page }, testInfo) => {
  test.setTimeout(90_000)
  await openCabinetWithKeyboard(page, testInfo.project.name === 'desktop' ? 'alina' : 'mark')

  await page.goto('/app')
  await expect(page.getByRole('heading', { name: 'Мой день' })).toBeVisible()
  const skip = page.getByRole('link', { name: 'Перейти к содержимому' })
  await page.keyboard.press('Tab')
  await expect(skip).toBeFocused()
  await expect(skip).toHaveCSS('outline-style', 'solid')

  const evidence = process.env.EVIDENCE_DIR
  if (evidence && testInfo.project.name === 'mobile-360') {
    await mkdir(evidence, { recursive: true })
    await page.screenshot({ path: join(evidence, 'mobile-360-keyboard-focus.png') })
  }

  await page.keyboard.press('Enter')
  await expect(page.getByRole('main')).toBeFocused()
  await checkAccessibility(page, 'главная')

  if (testInfo.project.name === 'desktop') {
    await page.setViewportSize({ width: 768, height: 900 })
    await checkAccessibility(page, 'главная 768 px')
    await page.setViewportSize({ width: 1440, height: 900 })
  }

  for (const [path, heading] of screens) {
    await page.goto(path)
    await expect(page.getByRole('heading', { name: heading, level: 1 })).toBeVisible()
    await expect(page.getByText('Загрузка данных…', { exact: true })).toHaveCount(0)
    await checkAccessibility(page, path)
  }

  await page.goto('/app/requests')
  const request = page.getByRole('main').getByRole('link', { name: /Справка об обучении|Заявление в деканат/ }).first()
  await request.click()
  await expect(page.getByRole('heading', { name: 'История заявки' })).toBeVisible()
  await checkAccessibility(page, 'подробности заявки')
})

test('доступные состояния загрузки, ошибки и пустого ответа', { tag: '@mobile-360' }, async ({ page }) => {
  await openCabinetWithKeyboard(page, 'alina')

  const study = '**/api/v1/study'
  let resume!: () => void
  const paused = new Promise<void>(resolve => { resume = resolve })
  await page.route(study, async route => {
    await paused
    await route.fulfill({ status: 503, json: {
      error: { code: 'SERVICE_UNAVAILABLE', message: 'Сервис временно недоступен', request_id: 'req-test' },
    } })
  }, { times: 1 })

  try {
    await page.goto('/app/study')
    await expect(page.getByRole('status')).toContainText('Загрузка данных')
    await checkAccessibility(page, 'загрузка')
  } finally {
    resume()
  }

  const error = page.getByRole('alert')
  await expect(error).toContainText('Сервис временно недоступен')
  await checkAccessibility(page, 'ошибка')
  await page.route(study, route => route.fulfill({ status: 200, json: {
    courses: [], summary: { passed: 0, pending: 0, total: 0 },
  } }), { times: 1 })
  await error.getByRole('button', { name: 'Повторить' }).press('Enter')
  await expect(page.getByRole('heading', { name: 'Дисциплин пока нет' })).toBeVisible()
  await checkAccessibility(page, 'пустой список')
})
