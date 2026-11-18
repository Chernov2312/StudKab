from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import randbelow, token_urlsafe

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.domain import utcnow
from app.core.exceptions import ApiError
from app.core.security import digest, dummy_hash, passwords
from app.db.dao.login_dao import LoginDAO
from app.db.dao.session_dao import SessionDAO
from app.db.dao.user_dao import UserDAO
from app.db.models import Session, User
from app.schemas.auth import LoginInput, LoginOutput, SessionInfo, UserInfo


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: Session


async def authenticate(db: AsyncSession, token: str | None) -> AuthContext:
    if token is None or len(token) != 43:
        raise ApiError("UNAUTHORIZED")
    session = await SessionDAO(db).get_valid_by_hash(digest(token), utcnow())
    if session is None:
        raise ApiError("UNAUTHORIZED")
    user = await UserDAO(db).get_active_by_id(session.user_id)
    if user is None:
        raise ApiError("UNAUTHORIZED")
    return AuthContext(user, session)


async def throttle(db: AsyncSession, settings: Settings, username: str, ip: str) -> None:
    now = utcnow()
    span = settings.login_window_seconds
    seconds = int(now.timestamp())
    window = datetime.fromtimestamp(seconds - seconds % span, UTC)
    dao = LoginDAO(db)
    async with db.begin():
        if randbelow(64) == 0:
            await dao.prune(now)
        allowed = await dao.consume(f"ip:{digest(ip)}", window, settings.login_address_limit)
        if allowed:
            allowed = await dao.consume(
                f"user:{digest(username.casefold())}",
                window,
                settings.login_username_limit,
            )
    if not allowed:
        raise ApiError("RATE_LIMITED", headers={"Retry-After": str(span - seconds % span)})


async def login(
    db: AsyncSession,
    settings: Settings,
    body: LoginInput,
    ip: str,
    previous_token: str | None,
) -> tuple[LoginOutput, str]:
    await throttle(db, settings, body.username, ip)
    async with db.begin():
        user = await UserDAO(db).get_by_username(body.username)
        hashed = user.password_hash if user is not None and user.active else dummy_hash
        verified = await run_in_threadpool(passwords.verify, body.password, hashed)
        if not verified or user is None or not user.active:
            raise ApiError("INVALID_CREDENTIALS")
        token = token_urlsafe(32)
        now = utcnow()
        dao = SessionDAO(db)
        if previous_token is not None and len(previous_token) == 43:
            await dao.revoke_by_hash(digest(previous_token), now)
        expires_at = now + timedelta(seconds=settings.session_ttl_seconds)
        await dao.create_session(user.id, digest(token), token_urlsafe(32), expires_at)
        result = LoginOutput(
            user=UserInfo.model_validate(user),
            session=SessionInfo(expires_at=expires_at),
        )
    return result, token


async def logout(db: AsyncSession, auth: AuthContext) -> None:
    try:
        await SessionDAO(db).revoke_by_hash(
            auth.session.token_hash,
            utcnow(),
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise
