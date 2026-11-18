from typing import Literal

from app.schemas.common import DTO


class Live(DTO):
    status: Literal["ok"] = "ok"


class Ready(DTO):
    status: Literal["ready"] = "ready"
    database: Literal["ok"] = "ok"
