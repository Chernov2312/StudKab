# ER-диаграмма БД — «Пульс»

Диаграмма **MVP** для PostgreSQL / SQLAlchemy 2 / Alembic. Источник функциональных требований — [`Task.md`](../Task.md), §8 и §10. Для Mermaid Live Editor можно использовать исходник [`database-erd.mmd`](./database-erd.mmd).

```mermaid
erDiagram
    direction LR

    USERS ||--o{ SESSIONS : "creates"
    USERS ||--o| STUDENTS : "has_profile"
    GROUPS ||--o{ STUDENTS : "includes"

    COURSES ||--o{ COURSE_OFFERINGS : "is_taught_as"
    GROUPS ||--o{ COURSE_OFFERINGS : "receives"
    INSTRUCTORS ||--o{ COURSE_OFFERINGS : "teaches"
    COURSE_OFFERINGS ||--o{ LESSONS : "schedules"
    LESSONS ||--o{ LESSON_CHANGES : "has_changes"

    STUDENTS ||--o{ ENROLLMENTS : "enrolls"
    COURSE_OFFERINGS ||--o{ ENROLLMENTS : "accepts"
    ENROLLMENTS ||--o{ GRADES : "receives"
    COURSE_OFFERINGS ||--o{ EXAMS : "has_exams"

    REQUEST_TYPES ||--o{ APPLICATIONS : "defines"
    STUDENTS ||--o{ APPLICATIONS : "submits"
    APPLICATIONS ||--o{ APPLICATION_EVENTS : "has_history"
    USERS |o--o{ APPLICATION_EVENTS : "performs_optional"
    STUDENTS ||--o{ NOTIFICATIONS : "receives"

    USERS {
        uuid id PK
        varchar username UK
        varchar password_hash
        varchar role
        boolean active
        timestamptz created_at
    }

    SESSIONS {
        uuid id PK
        uuid user_id FK
        varchar token_hash UK
        varchar csrf_token
        timestamptz expires_at
        timestamptz revoked_at
    }

    LOGIN_ATTEMPTS {
        varchar key PK
        timestamptz window PK
        int count
    }

    STUDENTS {
        uuid user_id PK, FK
        varchar full_name
        varchar faculty
        varchar program
        int course_year
        uuid group_id FK
    }

    GROUPS {
        uuid id PK
        varchar name UK
    }

    INSTRUCTORS {
        uuid id PK
        varchar display_name
    }

    COURSES {
        uuid id PK
        varchar title
        varchar assessment_type
    }

    COURSE_OFFERINGS {
        uuid id PK
        uuid course_id FK
        uuid group_id FK
        uuid instructor_id FK
        varchar term
    }

    LESSONS {
        uuid id PK
        uuid offering_id FK
        timestamptz starts_at
        timestamptz ends_at
        varchar room
        varchar lesson_type
    }

    LESSON_CHANGES {
        uuid id PK
        uuid lesson_id FK
        varchar kind
        jsonb old_values
        jsonb new_values
        timestamptz changed_at
    }

    ENROLLMENTS {
        uuid id PK
        uuid student_id FK
        uuid offering_id FK
    }

    GRADES {
        uuid id PK
        uuid enrollment_id FK
        varchar kind
        varchar value
        timestamptz graded_at
    }

    EXAMS {
        uuid id PK
        uuid offering_id FK
        timestamptz scheduled_at
        varchar room
        varchar exam_type
    }

    REQUEST_TYPES {
        uuid id PK
        varchar code UK
        varchar title
        text description
        jsonb fields_schema
        boolean comment_required
        int comment_max_length
    }

    APPLICATIONS {
        uuid id PK
        uuid student_id FK
        uuid type_id FK
        varchar status
        jsonb fields
        text comment
        timestamptz created_at
        timestamptz updated_at
    }

    APPLICATION_EVENTS {
        uuid id PK
        uuid application_id FK
        varchar from_status
        varchar to_status
        text note
        uuid actor_user_id FK
        timestamptz created_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid student_id FK
        varchar kind
        varchar title
        text body
        varchar target_type
        uuid target_id
        timestamptz created_at
        timestamptz read_at
    }
```

## Семантика и ограничения

