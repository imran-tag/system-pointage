# Create this file: staff_attendance/management/commands/cleanup_past_conges.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from staff_attendance.models import CongeReservation


class Command(BaseCommand):
    help = 'Clean up past congé reservations that are no longer needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Clean congés older than X days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        # Calculate the cutoff date
        cutoff_date = timezone.now().date() - timezone.timedelta(days=days)

        # Find past congé reservations
        past_conges = CongeReservation.objects.filter(end_date__lt=cutoff_date)
        count = past_conges.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'No congé reservations older than {days} days found.')
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {count} congé reservations older than {days} days:')
            )
            for conge in past_conges:
                self.stdout.write(f'  - {conge.staff_member.name}: {conge.start_date} to {conge.end_date}')
        else:
            past_conges.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} past congé reservations older than {days} days.')
            )

# Usage:
# python manage.py cleanup_past_conges --dry-run  # See what would be deleted
# python manage.py cleanup_past_conges             # Delete congés older than 30 days
# python manage.py cleanup_past_conges --days=60   # Delete congés older than 60 days