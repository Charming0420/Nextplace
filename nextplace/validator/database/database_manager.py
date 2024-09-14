import sqlite3
from typing import Tuple
import os
from threading import RLock

"""
Helper class manager connections to the SQLite database
"""


class DatabaseManager:

    def __init__(self):
        os.makedirs('data', exist_ok=True)  # Ensure data directory exists
        self.db_path = 'data/validator_v2.db'  # Set db path
        db_dir = os.path.dirname(self.db_path)
        self.lock = RLock()  # Reentrant lock for thread safety
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)  # Create db dir

    def query(self, query: str) -> list:
        """
        Get all results of a query from the database
        Args:
            query: a query string

        Returns:
            All rows matching the query
        """
        cursor, db_connection = self.get_cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        db_connection.close()
        return rows

    def query_and_commit(self, query: str) -> None:
        """
        Use for updating the database
        Args:
            query: query string

        Returns:
            None
        """
        cursor, db_connection = self.get_cursor()
        cursor.execute(query)
        db_connection.commit()
        cursor.close()
        db_connection.close()

    def get_cursor(self) -> Tuple[sqlite3.Cursor, sqlite3.Connection]:
        """
        Get a cursor and connection reference from the database
        Returns:
            cursor & connection objects
        """
        db_connection = self.get_db_connection()
        cursor = db_connection.cursor()
        return cursor, db_connection

    def get_db_connection(self) -> sqlite3.Connection:
        """
        Get a reference to the database
        Returns:
            A database connection
        """
        return sqlite3.connect(self.db_path)

    def delete_all_sales(self) -> None:
        """
        Delete all rows from the sales table
        Returns:
            None
        """
        self.query_and_commit('DELETE FROM sales')

    def delete_all_properties(self) -> None:
        """
        Delete all rows from the sales table
        Returns:
            None
        """
        self.query_and_commit('DELETE FROM properties')

    def get_size_of_table(self, table_name: str):
        cursor, db_connection = self.get_cursor()
        query = f"SELECT COUNT(*) FROM {table_name}"
        cursor.execute(query)
        row_count = cursor.fetchone()[0]
        cursor.close()
        db_connection.close()
        return row_count

