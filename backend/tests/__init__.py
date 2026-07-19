import os

os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/smarthunt_test",
)

os.environ.setdefault(
    "DATABASE_URL",
    os.environ["TEST_DATABASE_URL"],
)
