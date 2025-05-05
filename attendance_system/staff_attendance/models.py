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
    date = models.DateField(default=timezone.now) # obv for the date in the format hh:mm:ss
    present = models.BooleanField(default=False) # si c'est present
    timestamp = models.DateTimeField(null=True, blank=True) # timestampping

    class Meta:
        unique_together = ['staff_member', 'date']

    def __str__(self):
        status = "Present" if self.present else "Absent"
        return f"{self.staff_member.name} - {self.date} - {status}"