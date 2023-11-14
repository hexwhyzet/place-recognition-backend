import json
from enum import Enum as PythonEnum
from typing import Optional, List

from sqlalchemy import Column, Enum as SQLAlchemyEnum
from sqlmodel import Field, Relationship, SQLModel

from models.base import BaseSQLModel


class LanguageCode(PythonEnum):
    # picked up from ISO
    RU = 1  # Russian
    EN = 2  # English
    ZH = 3  # Chinese


class Translation(BaseSQLModel, table=True):
    text_content_id: Optional[int] = Field(
        foreign_key="text_content.id",
        nullable=False,
        exclude=True,
    )
    text_content: Optional["TextContent"] = Relationship(
        back_populates="translations",
    )
    text: str = Field(nullable=False)
    language: LanguageCode = Field(
        sa_column=Column(
            SQLAlchemyEnum(LanguageCode),
            nullable=False,
        )
    )


class TextContent(BaseSQLModel, table=True):
    translations: List[Translation] = Relationship(
        back_populates="text_content",
        sa_relationship_kwargs={"cascade": "delete"}
    )


class TextContentRead(SQLModel):
    translations: List[Translation] = None

    def dict(self, *args, **kwargs):
        result = {str(translation.language.name): translation.text for translation in self.__dict__.get('translations')}
        result['languages'] = list(result.keys())
        return result

    def json(self, *args, **kwargs):
        return json.dumps(self.dict(**kwargs))
