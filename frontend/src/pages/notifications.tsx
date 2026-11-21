import { useMutation, useQuery } from '@tanstack/react-query'
import { Bell, Check } from 'lucide-react'
import { useState } from 'react'
import { api, mutate, queryClient } from '../app/api'
import type { Notifications } from '../app/contracts'
import { Badge, Empty, Heading, PageControl, QueryView, TextLink } from '../components/ui'
import { dateLabel, notificationLabel, targetHref, timeLabel } from '../features/format'

export function NotificationsPage() {
  const [unread, setUnread] = useState(false)
  const [page, setPage] = useState(1)
  const query = useQuery({
    queryKey: ['notifications', unread, page],
    queryFn: ({ signal }) => api<Notifications>('/notifications?unread_only=' + unread + '&page=' + page, { signal }),
    refetchInterval: 60_000,
  })
  const mark = useMutation({
    mutationFn: (id: string) => mutate('/notifications/' + encodeURIComponent(id) + '/read'),
    onSuccess: async () => {
      if (unread && page > 1 && query.data?.items.length === 1) setPage(page - 1)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['notifications'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ])
    },
  })
  return <>
    <Heading title="Уведомления" description={query.data ? 'Непрочитано: ' + query.data.unread_count : undefined} />
    <div className="toolbar"><div className="switcher" role="group" aria-label="Фильтр уведомлений">
      <button aria-pressed={!unread} onClick={() => { setUnread(false); setPage(1) }}>Все</button>
      <button aria-pressed={unread} onClick={() => { setUnread(true); setPage(1) }}>Непрочитанные</button>
    </div></div>
    <QueryView query={query}>{data => <div className="stack">
      {data.items.length === 0 && <Empty title={unread ? 'Непрочитанных уведомлений нет' : 'Уведомлений пока нет'} />}
      {data.items.map(item => <article className={'card notification ' + (item.read_at ? '' : 'unread')} key={item.id}>
        <div className="list-heading"><span className="notification-kind"><Bell size={17} aria-hidden="true" />{notificationLabel[item.kind]}</span>
          <Badge tone={item.read_at ? 'quiet' : 'green'}>{item.read_at ? 'Прочитано' : 'Новое'}</Badge>
        </div>
        <h2>{item.title}</h2><p>{item.body}</p>
        <small>{dateLabel(item.created_at)}, {timeLabel(item.created_at)}</small>
        <div className="form-actions">
          {item.target && <TextLink to={targetHref(item.target)}>Открыть</TextLink>}
          {!item.read_at && <button className="button secondary" disabled={mark.isPending} onClick={() => mark.mutate(item.id)}>
            <Check size={16} aria-hidden="true" />{mark.isPending && mark.variables === item.id ? 'Сохраняем…' : 'Отметить прочитанным'}
          </button>}
        </div>
        {mark.error && mark.variables === item.id && <p className="form-error" role="alert">{mark.error.message || 'Не удалось сохранить отметку'}</p>}
      </article>)}
      <PageControl data={data.pagination} onChange={setPage} />
    </div>}</QueryView>
  </>
}
