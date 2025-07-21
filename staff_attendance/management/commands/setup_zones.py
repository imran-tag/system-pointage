# staff_attendance/management/commands/setup_zones.py

from django.core.management.base import BaseCommand
from staff_attendance.models import Zone, City
import random


class Command(BaseCommand):
    help = 'Setup zones and assign existing cities to zones'

    def handle(self, *args, **options):
        # Create zones
        zones = [
            'Zone Nord',
            'Zone Sud',
            'Zone Est',
            'Zone Ouest'
        ]

        created_zones = []
        for zone_name in zones:
            zone, created = Zone.objects.get_or_create(name=zone_name)
            created_zones.append(zone)
            if created:
                self.stdout.write(f'✓ Créé: {zone_name}')
            else:
                self.stdout.write(f'- Existe déjà: {zone_name}')

        # Assign existing cities to zones randomly if they don't have a zone
        unassigned_cities = City.objects.filter(zone__isnull=True)

        if unassigned_cities.exists():
            self.stdout.write(f'\nAssignation de {unassigned_cities.count()} chantiers aux zones...')

            for city in unassigned_cities:
                # Assign randomly, or you can customize this logic
                zone = random.choice(created_zones)
                city.zone = zone
                city.save()
                self.stdout.write(f'- {city.name} → {zone.name}')
        else:
            self.stdout.write('\nTous les chantiers sont déjà assignés à des zones.')

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Configuration terminée!')
        )

        # Print summary
        self.stdout.write('\n📊 Résumé:')
        for zone in created_zones:
            city_count = zone.cities.count()
            self.stdout.write(f'  {zone.name}: {city_count} chantier(s)')

# Usage: python manage.py setup_zones