from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import json
import datetime
from django.db.models import Count, Q
import os

from .models import City, StaffMember, Attendance

# Generate PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO


def attendance_page(request):
    """Render the main attendance page"""
    cities = City.objects.all()
    admin_password = settings.ADMIN_PASSWORD if hasattr(settings, 'ADMIN_PASSWORD') else "admin123"
    return render(request, 'staff_attendance/attendance.html', {
        'cities': cities,
        'admin_password': admin_password,
    })


def attendance_history(request):
    """Render the attendance history page"""
    cities = City.objects.all()
    admin_password = settings.ADMIN_PASSWORD if hasattr(settings, 'ADMIN_PASSWORD') else "admin123"
    return render(request, 'staff_attendance/attendance_history.html', {
        'cities': cities,
        'admin_password': admin_password,
    })


def staff_management(request):
    """Render the staff management page for drag and drop functionality"""
    cities = City.objects.all()
    return render(request, 'staff_attendance/staff_management.html', {
        'cities': cities,
    })


@csrf_exempt
def get_attendance_history(request):
    """API endpoint to get attendance history for the past 30 days"""
    # Calculate the date 30 days ago from today
    end_date = timezone.now().date()
    start_date = end_date - datetime.timedelta(days=30)

    # Get all staff members with their cities
    staff_members = StaffMember.objects.select_related('city').all()

    # Get attendance records for the past 30 days
    attendances = Attendance.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('-date')

    # Group attendances by date
    attendance_by_date = {}

    # Initialize all dates with empty dictionaries
    current_date = start_date
    while current_date <= end_date:
        attendance_by_date[current_date.isoformat()] = {
            'date': current_date.isoformat(),
            'display_date': current_date.strftime('%d/%m/%Y'),
            'weekday': current_date.strftime('%A'),
            'staff': {}
        }
        current_date += datetime.timedelta(days=1)

    # Fill in attendance data
    for attendance in attendances:
        date_key = attendance.date.isoformat()
        if date_key in attendance_by_date:
            if attendance.absence_reason == 'CONGE_STATUS':
                status = 'conge'
            elif attendance.present is True:
                status = 'present'
            elif attendance.present is False:
                status = 'absent'
            else:
                status = 'undefined'

            attendance_by_date[date_key]['staff'][attendance.staff_member_id] = {
                'status': status,
                'absence_reason': attendance.absence_reason if attendance.present is False and attendance.absence_reason != 'CONGE_STATUS' else None,
                'timestamp': attendance.timestamp.isoformat() if attendance.timestamp else None
            }

    # Convert to a list and sort by date (newest first)
    history_data = list(attendance_by_date.values())
    history_data.sort(key=lambda x: x['date'], reverse=True)

    # Prepare staff info
    staff_info = []
    for staff in staff_members:
        staff_info.append({
            'id': staff.id,
            'name': staff.name,
            'city': staff.city.name
        })

    return JsonResponse({
        'history': history_data,
        'staff': staff_info
    })


