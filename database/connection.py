"""MariaDB connection configuration loaded from environment variables."""

import os
from pathlib import Path


def connect():
    try:
        import pymysql
    except ImportError as error:
        raise RuntimeError("Install dependencies with: python -m pip install -r requirements.txt") from error

    try:
        from dotenv import load_dotenv
    except ImportError as error:
        raise RuntimeError("Install dependencies with: python -m pip install -r requirements.txt") from error

    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env", override=True)

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    if not user or password is None:
        raise RuntimeError("Set DB_USER and DB_PASSWORD in the project .env file before starting the game.")

    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=user,
        password=password,
        database=os.getenv("DB_NAME", "flight_game"),
        charset="latin1",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )