# Create this file: staff_attendance/migrations/0005_add_hours_and_grand_deplacement.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff_attendance', '0004_add_conge_reservation'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='hours_worked',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, verbose_name='Heures travaillées'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='grand_deplacement',
            field=models.BooleanField(default=False, verbose_name='Grand déplacement (nuit)'),
        ),
    ]