@csrf_exempt
def generate_history_pdf(request):
    """API endpoint to generate a PDF report of attendance history"""
    if request.method == 'POST':
        try:
            # Get time period
            end_date = timezone.now().date()
            start_date = end_date - datetime.timedelta(days=30)

            # Get all staff with their attendance
            staff_members = StaffMember.objects.select_related('city').all()

            # Get attendance records for the period
            attendances = Attendance.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).order_by('-date')

            # Create a dictionary for quick lookup
            attendance_dict = {}
            for attendance in attendances:
                key = (attendance.date, attendance.staff_member_id)
                attendance_dict[key] = attendance

            # Create a BytesIO buffer for the PDF
            buffer = BytesIO()

            # Create the PDF object
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30)
            elements = []

            # Set up styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            subtitle_style = styles['Heading2']
            normal_style = styles['Normal']
            date_style = styles['Heading3']

            # Add title
            elements.append(Paragraph("Historique de Présence du Personnel", title_style))
            elements.append(Spacer(1, 12))

            # Add date range
            date_range = f"Période: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            elements.append(Paragraph(date_range, subtitle_style))
            elements.append(Spacer(1, 20))

            # Group staff by city
            staff_by_city = {}
            for staff in staff_members:
                if staff.city.name not in staff_by_city:
                    staff_by_city[staff.city.name] = []
                staff_by_city[staff.city.name].append(staff)

            # For each city, create a section
            for city_name, city_staff in staff_by_city.items():
                elements.append(Paragraph(f"Ville: {city_name}", subtitle_style))
                elements.append(Spacer(1, 10))

                # Get all dates in the range
                dates = []
                current_date = start_date
                while current_date <= end_date:
                    dates.append(current_date)
                    current_date += datetime.timedelta(days=1)

                # Create table header with dates
                header = ["Nom"]
                for date in dates:
                    header.append(date.strftime('%d/%m'))

                # Create table data
                data = [header]

                # Add staff rows
                for staff in city_staff:
                    row = [staff.name]

                    # Add status for each date
                    for date in dates:
                        key = (date, staff.id)
                        attendance = attendance_dict.get(key)

                        if attendance:
                            if attendance.absence_reason == 'CONGE_STATUS':
                                status = "C"  # Congé
                            elif attendance.present is True:
                                status = "P"  # Present
                            elif attendance.present is False:
                                status = "A"  # Absent
                                if attendance.absence_reason:
                                    status = "A*"  # Absent with reason
                            else:
                                status = "-"  # Undefined
                        else:
                            status = "-"  # No record

                        row.append(status)

                    data.append(row)

                # Create the table
                col_widths = [120] + [20] * len(dates)  # Name column wider than date columns
                table = Table(data, colWidths=col_widths)

                # Style the table
                table_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ])

                # Add conditional formatting
                for i in range(1, len(data)):
                    for j in range(1, len(data[i])):
                        if data[i][j] == "P":
                            table_style.add('BACKGROUND', (j, i), (j, i), colors.green)
                            table_style.add('TEXTCOLOR', (j, i), (j, i), colors.white)
                        elif data[i][j] == "A" or data[i][j] == "A*":
                            table_style.add('BACKGROUND', (j, i), (j, i), colors.red)
                            table_style.add('TEXTCOLOR', (j, i), (j, i), colors.white)
                        elif data[i][j] == "C":
                            table_style.add('BACKGROUND', (j, i), (j, i), colors.purple)
                            table_style.add('TEXTCOLOR', (j, i), (j, i), colors.white)

                table.setStyle(table_style)
                elements.append(table)
                elements.append(Spacer(1, 20))

                # Add legend
                elements.append(Paragraph("Légende:", normal_style))
                elements.append(Paragraph("P = Présent", normal_style))
                elements.append(Paragraph("A = Absent", normal_style))
                elements.append(Paragraph("A* = Absent avec motif", normal_style))
                elements.append(Paragraph("C = En congé", normal_style))
                elements.append(Paragraph("- = Non défini", normal_style))
                elements.append(Spacer(1, 30))

            # Build PDF document
            doc.build(elements)

            # Get the value of the BytesIO buffer
            pdf = buffer.getvalue()
            buffer.close()

            # Create the HttpResponse with PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="historique-presences.pdf"'
            response.write(pdf)

            return response

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def get_staff_list(request):
    """API endpoint to get the list of staff members with attendance status"""
    today = timezone.now().date()

    # Get all staff members with their cities
    staff_members = StaffMember.objects.select_related('city').all()

    # Get today's attendance records
    attendances = Attendance.objects.filter(date=today)

    # Create a dictionary for quick lookup
    attendance_dict = {att.staff_member_id: att for att in attendances}

    # Prepare response data
    staff_data = []
    for staff in staff_members:
        attendance = attendance_dict.get(staff.id)
        # Determine status based on attendance record
        if attendance:
            if attendance.absence_reason == 'CONGE_STATUS':
                status = 'conge'
            elif attendance.present is True:
                status = 'present'
            elif attendance.present is False:
                status = 'absent'
            else:
                status = 'undefined'
        else:
            status = 'undefined'

        staff_data.append({
            'id': staff.id,
            'name': staff.name,
            'city': staff.city.name,
            'status': status,
            'absence_reason': attendance.absence_reason if attendance and attendance.present is False and attendance.absence_reason != 'CONGE_STATUS' else None,
            'timestamp': attendance.timestamp.isoformat() if attendance and attendance.timestamp else None
        })

    return JsonResponse({'staffMembers': staff_data})


