# add history of attendance and be able to generate that
# add dark mode
# add motif d'absence

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
        staff_data.append({
            'id': staff.id,
            'name': staff.name,
            'city': staff.city.name,
            'present': attendance.present if attendance else False,
            'timestamp': attendance.timestamp.isoformat() if attendance and attendance.timestamp else None
        })

    return JsonResponse({'staffMembers': staff_data})


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
    """API endpoint to mark a staff member as absent"""
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
                defaults={'present': False, 'timestamp': timezone.now()}
            )

            # Update if already exists
            if not created:
                attendance.present = False
                attendance.timestamp = timezone.now()
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
            data = [["Nom", "Ville", "Statut", "Heure"]]

            # Add staff data to table
            for staff in staff_members:
                attendance = attendance_dict.get(staff.id)
                status = "Présent" if attendance and attendance.present else "Absent"

                # Format the timestamp with proper timezone conversion
                time = ""
                if attendance and attendance.timestamp:
                    # Convert UTC time to local time (Europe/Paris)
                    local_time = timezone.localtime(attendance.timestamp)
                    time = local_time.strftime("%H:%M:%S")

                data.append([staff.name, staff.city.name, status, time])

            # Create table
            table = Table(data, colWidths=[120, 100, 80, 80])

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

            # Add conditional formatting for present/absent status
            for i in range(1, len(data)):
                if data[i][2] == "Présent":
                    table_style.add('BACKGROUND', (2, i), (2, i), colors.green)
                    table_style.add('TEXTCOLOR', (2, i), (2, i), colors.white)
                else:
                    table_style.add('BACKGROUND', (2, i), (2, i), colors.red)
                    table_style.add('TEXTCOLOR', (2, i), (2, i), colors.white)

            table.setStyle(table_style)
            elements.append(table)

            elements.append(Spacer(1, 30))

            # Add summary statistics
            elements.append(Paragraph("Résumé", subtitle_style))
            elements.append(Spacer(1, 6))

            total_staff = staff_members.count()
            present_staff = sum(1 for s in staff_members if attendance_dict.get(s.id) and attendance_dict[s.id].present)
            absent_staff = total_staff - present_staff
            present_percentage = round(present_staff / total_staff * 100, 1) if total_staff > 0 else 0

            elements.append(Paragraph(f"Nombre total de personnel: {total_staff}", normal_style))
            elements.append(Paragraph(f"Personnel présent: {present_staff} ({present_percentage}%)", normal_style))
            elements.append(Paragraph(f"Personnel absent: {absent_staff}", normal_style))

            elements.append(Spacer(1, 20))

            # Add city breakdown
            elements.append(Paragraph("Détail par ville", subtitle_style))
            elements.append(Spacer(1, 6))

            cities = City.objects.all()
            for city in cities:
                city_staff = staff_members.filter(city=city)
                city_total = city_staff.count()
                city_present = sum(1 for s in city_staff if attendance_dict.get(s.id) and attendance_dict[s.id].present)
                city_percentage = round(city_present / city_total * 100, 1) if city_total > 0 else 0

                elements.append(
                    Paragraph(
                        f"{city.name}: {city_present}/{city_total} présent(s) ({city_percentage}%)",
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