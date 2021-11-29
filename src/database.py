"""
Module for database related classes and functions.
"""
import logging
from os import path

from models import Base


class Scraper:
    """
    Scraper utility class.
    """

    def __init__(self, engine, database_path: str):
        self.engine = engine
        self.database_path = database_path
        self.products = []
        self.make_database()

    def make_database(self):
        """
        Create sqlite database if no current database exists.
        """
        if path.exists(self.database_path):
            logging.info(f"Database already exists at: {self.database_path}")
        else:
            logging.info(f"Creating database at: {self.database_path}")
            Base.metadata.create_all(self.engine)
