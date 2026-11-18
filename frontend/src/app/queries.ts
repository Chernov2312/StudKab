import { queryOptions } from '@tanstack/react-query'
import { api, getSession } from './api'
import type { Dashboard, RequestType } from './contracts'

export const sessionQuery = queryOptions({ queryKey: ['session'], queryFn: ({ signal }) => getSession(signal) })

export const dashboardQuery = queryOptions({
  queryKey: ['dashboard'],
  queryFn: ({ signal }) => api<Dashboard>('/dashboard', { signal }),
})

export const requestTypesQuery = queryOptions({
  queryKey: ['request-types'],
  queryFn: async ({ signal }) => (await api<{ items: RequestType[] }>('/request-types', { signal })).items,
})
