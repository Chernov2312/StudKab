import { QueryClient } from '@tanstack/react-query'
import type { LoginResult, Me } from './contracts'

type ErrorDetail = { field: string; message: string }
type ErrorBody = { code: string; message: string; request_id: string; details?: ErrorDetail[] }

export class ApiError extends Error {
  constructor(public status: number, public data?: ErrorBody) {
    super(data?.message ?? 'Не удалось связаться с сервисом.')
  }
}

export const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: false } },
})

type HttpOptions = Omit<RequestInit, 'credentials'>
export async function api<T>(path: string, options: HttpOptions = {}, clearSession = true): Promise<T> {
  const response = await fetch('/api/v1' + path, { ...options, credentials: 'include' })
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { error?: ErrorBody } | null
    if (response.status === 401 && clearSession) {
      queryClient.clear()
      window.location.replace('/login?expired=1')
    }
    throw new ApiError(response.status, payload?.error)
  }
  if (response.status === 204) return undefined as T
  return await response.json() as T
}

export async function getSession(signal?: AbortSignal) {
  try {
    return await api<Me>('/auth/me', { signal }, false)
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null
    throw error
  }
}

export function login(username: string, password: string) {
  return api<LoginResult>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  }, false)
}

export async function mutate<T>(path: string, body?: unknown) {
  const { csrf_token } = await api<{ csrf_token: string }>('/auth/csrf')
  return api<T>(path, {
    method: 'POST',
    headers: {
      'X-CSRF-Token': csrf_token,
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}
