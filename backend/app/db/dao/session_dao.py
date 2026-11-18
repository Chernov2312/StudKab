from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update

from app.db.dao.basedao import BaseDAO
from app.db.models import Session


class SessionDAO(BaseDAO):
    async def create_session(
        self, user_id: UUID, token_hash: str, csrf_token: str, expires_at: datetime
    ) -> Session:
        record = Session(
            user_id=user_id,
            token_hash=token_hash,
            csrf_token=csrf_token,
            expires_at=expires_at,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_valid_by_hash(self, token_hash: str, now: datetime) -> Session | None:
        return await self.session.scalar(
            select(Session).where(
                Session.token_hash == token_hash,
                Session.revoked_at.is_(None),
                Session.expires_at > now,
            )
        )

    async def revoke_by_hash(self, token_hash: str, now: datetime) -> None:
        await self.session.execute(
            update(Session)
            .where(
                Session.token_hash == token_hash,
                Session.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
