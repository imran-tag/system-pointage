# staff_attendance/models.py
from django.db import models
from django.utils import timezone


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

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Attendance(models.Model):
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    present = models.BooleanField(null=True, blank=True)  # Now allows NULL for congé
    timestamp = models.DateTimeField(null=True, blank=True)
    absence_reason = models.TextField(verbose_name="Motif d'absence", null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, verbose_name="Heures travaillées")
    grand_deplacement = models.BooleanField(default=False, verbose_name="Grand déplacement (nuit)")

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

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.staff_member.name} - Congé du {self.start_date} au {self.end_date}"

    @property
    def is_active(self):
        """Check if the congé is currently active (today is within the date range)"""
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
        # Automatically create attendance records for the congé period
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
                    'timestamp': timezone.now()
                }
            )

            # Update existing record if it's not already a congé
            if not created and attendance.absence_reason != 'CONGE_STATUS':
                attendance.present = None
                attendance.absence_reason = 'CONGE_STATUS'
                attendance.timestamp = timezone.now()
                attendance.save()

            current_date += timezone.timedelta(days=1)

    def delete(self, *args, **kwargs):
        # Remove attendance records for this congé period
        Attendance.objects.filter(
            staff_member=self.staff_member,
            date__gte=self.start_date,
            date__lte=self.end_date,
            absence_reason='CONGE_STATUS'
        ).delete()
        super().delete(*args, **kwargs)

    @classmethod
    def cleanup_past_records(cls):
        """
        Utility method to clean up past congé records if needed.
        This can be called manually or via a management command.
        """
        today = timezone.now().date()
        past_conges = cls.objects.filter(end_date__lt=today)
        count = past_conges.count()
        # Uncomment the line below if you want to automatically delete past congé records
        # past_conges.delete()
        return count