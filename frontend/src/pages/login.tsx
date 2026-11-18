import { ArrowRight, CalendarDays, FileText, GraduationCap } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ApiError, api, login, queryClient } from '../app/api'
import type { Me } from '../app/contracts'
import { sessionQuery } from '../app/queries'
import { Brand, notice } from '../components/ui'

export function LoginPage() {
  const [params] = useSearchParams()
  const [username, setUsername] = useState('')
  const [pending, setPending] = useState(false)
  const [message, setMessage] = useState('')
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (pending) return
    const field = event.currentTarget.elements.namedItem('password') as HTMLInputElement
    const password = field.value
    field.value = ''
    setPending(true)
    setMessage('')
    try {
      await login(username.trim(), password)
      queryClient.setQueryData(sessionQuery.queryKey, await api<Me>('/auth/me', {}, false))
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : 'Сервис недоступен. Проверьте подключение и попробуйте ещё раз.')
      field.focus()
    } finally {
      setPending(false)
    }
  }
  return <main className="login-page">
    <section className="login-context">
      <Brand />
      <div className="login-context-copy"><h2>Всё важное<br />об учёбе</h2>
        <ul>
          <li><CalendarDays aria-hidden="true" />Расписание и переносы</li>
          <li><GraduationCap aria-hidden="true" />Оценки и сессия</li>
          <li><FileText aria-hidden="true" />Заявки в деканат</li>
        </ul>
      </div>
    </section>
    <section className="login-panel">
      <div className="login-form">
        <div className="mobile-login-brand"><Brand /></div>
        <h1>Вход в кабинет</h1>
        {params.has('expired') && <p className="notice" role="status">Сессия завершилась. Войдите снова.</p>}
        <form onSubmit={submit} className="stack">
          <label>Логин<input type="text" name="username" autoComplete="username" minLength={3} maxLength={64} required value={username} onChange={event => setUsername(event.target.value)} /></label>
          <label>Пароль<input type="password" name="password" autoComplete="current-password" maxLength={256} required /></label>
          {message && <p className="form-error" role="alert">{message}</p>}
          <button className="button primary" disabled={pending}>{pending ? 'Входим…' : 'Войти'}<ArrowRight size={18} aria-hidden="true" /></button>
        </form>
        <p className="contest-notice">{notice}</p>
      </div>
    </section>
  </main>
}
