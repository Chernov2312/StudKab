import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, ArrowRight, Check, FileText, Plus } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ApiError, api, mutate, queryClient } from '../app/api'
import type { Page, RequestDetails, RequestInput, RequestItem, RequestStatus, RequestType } from '../app/contracts'
import { requestTypesQuery } from '../app/queries'
import { Badge, Empty, Heading, PageControl, QueryView } from '../components/ui'
import { dateLabel, fieldLabels, optionLabels, requestStatus, timeLabel } from '../features/format'

const statuses = Object.entries(requestStatus)
const statusTone = { new: 'quiet', in_progress: 'warm', ready: 'green', rejected: 'red' } as const

function RequestBadge({ status }: { status: RequestStatus }) {
  return <Badge tone={statusTone[status]}>{requestStatus[status]}</Badge>
}

export function RequestsPage() {
  const [params, setParams] = useSearchParams()
  const page = Number(params.get('page')) || 1
  const status = params.get('status') ?? ''
  const filters = new URLSearchParams({ page: String(page) })
  if (status) filters.set('status', status)
  const query = useQuery({
    queryKey: ['requests', page, status],
    queryFn: ({ signal }) => api<Page<RequestItem>>('/requests?' + filters, { signal }),
  })
  return <>
    <Heading title="Заявки" description="Обращения в деканат и их статусы"
      action={<Link className="button primary" to="/app/requests/new"><Plus size={18} aria-hidden="true" />Новая заявка</Link>} />
    <div className="toolbar"><label className="inline-field">Статус
      <select value={status} onChange={event => setParams(event.target.value ? { status: event.target.value } : {})}>
        <option value="">Все статусы</option>
        {statuses.map(([key, label]) => <option value={key} key={key}>{label}</option>)}
      </select>
    </label></div>
    <QueryView query={query}>{data => <div className="stack">
      {data.items.length === 0 && <Empty title={status ? 'Заявок с таким статусом нет' : 'Заявок пока нет'} />}
      {data.items.map(item => <Link className="card request-link" to={item.id} key={item.id}>
        <span className="tile-icon"><FileText size={19} aria-hidden="true" /></span>
        <div><h2>{item.type_title}</h2><p>{dateLabel(item.created_at)}</p></div>
        <RequestBadge status={item.status} /><ArrowRight size={18} aria-hidden="true" className="request-arrow" />
      </Link>)}
      <PageControl data={data.pagination} onChange={next => setParams({ page: String(next), ...(status ? { status } : {}) })} />
    </div>}</QueryView>
  </>
}