@csrf_exempt
def get_staff_by_city(request):
    """API endpoint to get staff members by city"""
    if request.method == 'GET':
        city_id = request.GET.get('city_id')

        if city_id:
            try:
                city = City.objects.get(id=city_id)
                staff_members = StaffMember.objects.filter(city=city)

                staff_data = []
                for staff in staff_members:
                    staff_data.append({
                        'id': staff.id,
                        'name': staff.name,
                        'city_id': staff.city.id,
                        'city_name': staff.city.name
                    })

                return JsonResponse({
                    'success': True,
                    'staff': staff_data,
                    'city_name': city.name
                })
            except City.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Ville non trouvée'}, status=404)
        else:
            # Return all staff if no city specified
            staff_members = StaffMember.objects.select_related('city').all()
            staff_data = []
            for staff in staff_members:
                staff_data.append({
                    'id': staff.id,
                    'name': staff.name,
                    'city_id': staff.city.id,
                    'city_name': staff.city.name
                })

            return JsonResponse({
                'success': True,
                'staff': staff_data
            })

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def mark_present(request):
    """API endpoint to mark a staff member as present"""
    if request.method == 'POST':
        data = json.loads(request.body)
        staff_id = data.get('staff_id')

        try:
            staff = StaffMember.objects.get(id=staff_id)
            today = timezone.now().date()

            # Get or create attendance record
            attendance, created = Attendance.objects.get_or_create(
                staff_member=staff,
                date=today,
                defaults={'present': True, 'timestamp': timezone.now()}
            )

            # Update if already exists
            if not created:
                attendance.present = True
                attendance.absence_reason = None  # Clear any absence reason
                attendance.timestamp = timezone.now()
                attendance.save()

            return JsonResponse({
                'success': True,
                'message': f"{staff.name} marqué présent à {timezone.now().strftime('%H:%M:%S')}"
            })

        except StaffMember.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Personnel non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def mark_absent(request):
    """API endpoint to mark a staff member as absent with reason"""
    if request.method == 'POST':
        data = json.loads(request.body)
        staff_id = data.get('staff_id')
        reason = data.get('reason', '')

        try:
            staff = StaffMember.objects.get(id=staff_id)
            today = timezone.now().date()

            # Get or create attendance record
            attendance, created = Attendance.objects.get_or_create(
                staff_member=staff,
                date=today,
                defaults={'present': False, 'timestamp': timezone.now(), 'absence_reason': reason}
            )

            # Update if already exists
            if not created:
                attendance.present = False
                attendance.timestamp = timezone.now()
                attendance.absence_reason = reason
                attendance.save()

            return JsonResponse({
                'success': True,
                'message': f"{staff.name} marqué absent à {timezone.now().strftime('%H:%M:%S')}"
            })

        except StaffMember.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Personnel non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def mark_conge(request):
    """API endpoint to mark a staff member as on leave (congé)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        staff_id = data.get('staff_id')

        try:
            staff = StaffMember.objects.get(id=staff_id)
            today = timezone.now().date()

            # Get or create attendance record
            attendance, created = Attendance.objects.get_or_create(
                staff_member=staff,
                date=today,
                defaults={'present': None, 'timestamp': timezone.now(), 'absence_reason': 'CONGE_STATUS'}
            )

            # Update if already exists
            if not created:
                attendance.present = None  # NULL for congé status
                attendance.absence_reason = 'CONGE_STATUS'  # Special identifier for congé
                attendance.timestamp = timezone.now()
                attendance.save()

            return JsonResponse({
                'success': True,
                'message': f"{staff.name} marqué en congé à {timezone.now().strftime('%H:%M:%S')}"
            })

        except StaffMember.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Personnel non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def mark_city_present(request):
    """API endpoint to mark all staff members of a city as present"""
    if request.method == 'POST':
        data = json.loads(request.body)
        city_name = data.get('city')

        try:
            city = City.objects.get(name=city_name)
            staff_members = StaffMember.objects.filter(city=city)
            today = timezone.now().date()
            current_time = timezone.now()

            # Mark all staff in the city as present
            for staff in staff_members:
                attendance, created = Attendance.objects.get_or_create(
                    staff_member=staff,
                    date=today,
                    defaults={'present': True, 'timestamp': current_time}
                )

                if not created:
                    attendance.present = True
                    attendance.absence_reason = None  # Clear any absence reason
                    attendance.timestamp = current_time
                    attendance.save()

            return JsonResponse({
                'success': True,
                'message': f"Tout le personnel de {city_name} marqué présent !"
            })

        except City.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Ville non trouvée'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def mark_all_present(request):
    """API endpoint to mark all staff members as present"""
    if request.method == 'POST':
        try:
            staff_members = StaffMember.objects.all()
            today = timezone.now().date()
            current_time = timezone.now()

            # Mark all staff as present
            for staff in staff_members:
                attendance, created = Attendance.objects.get_or_create(
                    staff_member=staff,
                    date=today,
                    defaults={'present': True, 'timestamp': current_time}
                )

                if not created:
                    attendance.present = True
                    attendance.absence_reason = None  # Clear any absence reason
                    attendance.timestamp = current_time
                    attendance.save()

            return JsonResponse({
                'success': True,
                'message': "Tout le personnel marqué présent !"
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def update_staff_city(request):
    """API endpoint to update staff member's city"""
    if request.method == 'POST':
        data = json.loads(request.body)
        staff_id = data.get('staff_id')
        new_city_id = data.get('city_id')
        new_city_name = data.get('city_name')

        try:
            staff = StaffMember.objects.get(id=staff_id)

            # Handle both city_id and city_name parameters
            if new_city_id:
                new_city = City.objects.get(id=new_city_id)
            elif new_city_name:
                new_city = City.objects.get(name=new_city_name)
            else:
                return JsonResponse({'success': False, 'message': 'City ID ou nom de ville requis'}, status=400)

            old_city_name = staff.city.name
            staff.city = new_city
            staff.save()

            return JsonResponse({
                'success': True,
                'message': f"{staff.name} déplacé de {old_city_name} vers {new_city.name}"
            })

        except StaffMember.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Personnel non trouvé'}, status=404)
        except City.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Ville non trouvée'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def verify_admin(request):
    """API endpoint to verify admin password"""
    if request.method == 'POST':
        data = json.loads(request.body)
        password = data.get('password')

        # In a real application, use a more secure authentication method
        admin_password = settings.ADMIN_PASSWORD if hasattr(settings, 'ADMIN_PASSWORD') else "admin123"

        if password == admin_password:
            return JsonResponse({'success': True, 'message': 'Mode administrateur activé'})
        else:
            return JsonResponse({'success': False, 'message': 'Mot de passe incorrect'}, status=401)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def generate_pdf(request):
    """API endpoint to generate a PDF report of attendance"""
    if request.method == 'POST':
        try:
            # Get today's date
            today = timezone.now().date()

            # Get all staff with their attendance
            staff_members = StaffMember.objects.select_related('city').all()

            # Get attendance records for today
            attendances = Attendance.objects.filter(date=today)
            attendance_dict = {att.staff_member_id: att for att in attendances}

            # Create a BytesIO buffer for the PDF
            buffer = BytesIO()

            # Create the PDF object
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []

            # Set up styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            subtitle_style = styles['Heading2']
            normal_style = styles['Normal']

            # Add title
            elements.append(Paragraph("Rapport de Présence du Personnel", title_style))
            elements.append(Spacer(1, 12))

            # Add date
            date_str = today.strftime("%A %d %B %Y")
            date_str = date_str.capitalize()  # Capitalize first letter
            elements.append(Paragraph(date_str, subtitle_style))
            elements.append(Spacer(1, 12))

            # Create table data
            data = [["Nom", "Ville", "Statut", "Heure", "Motif d'absence"]]

            # Add staff data to table
            for staff in staff_members:
                attendance = attendance_dict.get(staff.id)

                # Determine status
                if attendance:
                    if attendance.absence_reason == 'CONGE_STATUS':
                        status = "En congé"
                    elif attendance.present is True:
                        status = "Présent"
                    elif attendance.present is False:
                        status = "Absent"
                    else:
                        status = "Non défini"
                else:
                    status = "Non défini"

                # Format the timestamp with proper timezone conversion
                time = ""
                if attendance and attendance.timestamp:
                    # Convert UTC time to local time (Europe/Paris)
                    local_time = timezone.localtime(attendance.timestamp)
                    time = local_time.strftime("%H:%M:%S")

                # Get absence reason
                absence_reason = ""
                if attendance and attendance.present is False and attendance.absence_reason != 'CONGE_STATUS':
                    absence_reason = attendance.absence_reason

                data.append([staff.name, staff.city.name, status, time, absence_reason])

            # Create table
            table = Table(data, colWidths=[100, 80, 70, 60, 150])

            # Style the table
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (4, 1), (4, -1), 'LEFT'),  # Left align reason text
            ])

            # Add conditional formatting for present/absent/conge status
            for i in range(1, len(data)):
                if data[i][2] == "Présent":
                    table_style.add('BACKGROUND', (2, i), (2, i), colors.green)
                    table_style.add('TEXTCOLOR', (2, i), (2, i), colors.white)
                elif data[i][2] == "Absent":
                    table_style.add('BACKGROUND', (2, i), (2, i), colors.red)
                    table_style.add('TEXTCOLOR', (2, i), (2, i), colors.white)
                elif data[i][2] == "En congé":
                    table_style.add('BACKGROUND', (2, i), (2, i), colors.purple)
                    table_style.add('TEXTCOLOR', (2, i), (2, i), colors.white)
                else:  # Undefined
                    table_style.add('BACKGROUND', (2, i), (2, i), colors.orange)
                    table_style.add('TEXTCOLOR', (2, i), (2, i), colors.white)

            table.setStyle(table_style)
            elements.append(table)

            elements.append(Spacer(1, 30))

            # Add summary statistics
            elements.append(Paragraph("Résumé", subtitle_style))
            elements.append(Spacer(1, 6))

            total_staff = staff_members.count()
            present_staff = sum(
                1 for s in staff_members if attendance_dict.get(s.id) and attendance_dict[s.id].present is True)
            absent_staff = sum(
                1 for s in staff_members if
                attendance_dict.get(s.id) and attendance_dict[s.id].present is False and attendance_dict[
                    s.id].absence_reason != 'CONGE_STATUS')
            conge_staff = sum(
                1 for s in staff_members if
                attendance_dict.get(s.id) and attendance_dict[s.id].absence_reason == 'CONGE_STATUS')
            undefined_staff = total_staff - present_staff - absent_staff - conge_staff

            present_percentage = round(present_staff / total_staff * 100, 1) if total_staff > 0 else 0
            absent_percentage = round(absent_staff / total_staff * 100, 1) if total_staff > 0 else 0
            conge_percentage = round(conge_staff / total_staff * 100, 1) if total_staff > 0 else 0
            undefined_percentage = round(undefined_staff / total_staff * 100, 1) if total_staff > 0 else 0

            elements.append(Paragraph(f"Nombre total de personnel: {total_staff}", normal_style))
            elements.append(Paragraph(f"Personnel présent: {present_staff} ({present_percentage}%)", normal_style))
            elements.append(Paragraph(f"Personnel absent: {absent_staff} ({absent_percentage}%)", normal_style))
            elements.append(Paragraph(f"Personnel en congé: {conge_staff} ({conge_percentage}%)", normal_style))
            elements.append(
                Paragraph(f"Personnel non défini: {undefined_staff} ({undefined_percentage}%)", normal_style))

            elements.append(Spacer(1, 20))

            # Add city breakdown
            elements.append(Paragraph("Détail par ville", subtitle_style))
            elements.append(Spacer(1, 6))

            cities = City.objects.all()
            for city in cities:
                city_staff = staff_members.filter(city=city)
                city_total = city_staff.count()

                city_present = sum(
                    1 for s in city_staff if attendance_dict.get(s.id) and attendance_dict[s.id].present is True)
                city_absent = sum(
                    1 for s in city_staff if
                    attendance_dict.get(s.id) and attendance_dict[s.id].present is False and attendance_dict[
                        s.id].absence_reason != 'CONGE_STATUS')
                city_conge = sum(
                    1 for s in city_staff if
                    attendance_dict.get(s.id) and attendance_dict[s.id].absence_reason == 'CONGE_STATUS')
                city_undefined = city_total - city_present - city_absent - city_conge

                city_present_percentage = round(city_present / city_total * 100, 1) if city_total > 0 else 0

                elements.append(
                    Paragraph(
                        f"{city.name}: {city_present}/{city_total} présent(s) ({city_present_percentage}%), {city_absent} absent(s), {city_conge} en congé, {city_undefined} non défini(s)",
                        normal_style
                    )
                )

            # Build PDF document
            doc.build(elements)

            # Get the value of the BytesIO buffer
            pdf = buffer.getvalue()
            buffer.close()

            # Create the HttpResponse with PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="rapport-presences.pdf"'
            response.write(pdf)

            return response

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)