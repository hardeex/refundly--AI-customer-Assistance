"""Test database setup.

Tests run against a real Postgres database - a dedicated one, named after the
dev database with a "-test" suffix, so they never touch dev data. It's created
automatically if it doesn't exist yet, and the schema is (re)created once per
test session from the same models the app uses.

Rather than fight SQLAlchemy's session/transaction semantics against endpoint
code that calls db.commit() itself, each test gets a plain session and every
table is truncated afterwards - simpler to reason about than nested
transactions, and fast enough at this scale.
"""

import psycopg
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import api_customer_refund_system.models  # noqa: F401 - registers tables on Base.metadata
from api_customer_refund_system.core.config import get_settings
from api_customer_refund_system.db.base import Base


def _test_database_url() -> str:
    dev_url = get_settings().database_url
    prefix, _, dbname = dev_url.rpartition("/")
    return f"{prefix}/{dbname}-test"


def _ensure_database_exists(database_url: str) -> None:
    plain_url = database_url.replace("postgresql+psycopg://", "postgresql://")
    prefix, _, dbname = plain_url.rpartition("/")
    conn = psycopg.connect(f"{prefix}/postgres", autocommit=True)
    try:
        row = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)
        ).fetchone()
        if row is None:
            conn.execute(f'CREATE DATABASE "{dbname}"')
    finally:
        conn.close()


TEST_DATABASE_URL = _test_database_url()
_ensure_database_exists(TEST_DATABASE_URL)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def _test_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
