# Create this file: staff_attendance/migrations/0004_add_conge_reservation.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('staff_attendance', '0003_add_conge_support'),
    ]

    operations = [
        migrations.CreateModel(
            name='CongeReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField(blank=True, null=True, verbose_name='Motif du congé')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('staff_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conge_reservations', to='staff_attendance.staffmember')),
            ],
            options={
                'ordering': ['start_date'],
            },
        ),
    ]