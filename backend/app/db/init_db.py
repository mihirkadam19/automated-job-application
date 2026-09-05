from app.db import models  # noqa: F401  registers models on Base.metadata
from app.db.base import Base, DB_PATH, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
