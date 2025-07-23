# staff_attendance/management/commands/create_admin.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from staff_attendance.models import UserProfile, Zone


class Command(BaseCommand):
    help = 'Create an admin user with default credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Admin username (default: admin)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Admin password (default: admin123)',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Admin',
            help='Admin first name (default: Admin)',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='User',
            help='Admin last name (default: User)',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists.')
            )
            return

        # Create the admin user
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=True
            )

            # Create user profile
            profile = UserProfile.objects.create(
                user=user,
                role='admin',
                can_modify_all=True
            )

            # Assign all zones to admin (if any exist)
            zones = Zone.objects.all()
            if zones.exists():
                profile.assigned_zones.set(zones)
                self.stdout.write(f'Assigned {zones.count()} zones to admin user')

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user: {username}')
            )
            self.stdout.write(f'Password: {password}')
            self.stdout.write(f'Name: {first_name} {last_name}')
            self.stdout.write(f'Role: Admin')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {e}')
            )

# Usage:
# python manage.py create_admin
# python manage.py create_admin --username=boss --password=secret123