import { Activity, AlertCircle, ArrowRight, Inbox, LoaderCircle } from 'lucide-react'
import type { ReactNode } from 'react'
import { useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ApiError } from '../../app/api'
import type { Pagination } from '../../app/contracts'

export const notice = 'Конкурсный прототип. Неофициальный сервис. Все данные вымышлены.'

export function Brand() {
  return <div className="brand"><span className="brand-icon"><Activity aria-hidden="true" /></span><span>Пульс<small>Цифровой деканат</small></span></div>
}

export function Heading({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <header className="page-heading"><div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</header>
}

export function Loading({ label = 'Загрузка данных…' }: { label?: string }) {
  return <div className="state" role="status"><LoaderCircle className="spinner" aria-hidden="true" /><p>{label}</p></div>
}

export function ErrorState({ error, retry, back }: { error: Error; retry?: () => void; back?: string }) {
  const missing = error instanceof ApiError && error.status === 404
  return <div className="state" role="alert">
    <AlertCircle aria-hidden="true" />
    <h2>{missing ? 'Запись не найдена' : 'Не удалось загрузить данные'}</h2>
    <p>{missing ? 'Проверьте ссылку или вернитесь в раздел.' : error instanceof ApiError ? error.message : 'Проверьте подключение к сети и повторите запрос.'}</p>
    {retry && !missing && <button className="button secondary" onClick={retry}>Повторить</button>}
    {back && <Link className="button secondary" to={back}>Вернуться в раздел</Link>}
  </div>
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return <div className="state"><Inbox aria-hidden="true" /><h2>{title}</h2>{children}</div>
}

export function QueryView<T>({ query, children, back }: {
  query: { isPending: boolean; error: Error | null; data: T | undefined; refetch: () => unknown }
  children: (data: T) => ReactNode
  back?: string
}) {
  if (query.isPending) return <Loading />
  if (query.error) return <ErrorState error={query.error} retry={query.refetch} back={back} />
  return query.data === undefined ? null : children(query.data)
}

export function Badge({ children, tone = 'quiet' }: { children: ReactNode; tone?: 'quiet' | 'warm' | 'green' | 'red' }) {
  return <span className={'badge ' + tone}>{children}</span>
}

export function TextLink({ to, children }: { to: string; children: ReactNode }) {
  return <Link className="text-link" to={to}>{children}<ArrowRight size={16} aria-hidden="true" /></Link>
}

export function PageControl({ data, onChange }: { data: Pagination; onChange: (page: number) => void }) {
  if (data.page === 1 && !data.has_next) return null
  return <nav className="pagination" aria-label="Страницы">
    <button className="button secondary" disabled={data.page === 1} onClick={() => onChange(data.page - 1)}>Назад</button>
    <span>Страница {data.page}</span>
    <button className="button secondary" disabled={!data.has_next} onClick={() => onChange(data.page + 1)}>Далее</button>
  </nav>
}

export function AnchorCard({ id, children }: { id: string; children: ReactNode }) {
  const { hash } = useLocation()
  const ref = useRef<HTMLElement>(null)
  const selected = hash === '#' + id
  useEffect(() => {
    if (selected) ref.current?.scrollIntoView({ block: 'center' })
  }, [selected])
  return <article ref={ref} id={id} className={'card ' + (selected ? 'selected-card' : '')}>{children}</article>
}
