from pathlib import Path

from database.connection import connect


def setup_database() -> None:
    statement = Path(__file__).with_name("schema.sql").read_text(
        encoding="ascii"
    ).strip()

    connection = connect()

    try:
        with connection.cursor() as cursor:
            cursor.execute(statement)

        connection.commit()

    finally:
        connection.close()