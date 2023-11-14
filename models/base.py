from typing import Optional

from sqlalchemy import Column, BigInteger
from sqlalchemy.orm import declared_attr
from sqlmodel import SQLModel, Field

from libs.utils import camel_to_snake


class TableNameSQLMode(SQLModel):
    @declared_attr
    def __tablename__(cls) -> str:
        return camel_to_snake(cls.__name__)


class BaseSQLModel(TableNameSQLMode):
    id: Optional[int] = Field(sa_column=Column(BigInteger, primary_key=True))
