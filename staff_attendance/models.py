from django.db import models
from django.utils import timezone


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Cities"


class StaffMember(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='staff_members')

    def __str__(self):
        return self.name


class Attendance(models.Model):
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    present = models.BooleanField(null=True, blank=True)  # Now allows NULL for congé
    timestamp = models.DateTimeField(null=True, blank=True)
    absence_reason = models.TextField(verbose_name="Motif d'absence", null=True, blank=True)

    class Meta:
        unique_together = ['staff_member', 'date']

    def __str__(self):
        if self.absence_reason == 'CONGE_STATUS':
            status = "En congé"
        elif self.present is True:
            status = "Present"
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