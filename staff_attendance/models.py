# staff_attendance/models.py - Updated with user tracking

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Zone(models.Model):
    """Model for zones that contain cities/chantiers"""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='cities', null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name']


class StaffMember(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='staff_members')
    date_fin_contrat = models.DateField(null=True, blank=True, verbose_name="Date de fin de contrat")  # NOUVEAU CHAMP

    def __str__(self):
        return self.name

    @property
    def contract_status(self):
        """Retourne le statut du contrat"""
        if not self.date_fin_contrat:
            return 'indefini'  # Contrat à durée indéterminée

        today = timezone.now().date()
        days_remaining = (self.date_fin_contrat - today).days

        if days_remaining < 0:
            return 'expire'  # Contrat expiré
        elif days_remaining <= 7:
            return 'warning'  # Attention - expire dans une semaine
        else:
            return 'active'  # Contrat actif

    @property
    def days_until_contract_end(self):
        """Retourne le nombre de jours avant la fin du contrat"""
        if not self.date_fin_contrat:
            return None

        today = timezone.now().date()
        return (self.date_fin_contrat - today).days


class Attendance(models.Model):
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    present = models.BooleanField(null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    absence_reason = models.TextField(verbose_name="Motif d'absence", null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                       verbose_name="Heures travaillées")
    grand_deplacement = models.BooleanField(default=False, verbose_name="Grand déplacement (nuit)")

    chantier_at_time = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True,
                                         verbose_name="Chantier au moment de la présence")

    # NEW: Track which user made the change
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créé par")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='updated_attendances', verbose_name="Modifié par")

    class Meta:
        unique_together = ['staff_member', 'date']
        ordering = ['-date', 'staff_member__name']

    def __str__(self):
        if self.absence_reason == 'CONGE_STATUS':
            status = "En congé"
        elif self.present is True:
            status = f"Present ({self.hours_worked}h)" if self.hours_worked else "Present"
            if self.grand_deplacement:
                status += " - Grand déplacement"
        elif self.present is False:
            status = "Absent"
        else:
            status = "Non défini"
        return f"{self.staff_member.name} - {self.date} - {status}"

    @property
    def status(self):
        """Return the actual status of attendance"""
        if self.absence_reason == 'CONGE_STATUS':
            return 'conge'
        elif self.present is True:
            return 'present'
        elif self.present is False:
            return 'absent'
        else:
            return 'undefined'


class CongeReservation(models.Model):
    """Model to store congé reservations with date ranges"""
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='conge_reservations')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True, null=True, verbose_name="Motif du congé")
    created_at = models.DateTimeField(auto_now_add=True)

    # NEW: Track which user created the congé
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Créé par")

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.staff_member.name} - Congé du {self.start_date} au {self.end_date}"

    @property
    def is_active(self):
        """Check if the congé is currently active"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    @property
    def is_past(self):
        """Check if the congé is completely in the past"""
        today = timezone.now().date()
        return self.end_date < today

    @property
    def is_future(self):
        """Check if the congé is completely in the future"""
        today = timezone.now().date()
        return self.start_date > today

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.create_attendance_records()

    def create_attendance_records(self):
        """Create attendance records for each day in the congé period"""
        current_date = self.start_date
        while current_date <= self.end_date:
            attendance, created = Attendance.objects.get_or_create(
                staff_member=self.staff_member,
                date=current_date,
                defaults={
                    'present': None,
                    'absence_reason': 'CONGE_STATUS',
                    'timestamp': timezone.now(),
                    'created_by': self.created_by
                }
            )

            if not created and attendance.absence_reason != 'CONGE_STATUS':
                attendance.present = None
                attendance.absence_reason = 'CONGE_STATUS'
                attendance.timestamp = timezone.now()
                attendance.updated_by = self.created_by
                attendance.save()

            current_date += timezone.timedelta(days=1)

    def delete(self, *args, **kwargs):
        Attendance.objects.filter(
            staff_member=self.staff_member,
            date__gte=self.start_date,
            date__lte=self.end_date,
            absence_reason='CONGE_STATUS'
        ).delete()
        super().delete(*args, **kwargs)


# NEW: User Profile model to extend User functionality
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=[
        ('admin', 'Administrateur'),
        ('manager', 'Manager'),
        ('user', 'Utilisateur')
    ], default='user')
    can_modify_all = models.BooleanField(default=False, verbose_name="Peut modifier toutes les présences")
    assigned_zones = models.ManyToManyField(Zone, blank=True, verbose_name="Zones assignées")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role in ['admin', 'manager']