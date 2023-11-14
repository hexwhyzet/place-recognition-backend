from os import environ

from sqlmodel import create_engine, Session

DATABASE_URL = f"postgresql://{environ.get('DB_USER')}:{environ.get('DB_PASSWORD')}@{environ.get('DB_HOST')}:{environ.get('DB_PORT')}/{environ.get('DB_DATABASE')}"

ENGINE = create_engine(DATABASE_URL, echo=False)


def GetSQLModelSession() -> Session:
    return Session(ENGINE)
