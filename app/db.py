from contextlib import contextmanager
from functools import cache
from typing import Annotated, Generator

from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine
import redis
import os

db_port = os.getenv("DB_PORT")
db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USERNAME")
db_pass = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
db_engine = create_engine(
    f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
)


def create_tables():
    SQLModel.metadata.create_all(db_engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(db_engine) as session:
        yield session


def _get_session():
    with get_session() as session:
        yield session


SessionDeps = Annotated[Session, Depends(_get_session)]


@cache
def get_redis() -> redis.Redis:
    redis_port = os.getenv("REDIS_PORT") or ""
    redis_host = os.getenv("REDIS_URL") or ""
    redis_db = os.getenv("REDIS_DB") or ""
    r = redis.Redis(host=redis_host, port=int(redis_port), db=int(redis_db))
    return r
