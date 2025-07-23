# staff_attendance/urls.py - Fixed URLs to prevent redirect loop

from django.urls import path
from . import views

app_name = 'staff_attendance'

urlpatterns = [
    # Authentication URLs - These should come FIRST
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/login/', views.login_api, name='login_api'),
    path('api/current-user/', views.get_current_user, name='get_current_user'),

    # Main application URLs
    path('', views.home_redirect, name='home_redirect'),  # This handles the root redirect
    path('attendance/', views.attendance_page, name='attendance_page'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('manage-staff/', views.staff_management, name='staff_management'),
    path('users/', views.user_management, name='user_management'),

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

    # Zone management API endpoints
    path('api/zones/', views.get_zones_list, name='get_zones_list'),

    # City management API endpoints
    path('api/cities/', views.get_cities_list, name='get_cities_list'),
    path('api/add-city/', views.add_city, name='add_city'),
    path('api/update-city-name/', views.update_city_name, name='update_city_name'),
    path('api/delete-city/', views.delete_city, name='delete_city'),

    # Congé period API endpoints
    path('api/mark-conge-period/', views.mark_conge_with_period, name='mark_conge_with_period'),
    path('api/conge-reservations/', views.get_conge_reservations, name='get_conge_reservations'),
    path('api/remove-conge-reservation/', views.remove_conge_reservation, name='remove_conge_reservation'),
    path('api/remove-daily-conge/', views.remove_daily_conge, name='remove_daily_conge'),

    # User management API endpoints
    path('api/users/', views.get_users_list, name='get_users_list'),
    path('api/create-user/', views.create_user, name='create_user'),
    path('api/delete-user/', views.delete_user, name='delete_user'),

    # Admin and reports
    path('api/verify-admin/', views.verify_admin, name='verify_admin'),
    path('api/generate-pdf/', views.generate_pdf, name='generate_pdf'),
    path('api/attendance-history/', views.get_attendance_history, name='get_attendance_history'),
    path('api/generate-history-pdf/', views.generate_history_pdf, name='generate_history_pdf'),
    path('api/cleanup-past-conges/', views.cleanup_past_conges, name='cleanup_past_conges'),
]