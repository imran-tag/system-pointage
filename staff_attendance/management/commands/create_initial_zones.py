# staff_attendance/management/commands/create_initial_zones.py

from django.core.management.base import BaseCommand
from staff_attendance.models import Zone


class Command(BaseCommand):
    help = 'Create initial zones'

    def handle(self, *args, **options):
        zones = [
            'Zone Nord',
            'Zone Sud',
            'Zone Est',
            'Zone Ouest'
        ]

        created_count = 0
        for zone_name in zones:
            zone, created = Zone.objects.get_or_create(name=zone_name)
            if created:
                created_count += 1
                self.stdout.write(f'Créé: {zone_name}')
            else:
                self.stdout.write(f'Existe déjà: {zone_name}')

        self.stdout.write(
            self.style.SUCCESS(f'Terminé! {created_count} nouvelles zones créées.')
        )