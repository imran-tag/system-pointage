from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.utils import OperationalError
import os
import time


class Command(BaseCommand):
    help = 'Sets up the staff attendance system with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting setup for Staff Attendance System...'))

        # Wait for database to be available
        self.wait_for_db()

        # Run migrations
        self.stdout.write('Running migrations...')
        call_command('migrate')

        # Load initial data
        self.stdout.write('Loading initial data...')
        call_command('loaddata', 'initial_data.json')

        self.stdout.write(self.style.SUCCESS('Setup completed successfully!'))

    def wait_for_db(self):
        """Wait for database to be available"""
        self.stdout.write('Waiting for database...')
        db_conn = None
        while not db_conn:
            try:
                connection.ensure_connection()
                db_conn = True
            except OperationalError:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)