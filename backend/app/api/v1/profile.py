from fastapi import APIRouter

from app.core.dependencies import CurrentStudent
from app.schemas.profile import Profile

router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=Profile)
async def profile(student: CurrentStudent) -> Profile:
    return student.profile
