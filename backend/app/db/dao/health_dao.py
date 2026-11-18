from sqlalchemy import select

from app.db.dao.basedao import BaseDAO


class HealthDAO(BaseDAO):
    async def ping(self) -> None:
        await self.session.execute(select(1))
