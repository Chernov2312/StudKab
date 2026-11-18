from uuid import UUID

from sqlalchemy import select

from app.db.dao.basedao import BaseDAO
from app.db.models import User


class UserDAO(BaseDAO):
    async def get_by_username(self, username: str) -> User | None:
        return await self.session.scalar(select(User).where(User.username == username))

    async def get_active_by_id(self, user_id: UUID) -> User | None:
        return await self.session.scalar(select(User).where(User.id == user_id, User.active))