- `STUDENTS.user_id` — одновременно **PK** и **FK** на `USERS.id`. Студентский `student_id` в `ENROLLMENTS`, `APPLICATIONS` и `NOTIFICATIONS` ссылается на `STUDENTS.user_id`. У сотрудника (`USERS.role = staff`) профиль в `STUDENTS` необязателен.
- `LOGIN_ATTEMPTS` хранит общие счётчики входа по хешу имени или адреса и началу временного окна. Составной PK обеспечивает атомарное увеличение, индекс окна используется для удаления устаревших счётчиков.
- `ENROLLMENTS.id` — отдельный UUID **PK**, чтобы `GRADES.enrollment_id` ссылался на один конкретный enrollment. Дополнительно требуется `UNIQUE(student_id, offering_id)`; этот составной уникальный индекс не отображается в колонках диаграммы.
- `SESSIONS.token_hash` хранит только хеш случайного значения из HttpOnly cookie, **не** исходный токен. `SESSIONS.revoked_at`, `NOTIFICATIONS.read_at`, `APPLICATIONS.comment`, `APPLICATION_EVENTS.actor_user_id` и `APPLICATION_EVENTS.from_status` могут быть `NULL` по смыслу домена (первое событие не имеет старого статуса; системное событие — автора).
- `APPLICATIONS.fields` хранит JSONB, **проверенный** по `REQUEST_TYPES.fields_schema`; сама DB-схема не заменяет серверную валидацию Pydantic и бизнес-правил.
- `LESSONS` хранит действующие время и аудиторию. В `LESSON_CHANGES` сохраняются прежние и новые значения. При отмене новое значение равно `NULL`, время в `LESSONS` сохраняется.
- `NOTIFICATIONS.target_type` + `target_id` — необязательная полиморфная ссылка для UI; **внешнего ключа на произвольную таблицу здесь нет**, и ни одно действие по ней не может обходить ownership check.
- Допустимые значения `USERS.role`, статусов `APPLICATIONS.status`, типов событий и оценок нужно зафиксировать через `Enum`/`CHECK` в Alembic. `STUDENTS.course_year` ограничен `1..6`; `LESSONS.ends_at > starts_at`.
- Для запросов критичны индексы на `SESSIONS.token_hash`, `STUDENTS.group_id`, `LESSONS(offering_id, starts_at)`, `ENROLLMENTS(student_id, offering_id)`, `APPLICATIONS(student_id, created_at)`, `APPLICATION_EVENTS(application_id, created_at)`, `NOTIFICATIONS(student_id, created_at)`; состав и направления индексов проверяются на реальных запросах.
- Все временные метки в БД — `TIMESTAMPTZ` (UTC), в интерфейсе демонстрационные даты отображаются в `Europe/Moscow`.

## Защита от доступа к чужим данным

- `user_id`/`student_id` текущего студента определяется **по серверной сессии**, а не из path/query/body.
- `APPLICATIONS` и `NOTIFICATIONS` всегда читаются и обновляются с SQL-фильтром `student_id = current_student_id`.
- `GRADES` доступны только через `ENROLLMENTS.student_id = current_student_id`.
- `LESSONS` доступны через `STUDENTS.group_id` → `COURSE_OFFERINGS.group_id`; `EXAMS` — через `ENROLLMENTS` (а не просто по группе).
- Изменение статуса заявки и добавление `APPLICATION_EVENTS` выполняются **одной транзакцией**; чужой или несуществующий приватный UUID даёт одинаковый HTTP `404`.

## Где реализуется схема

| Таблицы | SQLAlchemy models (`backend/app/db/models/`) | DAO (`backend/app/db/dao/`) |
|---|---|---|
| `users`, `sessions` | `user.py`, `session.py` | `user_dao.py`, `session_dao.py` |
| `login_attempts` | `user.py` | `login_dao.py` |
| `students`, `groups` | `student.py` | `student_dao.py` |
| `instructors`, `courses`, `course_offerings`, `lessons`, `lesson_changes` | `schedule.py` | `schedule_dao.py` |
| `enrollments`, `grades`, `exams` | `study.py` | `study_dao.py`, `exam_dao.py` |
| `request_types`, `applications`, `application_events` | `application.py` | `application_dao.py` |
| `notifications` | `notification.py` | `notification_dao.py` |

**Важно:** диаграмма описывает целевую схему, но сама по себе таблиц не создаёт. Источник исполняемой схемы — Alembic-миграции; при изменении сущностей обновлять эту диаграмму, модели, миграции, DAO, DTO и тесты в одной задаче.
