from django.contrib import admin
from .models import City, StaffMember, Attendance, CongeReservation


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# Dans admin.py
@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'date_fin_contrat', 'contract_status_display')
    list_filter = ('city', 'date_fin_contrat')
    search_fields = ('name',)

    def contract_status_display(self, obj):
        status = obj.contract_status
        if status == 'warning':
            return f"⚠️ Expire dans {obj.days_until_contract_end} jours"
        elif status == 'expire':
            return "❌ Expiré"
        elif status == 'active':
            return "✅ Actif"
        else:
            return "♾️ Indéterminé"

    contract_status_display.short_description = 'Statut Contrat'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'city_name', 'date', 'present', 'hours_worked', 'grand_deplacement', 'timestamp')
    list_filter = ('present', 'date', 'staff_member__city', 'grand_deplacement')
    search_fields = ('staff_member__name',)
    date_hierarchy = 'date'
    readonly_fields = ('timestamp',)

    def city_name(self, obj):
        return obj.staff_member.city.name

    city_name.short_description = 'City'
    city_name.admin_order_field = 'staff_member__city__name'

    fieldsets = (
        ('Informations de base', {
            'fields': ('staff_member', 'date', 'present')
        }),
        ('Détails de présence', {
            'fields': ('hours_worked', 'grand_deplacement', 'timestamp'),
            'classes': ('collapse',)
        }),
        ('Absence', {
            'fields': ('absence_reason',),
            'classes': ('collapse',)
        }),
    )


@admin.register(CongeReservation)
class CongeReservationAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'city_name', 'start_date', 'end_date', 'reason', 'created_at')
    list_filter = ('start_date', 'end_date', 'staff_member__city')
    search_fields = ('staff_member__name', 'reason')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at',)

    def city_name(self, obj):
        return obj.staff_member.city.name

    city_name.short_description = 'City'
    city_name.admin_order_field = 'staff_member__city__name'