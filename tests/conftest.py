import pytest
import redis
from sqlmodel import SQLModel, Session
from app.db import db_engine
import app.tasks as tasks


@pytest.fixture(name="session")
def session_fixture():

    db_engine.url = "sqlite:///:memory:"

    SQLModel.metadata.create_all(db_engine)

    session = Session(db_engine)
    yield session

    SQLModel.metadata.drop_all(db_engine)
    session.close()
    db_engine.dispose()


r = redis.Redis("localhost", db=14)


@pytest.fixture(name="redis")
def mock_redis():
    yield r
    r.flushdb()


@pytest.fixture(autouse=True)
def config_celery():
    tasks.c.conf.update(
        broken_url="memory://",
        result_backend="cache+memory://",
        task_always_eager=True,  # Execute tasks synchronously
        task_eager_propagates=True,
    )
