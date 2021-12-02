"""
Script for batch converting the legacy json "database" into the new sqlite 
database format.
"""
import os

from sqlalchemy.orm import sessionmaker

from configuration import PATHS
from scraper.scraper import create_database, delete_database, get_engine
from utilities.json_to_sql import import_json_data

# ------------------------------ Database setup -------------------------------

database_path = PATHS["database"]
engine = get_engine(database_path, quite=True)
Session = sessionmaker(bind=engine)

# delete_database(database_path)
create_database(engine, database_path)

# ----------------------------- Import json data ------------------------------

try:
    from configuration import raw_data_filepath
except:
    raise Exception("Please define the path to the .json files")

import_json_data(Session, raw_data_filepath)
