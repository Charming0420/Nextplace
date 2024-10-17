import threading

from nextplace.validator.database.database_manager import DatabaseManager
import bittensor as bt

"""
Helper class to setup database tables, indices
"""


class TableInitializer:
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager

    def create_tables(self) -> None:
        """
        Create all validator tables
        Returns:
            None
        """
        cursor, db_connection = self.database_manager.get_cursor()
        self._create_properties_table(cursor)
        self._create_scored_predictions_table(cursor)
        self._create_sales_table(cursor)
        self._create_miner_scores_table(cursor)
        self._create_active_miners_table(cursor)
        self._create_website_comms_table(cursor)
        db_connection.commit()
        cursor.close()
        db_connection.close()

    def _migrate_prediction_ids(self):
        current_thread = threading.current_thread().name
        bt.logging.trace(f"| {current_thread} | 💾 Migrating prediction ID's to new table")
        distinct_ids_query = """
            SELECT DISTINCT(nextplace_id)
            FROM predictions
        """
        ids_results = self.database_manager.query(distinct_ids_query)

        insert_query = """
            INSERT INTO ids (nextplace_id)
            VALUES(?)
        """
        values = [(result[0],) for result in ids_results]
        self.database_manager.query_and_commit_many(insert_query, values)

    def _create_sales_table(self, cursor) -> None:
        """
        Create the sales table
        Args:
            cursor: a database cursor

        Returns:
            None
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                nextplace_id TEXT PRIMARY KEY,
                property_id TEXT,
                sale_price REAL,
                sale_date DATETIME
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sale_date ON sales(sale_date)
        ''')

    def _create_scored_predictions_table(self, cursor) -> None:
        """
        Create the predictions table
        Args:
            cursor: a database cursor

        Returns:
            None
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scored_predictions (
                nextplace_id TEXT,
                market TEXT,
                miner_hotkey TEXT,
                predicted_sale_price REAL,
                predicted_sale_date DATE,
                prediction_timestamp DATETIME,
                sale_price REAL,
                sale_date DATE,
                score_timestamp DATETIME,
                PRIMARY KEY (nextplace_id, miner_hotkey)
                )
        ''')

    def _create_properties_table(self, cursor) -> None:
        """
        Create the properties table
        Args:
            cursor: a database cursor

        Returns:
            None
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                nextplace_id TEXT PRIMARY KEY,
                property_id TEXT,
                listing_id TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                price INTEGER,
                beds INTEGER,
                baths REAL,
                sqft INTEGER,
                lot_size INTEGER,
                year_built INTEGER,
                days_on_market INTEGER,
                latitude REAL,
                longitude REAL,
                property_type TEXT,
                last_sale_date TEXT,
                hoa_dues INTEGER,
                query_date TEXT,
                market TEXT
            )
        ''')


    def _create_miner_scores_table(self, cursor) -> None:
        """
        Create the miner scores table
        Args:
            cursor: a database cursor

        Returns:
            None
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS miner_scores (
                miner_hotkey TEXT PRIMARY KEY,
                lifetime_score REAL,
                total_predictions INTEGER,
                last_update_timestamp DATETIME
            )
        ''')


    def _create_active_miners_table(self, cursor) -> None:
        """
        Create the active miners table
        Args:
            cursor: a database cursor

        Returns:
            None
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_miners (
                miner_hotkey TEXT PRIMARY KEY
            )
        ''')

    def _create_website_comms_table(self, cursor) -> None:
        """
        Create the website_comms table
        Args:
            cursor: a database cursor

        Returns:
            None
        """
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS website_comms (
                nextplace_id TEXT,
                miner_hotkey TEXT,
                miner_coldkey TEXT,
                prediction_date DATETIME,
                predicted_sale_price REAL,
                predicted_sale_date DATE,
                already_sent INTEGER DEFAULT 0,
                PRIMARY KEY (nextplace_id, miner_hotkey)
            )
        ''')
