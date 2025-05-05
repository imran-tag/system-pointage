from django.contrib import admin
from .models import City, StaffMember, Attendance


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')
    list_filter = ('city',)
    search_fields = ('name',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'city_name', 'date', 'present', 'timestamp')
    list_filter = ('present', 'date', 'staff_member__city')
    search_fields = ('staff_member__name',)
    date_hierarchy = 'date'

    def city_name(self, obj):
        return obj.staff_member.city.name

    city_name.short_description = 'City'
    city_name.admin_order_field = 'staff_member__city__name'