import { useQuery } from '@tanstack/react-query'
import { UserRound } from 'lucide-react'
import { api } from '../app/api'
import type { Profile } from '../app/contracts'
import { Heading, QueryView } from '../components/ui'

export function ProfilePage() {
  const query = useQuery({ queryKey: ['profile'], queryFn: ({ signal }) => api<Profile>('/profile', { signal }) })
  return <><Heading title="Профиль" /><QueryView query={query}>{profile => <article className="card">
    <div className="list-heading"><h2>{profile.full_name}</h2><span className="tile-icon"><UserRound size={20} aria-hidden="true" /></span></div>
    <dl className="details">
      <div><dt>Факультет</dt><dd>{profile.faculty}</dd></div>
      <div><dt>Направление</dt><dd>{profile.program}</dd></div>
      <div><dt>Курс</dt><dd>{profile.course_year}</dd></div>
      <div><dt>Группа</dt><dd>{profile.group.name}</dd></div>
    </dl>
  </article>}</QueryView></>
}
