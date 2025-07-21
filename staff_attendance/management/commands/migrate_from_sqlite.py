from django.core.management.base import BaseCommand
from staff_attendance.models import City, StaffMember
import sqlite3
import os


class Command(BaseCommand):
    help = 'Migrate data from SQLite to new database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sqlite-path',
            type=str,
            default='db.sqlite3',
            help='Path to SQLite database file',
        )

    def handle(self, *args, **options):
        sqlite_path = options['sqlite_path']

        if not os.path.exists(sqlite_path):
            self.stdout.write(
                self.style.ERROR(f'SQLite file not found: {sqlite_path}')
            )
            return

        # Connect to SQLite database
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()

        try:
            # Migrate Cities
            self.stdout.write('Migrating cities...')
            cursor.execute("SELECT id, name FROM staff_attendance_city")
            cities = cursor.fetchall()

            for city_id, city_name in cities:
                city, created = City.objects.get_or_create(
                    name=city_name
                )
                if created:
                    self.stdout.write(f'  Created city: {city_name}')
                else:
                    self.stdout.write(f'  City already exists: {city_name}')

            # Migrate Staff Members
            self.stdout.write('Migrating staff members...')
            cursor.execute("""
                SELECT sm.id, sm.name, c.name as city_name 
                FROM staff_attendance_staffmember sm
                JOIN staff_attendance_city c ON sm.city_id = c.id
            """)
            staff_members = cursor.fetchall()

            for staff_id, staff_name, city_name in staff_members:
                city = City.objects.get(name=city_name)
                staff, created = StaffMember.objects.get_or_create(
                    name=staff_name,
                    defaults={'city': city}
                )
                if created:
                    self.stdout.write(f'  Created staff: {staff_name} in {city_name}')
                else:
                    self.stdout.write(f'  Staff already exists: {staff_name}')

            # Note: We're not migrating attendance records as they're daily data
            # and you probably want to start fresh

            self.stdout.write(
                self.style.SUCCESS('Migration completed successfully!')
            )
            self.stdout.write(
                'Note: Attendance records were not migrated. You can start fresh with daily tracking.'
            )

        except sqlite3.Error as e:
            self.stdout.write(
                self.style.ERROR(f'SQLite error: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during migration: {e}')
            )
        finally:
            conn.close()