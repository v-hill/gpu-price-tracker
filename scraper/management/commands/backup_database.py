"""
Backup an existing database with a timestamp.
Run this script using `python manage.py backup_database`
"""

import datetime
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Make a backup of the sqlite3 database."

    def handle(self, *args, **kwargs):
        database_path = settings.DATABASES["default"]["NAME"]
        if os.path.exists(database_path):
            old_name = database_path.stem
            new_name = f"{datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S')}_{old_name}{database_path.suffix}"
            new_database_path = database_path.parent / new_name
            self.stdout.write(f"Backing up database to: {new_database_path}")
            shutil.copy(database_path, new_database_path)
            self.stdout.write(
                self.style.SUCCESS("Successfully backed up database!")
            )
