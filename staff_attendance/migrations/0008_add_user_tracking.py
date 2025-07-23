# staff_attendance/migrations/0008_add_user_tracking.py

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('staff_attendance', '0007_alter_attendance_options_alter_city_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Créé par'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='updated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_attendances', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par'),
        ),
        migrations.AddField(
            model_name='congereservation',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Créé par'),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('admin', 'Administrateur'), ('manager', 'Manager'), ('user', 'Utilisateur')], default='user', max_length=20)),
                ('can_modify_all', models.BooleanField(default=False, verbose_name='Peut modifier toutes les présences')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_zones', models.ManyToManyField(blank=True, to='staff_attendance.zone', verbose_name='Zones assignées')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]