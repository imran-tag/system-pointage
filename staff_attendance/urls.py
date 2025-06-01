from django.urls import path
from . import views

app_name = 'staff_attendance'

path('api/cities/', views.get_cities_list, name='get_cities_list'),

urlpatterns = [
    path('', views.attendance_page, name='attendance_page'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('manage-staff/', views.staff_management, name='staff_management'),

    # Staff API endpoints
    path('api/staff/', views.get_staff_list, name='get_staff_list'),
    path('api/staff-by-city/', views.get_staff_by_city, name='get_staff_by_city'),
    path('api/update-staff-city/', views.update_staff_city, name='update_staff_city'),

    # Attendance API endpoints
    path('api/mark-present/', views.mark_present, name='mark_present'),
    path('api/mark-absent/', views.mark_absent, name='mark_absent'),
    path('api/mark-conge/', views.mark_conge, name='mark_conge'),
    path('api/mark-city-present/', views.mark_city_present, name='mark_city_present'),
    path('api/mark-all-present/', views.mark_all_present, name='mark_all_present'),

    # City management API endpoints
    path('api/cities/', views.get_cities_list, name='get_cities_list'),
    path('api/add-city/', views.add_city, name='add_city'),
    path('api/update-city-name/', views.update_city_name, name='update_city_name'),
    path('api/delete-city/', views.delete_city, name='delete_city'),

    # Congé period API endpoints
    path('api/mark-conge-period/', views.mark_conge_with_period, name='mark_conge_with_period'),
    path('api/conge-reservations/', views.get_conge_reservations, name='get_conge_reservations'),
    path('api/remove-conge-reservation/', views.remove_conge_reservation, name='remove_conge_reservation'),

    # Admin and reports
    path('api/verify-admin/', views.verify_admin, name='verify_admin'),
    path('api/generate-pdf/', views.generate_pdf, name='generate_pdf'),
    path('api/attendance-history/', views.get_attendance_history, name='get_attendance_history'),
    path('api/generate-history-pdf/', views.generate_history_pdf, name='generate_history_pdf'),
]