function RequestForm({ types }: { types: RequestType[] }) {
  const [code, setCode] = useState(types[0]?.code ?? '')
  const [comment, setComment] = useState('')
  const kind = types.find(item => item.code === code)
  const navigate = useNavigate()
  const submission = useMutation({
    mutationFn: (input: RequestInput) => mutate<RequestDetails>('/requests', input),
    onSuccess: result => {
      queryClient.setQueryData(['request', result.id], result)
      void queryClient.invalidateQueries({ queryKey: ['requests'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      navigate('/app/requests/' + result.id, { replace: true, state: { created: true } })
    },
  })
  if (!kind) return <Empty title="Типы заявок пока недоступны" />
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (submission.isPending) return
    const form = new FormData(event.currentTarget)
    const fields = Object.fromEntries(
      Object.keys(kind.fields_schema.properties).flatMap(key => {
        const value = form.get(key)
        return typeof value === 'string' && value !== '' ? [[key, value]] : []
      }),
    )
    submission.mutate({ type_code: kind.code, fields, comment: comment || null })
  }
  const error = submission.error
  return <form className="card form-card stack" onSubmit={submit}>
    <label>Тип заявки<select value={code} disabled={submission.isPending} onChange={event => {
      setCode(event.target.value)
      setComment('')
      submission.reset()
    }}>{types.map(type => <option key={type.code} value={type.code}>{type.title}</option>)}</select></label>
    <p className="form-hint">{kind.description}</p>
    <div className="stack" key={code}>
      {Object.entries(kind.fields_schema.properties).map(([name, property]) => <label key={name}>{property.title}
        <select name={name} defaultValue="" required={kind.fields_schema.required.includes(name)} disabled={submission.isPending}>
          <option value="">Выберите вариант</option>
          {property.enum.map(value => <option key={value} value={value}>{optionLabels[value] || value}</option>)}
        </select>
      </label>)}
    </div>
    <label>Комментарий {kind.comment_required ? '' : '(необязательно)'}
      <textarea value={comment} onChange={event => setComment(event.target.value)} rows={4} maxLength={kind.comment_max_length} required={kind.comment_required} disabled={submission.isPending} />
      <small className="form-hint">{comment.length} / {kind.comment_max_length}</small>
    </label>
    {error && <div className="form-error" role="alert">
      <p>{error instanceof ApiError ? error.message : 'Не удалось отправить. Проверьте подключение и повторите попытку.'}</p>
      {error instanceof ApiError && error.data?.details?.length ? <ul>{error.data.details.map((detail, index) =>
        <li key={detail.field + index}>{propertyLabel(detail.field, kind)}{detail.message}</li>)}</ul> : null}
    </div>}
    <div className="form-actions">
      <button className="button primary" disabled={submission.isPending}>{submission.isPending ? 'Отправляем…' : 'Отправить заявку'}<ArrowRight size={18} aria-hidden="true" /></button>
      <Link className="button secondary" to="/app/requests">К списку</Link>
    </div>
  </form>
}

function propertyLabel(field: string, type: RequestType) {
  if (field === 'comment') return 'Комментарий. '
  if (field === 'type_code') return 'Тип заявки. '
  const property = type.fields_schema.properties[field.replace(/^fields\./, '')]?.title
  return property ? property + '. ' : ''
}

export function NewRequestPage() {
  const query = useQuery(requestTypesQuery)
  return <><Link className="back-link" to="/app/requests"><ArrowLeft size={17} aria-hidden="true" /> Все заявки</Link>
    <Heading title="Новая заявка" description="Выберите тип обращения и заполните его поля" />
    <QueryView query={query}>{types => <RequestForm types={types} />}</QueryView>
  </>
}

export function RequestDetailsPage() {
  const { requestId } = useParams()
  const justCreated = useLocation().state?.created === true
  const query = useQuery({
    queryKey: ['request', requestId],
    queryFn: ({ signal }) => api<RequestDetails>('/requests/' + encodeURIComponent(requestId ?? ''), { signal }),
  })
  return <><Link className="back-link" to="/app/requests"><ArrowLeft size={17} aria-hidden="true" /> Все заявки</Link>
    <Heading title="Подробности заявки" />
    <QueryView query={query} back="/app/requests">{item => <div className="stack">
      {justCreated && <div className="notice success" role="status"><Check size={18} aria-hidden="true" />Заявка отправлена</div>}
      <article className="card">
        <div className="list-heading"><h2>{item.type_title}</h2><RequestBadge status={item.status} /></div>
        <dl className="details">
          <div><dt>Номер</dt><dd className="record-id">{item.id}</dd></div>
          <div><dt>Дата подачи</dt><dd>{dateLabel(item.created_at)}, {timeLabel(item.created_at)}</dd></div>
          {Object.entries(item.fields).map(([field, value]) => <div key={field}><dt>{fieldLabels[field] ?? field}</dt><dd>{optionLabels[value] ?? value}</dd></div>)}
          <div><dt>Комментарий</dt><dd className="record-comment">{item.comment || 'Без комментария'}</dd></div>
        </dl>
      </article>
      <section className="card"><h2>История заявки</h2><ol className="timeline">
        {item.history.map(event => <li key={event.id}>
          <RequestBadge status={event.to_status} /><p>{event.note}</p>
          <small>{dateLabel(event.created_at)}, {timeLabel(event.created_at)}</small>
        </li>)}
      </ol></section>
    </div>}</QueryView>
  </>
}
