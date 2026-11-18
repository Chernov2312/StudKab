from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert

from app.db.dao.basedao import BaseDAO
from app.db.models import LoginAttempt


class LoginDAO(BaseDAO):
    async def consume(self, key: str, window: datetime, limit: int) -> bool:
        statement = insert(LoginAttempt).values(key=key, window=window, count=1)
        accepted = await self.session.scalar(
            statement.on_conflict_do_update(
                index_elements=[LoginAttempt.key, LoginAttempt.window],
                set_={"count": LoginAttempt.count + 1},
                where=LoginAttempt.count < limit,
            ).returning(LoginAttempt.count)
        )
        return accepted is not None

    async def prune(self, now: datetime) -> None:
        await self.session.execute(
            delete(LoginAttempt).where(
                LoginAttempt.window < now - timedelta(days=1),
            )
        )
