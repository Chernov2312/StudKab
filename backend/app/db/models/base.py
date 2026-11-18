from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, MetaData, func
from sqlalchemy.orm import DeclarativeBase, mapped_column

Id = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]
Timestamp = Annotated[datetime, mapped_column(DateTime(timezone=True))]
CreatedAt = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def choice[E: StrEnum](kind: type[E], name: str) -> Enum:
    return Enum(
        kind,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda options: [item.value for item in options],
    )
