// @vitest-environment node
import { afterEach, expect, it, vi } from 'vitest'
import { ApiError, api, getSession, mutate, queryClient } from '../../src/app/api'

afterEach(() => {
  queryClient.clear()
  vi.unstubAllGlobals()
})

it('при истечении сессии очищает приватный кэш и возвращает на вход', async () => {
  const replace = vi.fn()
  vi.stubGlobal('window', { location: { replace } })
  vi.stubGlobal('fetch', vi.fn(async () => new Response(null, { status: 401 })))
  queryClient.setQueryData(['requests'], [1])
  await expect(api('/requests')).rejects.toBeInstanceOf(ApiError)
  expect(queryClient.getQueryData(['requests'])).toBeUndefined()
  expect(replace).toHaveBeenCalledWith('/login?expired=1')
})

it('считает гостя текущим состоянием и сохраняет прочие ошибки', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(new Response(null, { status: 401 }))
    .mockResolvedValueOnce(new Response(null, { status: 503 }))
  vi.stubGlobal('fetch', fetch)
  expect(await getSession()).toBeNull()
  await expect(getSession()).rejects.toMatchObject({ status: 503 })
})

it('отправляет credentials, CSRF и пустое тело для выхода', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(Response.json({ csrf_token: 'fixture-csrf' }))
    .mockResolvedValueOnce(new Response(null, { status: 204 }))
  vi.stubGlobal('fetch', fetch)
  expect(await mutate('/auth/logout')).toBeUndefined()
  expect(fetch).toHaveBeenNthCalledWith(1, '/api/v1/auth/csrf', { credentials: 'include' })
  expect(fetch).toHaveBeenNthCalledWith(2, '/api/v1/auth/logout', {
    method: 'POST', credentials: 'include', headers: { 'X-CSRF-Token': 'fixture-csrf' }, body: undefined,
  })
})
