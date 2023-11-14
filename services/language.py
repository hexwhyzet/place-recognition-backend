from sqlalchemy import select
from sqlmodel import Session

from models import TextContent
from models.language import LanguageCode, Translation


def create_text_content(session: Session, **kwargs):
    text_content = TextContent()
    session.add(text_content)
    session.flush()
    for language, text in kwargs.items():
        if language not in LanguageCode.__members__:
            raise Exception(f"Unkown language specified: {language}")

        for language_code in LanguageCode:
            if language_code.name == language.upper():
                translation = Translation(
                    text_content_id=text_content.id,
                    text=text,
                    language=language_code
                )
                session.add(translation)
                break

    session.flush()
    return text_content


def translation_exists(session: Session, text_content: TextContent, text: str, language: LanguageCode):
    statement = select(Translation).where(Translation.text_content == text_content).where(text == text).where(
        language == language)
    results = session.exec(statement)
    return len(results.all()) > 0
