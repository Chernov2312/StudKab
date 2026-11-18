from collections.abc import Collection
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import joinedload

from app.core.domain import ApplicationStatus
from app.db.dao.basedao import BaseDAO
from app.db.models import Application, ApplicationEvent, RequestType


class ApplicationDAO(BaseDAO):
    @staticmethod
    def _owned(
        student_id: UUID,
        statuses: Collection[ApplicationStatus] = (),
    ) -> Select[tuple[Application]]:
        statement = select(Application).where(Application.student_id == student_id)
        if statuses:
            statement = statement.where(Application.status.in_(statuses))
        return statement

    async def count_for_student(
        self,
        student_id: UUID,
        statuses: Collection[ApplicationStatus] = (),
    ) -> int:
        return (
            await self.session.scalar(
                select(func.count()).select_from(self._owned(student_id, statuses).subquery())
            )
        ) or 0

    async def list_for_student(
        self,
        student_id: UUID,
        statuses: Collection[ApplicationStatus],
        offset: int,
        limit: int,
    ) -> list[Application]:
        statement = (
            self._owned(student_id, statuses)
            .options(
                joinedload(Application.request_type),
            )
            .order_by(Application.created_at.desc(), Application.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(await self.session.scalars(statement))

    async def get_for_student(self, application_id: UUID, student_id: UUID) -> Application | None:
        return await self.session.scalar(
            self._owned(student_id)
            .where(
                Application.id == application_id,
            )
            .options(joinedload(Application.request_type))
        )

    async def history_for_student(
        self,
        application_id: UUID,
        student_id: UUID,
    ) -> list[ApplicationEvent]:
        return list(
            await self.session.scalars(
                select(ApplicationEvent)
                .join(Application)
                .where(
                    ApplicationEvent.application_id == application_id,
                    Application.student_id == student_id,
                )
                .order_by(ApplicationEvent.created_at, ApplicationEvent.id)
            )
        )

    async def list_types(self) -> list[RequestType]:
        return list(
            await self.session.scalars(select(RequestType).order_by(RequestType.code.desc()))
        )

    async def get_type(self, code: str) -> RequestType | None:
        return await self.session.scalar(select(RequestType).where(RequestType.code == code))

    async def create(self, application: Application) -> Application:
        self.session.add(application)
        await self.session.flush()
        return application

    async def add_event(self, event: ApplicationEvent) -> ApplicationEvent:
        self.session.add(event)
        await self.session.flush()
        return event
