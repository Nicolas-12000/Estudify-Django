from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import random
import os
from datetime import timedelta, date

from apps.courses.models import Course, Subject, CourseEnrollment
from apps.academics.models import Grade, Attendance
from utils.reports import PDFReportGenerator

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data: admin, teacher, students, courses, subjects, grades and attendances.'

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=10, help='Number of demo students to create')
        parser.add_argument('--months', type=int, default=6, help='Months of attendance history to generate')
        parser.add_argument('--start-date', type=str, help='Start date for generated history (YYYY-MM-DD)')
        parser.add_argument('--with-pdf', action='store_true', help='Generate sample boletines PDFs')
        parser.add_argument('--force', action='store_true', help='If set, will recreate demo records when possible')

    def handle(self, *args, **options):
        students_count = options['students']
        months = options['months']
        start_date_opt = options.get('start_date')
        with_pdf = options.get('with_pdf', False)
        force = options['force']

        self.stdout.write('Seeding demo data...')

        with transaction.atomic():
            # Create admin
            admin_username = 'demo_admin'
            admin, created = User.objects.get_or_create(username=admin_username, defaults={
                'first_name': 'Demo', 'last_name': 'Admin', 'email': 'admin@example.com', 'role': User.UserRole.ADMIN, 'is_staff': True, 'is_superuser': True
            })
            if created:
                admin.set_password('adminpass')
                admin.save()

            # Create teacher
            teacher_username = 'demo_teacher'
            teacher, created = User.objects.get_or_create(username=teacher_username, defaults={
                'first_name': 'Demo', 'last_name': 'Teacher', 'email': 'teacher@example.com', 'role': User.UserRole.TEACHER
            })
            if created:
                teacher.set_password('teacherpass')
                teacher.save()

            # Create students
            students = []
            for i in range(1, students_count + 1):
                uname = f'demo_student_{i}'
                u, created = User.objects.get_or_create(username=uname, defaults={
                    'first_name': f'Student{i}', 'last_name': 'Demo', 'email': f'student{i}@example.com', 'role': User.UserRole.STUDENT
                })
                if created:
                    u.set_password('studentpass')
                    u.save()
                students.append(u)

            # Optionally cleanup existing demo objects if --force
            if force:
                Course.objects.filter(code='DEMOC101').delete()
                Subject.objects.filter(code__startswith='DEMO-S').delete()
                from apps.courses.models import TimeSlot, Classroom, CourseSession
                TimeSlot.objects.filter(day_of_week__in=[0,2,4]).delete()
                Classroom.objects.filter(name__icontains='Demo Aula').delete()
                CourseSession.objects.filter(course__code='DEMOC101').delete()

            # Create a course and subjects
            course_code = 'DEMOC101'
            # Use update_or_create so existing demo course is assigned to demo teacher
            course, created = Course.objects.update_or_create(
                code=course_code,
                defaults={
                    'name': 'Curso Demo',
                    'description': 'Curso generado para pruebas',
                    'academic_year': timezone.now().year,
                    'semester': 1,
                    'teacher': teacher,
                    'max_students': 200,
                }
            )

            subjects = []
            for sidx in range(1, 4):
                code = f'DEMO-S{sidx}'
                # ensure subject is created/updated and assigned to demo course and demo teacher
                subj, created_subj = Subject.objects.update_or_create(
                    code=code,
                    defaults={
                        'name': f'Materia Demo {sidx}',
                        'description': 'Materia demo',
                        'credits': 3,
                        'course': course,
                        'teacher': teacher,
                    }
                )
                subjects.append(subj)

            # Create classrooms and timeslots, then create course sessions
            from apps.courses.models import TimeSlot, Classroom, CourseSession
            # Simple demo classrooms
            classroom, _ = Classroom.objects.get_or_create(name='Demo Aula A', defaults={'location': 'Edificio Demo', 'capacity': 40})
            # Create a few timeslots (Mon/Wed/Fri 08:00-09:30)
            ts_mon, _ = TimeSlot.objects.get_or_create(day_of_week=TimeSlot.MON, defaults={'start_time': '08:00', 'end_time': '09:30'})
            ts_wed, _ = TimeSlot.objects.get_or_create(day_of_week=TimeSlot.WED, defaults={'start_time': '08:00', 'end_time': '09:30'})
            ts_fri, _ = TimeSlot.objects.get_or_create(day_of_week=TimeSlot.FRI, defaults={'start_time': '08:00', 'end_time': '09:30'})
            # Link one session per course (use Monday timeslot)
            CourseSession.objects.get_or_create(course=course, timeslot=ts_mon, defaults={'classroom_fk': classroom, 'recurrence': 'weekly', 'notes': 'Sesión demo'})

            # Enroll students
            for s in students:
                CourseEnrollment.objects.get_or_create(student=s, course=course)

            # Create diversified grades for each student/subject (quizzes, homework, exams, project)
            grade_types = [('QUIZ', 10.0), ('HOMEWORK', 15.0), ('PROJECT', 25.0), ('EXAM', 50.0)]
            for s in students:
                for subj in subjects:
                    for gt, wt in grade_types:
                        # create two entries per grade type with slight variation
                        for n in range(1, 3):
                            val = round(random.uniform(2.0, 5.0), 1)
                            comments = f'Demo {gt} #{n}'
                            Grade.objects.create(student=s, subject=subj, value=val, grade_type=gt, weight=wt, comments=comments, graded_by=teacher)

            # Create attendances anchored to the course timeslots for the past `months` months
            today = date.today()
            if start_date_opt:
                try:
                    start_date = date.fromisoformat(start_date_opt)
                except Exception:
                    start_date = today - timedelta(days=months * 30)
            else:
                start_date = today - timedelta(days=months * 30)

            statuses = [Attendance.AttendanceStatus.PRESENT, Attendance.AttendanceStatus.ABSENT, Attendance.AttendanceStatus.LATE, Attendance.AttendanceStatus.EXCUSED]
            created_att = 0
            # For each timeslot of the course's sessions, generate dates matching that day_of_week
            sessions = CourseSession.objects.filter(course=course, is_active=True)
            for sess in sessions:
                dow = sess.timeslot.day_of_week
                # find first date >= start_date that matches dow
                d = start_date
                days_ahead = (dow - d.weekday()) % 7
                d = d + timedelta(days=days_ahead)
                while d <= today:
                    for s in students:
                        status = random.choices(statuses, weights=(75, 15, 7, 3))[0]
                        notes = ''
                        if status == Attendance.AttendanceStatus.LATE:
                            notes = 'Llegó con retraso'
                        Attendance.objects.get_or_create(student=s, course=course, date=d, defaults={'status': status, 'notes': notes, 'recorded_by': teacher})
                        created_att += 1
                    d += timedelta(days=7)

            # If no sessions were configured, create a weekly series as fallback
            if not sessions:
                d = start_date
                while d <= today:
                    for s in students:
                        status = random.choices(statuses, weights=(75, 15, 7, 3))[0]
                        Attendance.objects.get_or_create(student=s, course=course, date=d, defaults={'status': status, 'recorded_by': teacher})
                    d += timedelta(days=7)

            # Generate example PDFs if requested
            if with_pdf:
                try:
                    reports_dir = os.path.join(settings.BASE_DIR, 'media', 'reports')
                    os.makedirs(reports_dir, exist_ok=True)
                    first_student = students[0]
                    grades_qs = Grade.objects.filter(student=first_student)
                    response = PDFReportGenerator.generate_grade_report(first_student, grades_qs, course=course)
                    filename = os.path.join(reports_dir, f'boletin_{first_student.username}.pdf')
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'No se pudo generar PDF demo: {e}'))

        self.stdout.write(self.style.SUCCESS('Demo seed completado.'))
        self.stdout.write(f'Admin: {admin_username} / password: adminpass')
        self.stdout.write(f'Teacher: {teacher_username} / password: teacherpass')
        self.stdout.write(f'Students: {students_count} users: demo_student_1 .. demo_student_{students_count} / password: studentpass')