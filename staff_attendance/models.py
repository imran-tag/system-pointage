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