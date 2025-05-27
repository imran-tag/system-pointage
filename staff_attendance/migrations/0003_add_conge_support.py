# Create this file: staff_attendance/migrations/0003_add_conge_support.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff_attendance', '0002_attendance_absence_reason'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='present',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]