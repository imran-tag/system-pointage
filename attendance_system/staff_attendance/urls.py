from django.urls import path
from . import views

app_name = 'staff_attendance'

urlpatterns = [
    path('', views.attendance_page, name='attendance_page'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('manage-staff/', views.staff_management, name='staff_management'),
    path('api/staff/', views.get_staff_list, name='get_staff_list'),
    path('api/staff-by-city/', views.get_staff_by_city, name='get_staff_by_city'),
    path('api/update-staff-city/', views.update_staff_city, name='update_staff_city'),
    path('api/mark-present/', views.mark_present, name='mark_present'),
    path('api/mark-absent/', views.mark_absent, name='mark_absent'),
    path('api/mark-conge/', views.mark_conge, name='mark_conge'),
    path('api/mark-city-present/', views.mark_city_present, name='mark_city_present'),
    path('api/mark-all-present/', views.mark_all_present, name='mark_all_present'),
    path('api/verify-admin/', views.verify_admin, name='verify_admin'),
    path('api/generate-pdf/', views.generate_pdf, name='generate_pdf'),
    path('api/attendance-history/', views.get_attendance_history, name='get_attendance_history'),
    path('api/generate-history-pdf/', views.generate_history_pdf, name='generate_history_pdf'),
]