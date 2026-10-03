
"""Queries for the existing flight_game schema and game_save table."""

from typing import Any

from database.connection import connect


class GameRepository:
    def list_saves(self) -> list[dict[str, Any]]:
        connection = connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT s.save_name, s.game_id, s.saved_at, g.location "
                    "FROM game_save AS s JOIN game AS g ON g.id = s.game_id "
                    "ORDER BY s.save_name"
                )
                return list(cursor.fetchall())
        finally:
            connection.close()