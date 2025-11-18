from django.core.management.base import BaseCommand

from .command_helpers import (
    create_superuser_if_missing,
    create_user_if_missing,
    env_or_default,
)

from apps.courses.models import Course, TimeSlot, Classroom, CourseSession
from apps.core.management.commands.command_helpers import (
    create_subjects_for_course,
    enroll_students_in_course,
    create_grades_for_subjects,
    create_attendance_for_course,
)
from datetime import time


class Command(BaseCommand):
    help = 'Create initial users (admin/teacher/student) if they do not exist.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preset',
            choices=['auto', 'curated'],
            default='auto',
            help='Choose preset data: "auto" (default) or "curated" (more detailed dataset)'
        )

    def handle(self, *args, **options):  # noqa: C901 - command builds many demo objects
        created = []

        # Admin (prefer environment variables)
        admin_username = env_or_default('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = env_or_default('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        admin_password = env_or_default('DJANGO_SUPERUSER_PASSWORD', 'changeme')

        su_created, _ = create_superuser_if_missing(
            admin_username, admin_email, admin_password,
            self.stdout, self.stderr, self.style)
        if su_created:
            created.append(('superuser', admin_username))

        # Teachers: create multiple teachers to make the demo feel alive
        teacher_count = int(env_or_default('SEED_TEACHER_COUNT', '7'))
        teachers = []
        from django.contrib.auth import get_user_model
        User = get_user_model()
        role_val_teacher = (getattr(User, 'UserRole', None) and User.UserRole.TEACHER)
        for i in range(1, teacher_count + 1):
            username = f'teacher{i}'
            email = f'{username}@example.com'
            password = env_or_default('SEED_TEACHER_PASSWORD', 'teacherpass')
            # Assign role explicitly to avoid writing to read-only convenience properties
            t_created, user_obj = create_user_if_missing(
                username, email, password,
                set_staff=True, role_attr='role', role_value=role_val_teacher,
                stdout=self.stdout, stderr=self.stderr, style=self.style)
            if t_created:
                created.append(('teacher', username))
            if user_obj:
                teachers.append(user_obj)

        # Students: create multiple students for demo
        student_count = int(env_or_default('SEED_STUDENT_COUNT', '10'))
        students = []
        role_val_student = (getattr(User, 'UserRole', None) and User.UserRole.STUDENT)
        for i in range(1, student_count + 1):
            username = f'student{i}'
            email = f'{username}@example.com'
            password = env_or_default('SEED_STUDENT_PASSWORD', 'studentpass')
            s_created, user_obj = create_user_if_missing(
                username, email, password,
                role_attr='role', role_value=role_val_student,
                stdout=self.stdout, stderr=self.stderr, style=self.style)
            if s_created:
                created.append(('student', username))
            if user_obj:
                students.append(user_obj)

        if created:
            self.stdout.write(self.style.SUCCESS(f'Initial data created: {created}'))
        else:
            self.stdout.write('No initial objects were created (all exist).')

        # Additional demo data: create a demo course, subjects, enroll student, sessions
        try:
            preset = options.get('preset', 'auto') if options else 'auto'
            # If curated preset requested, run the more detailed, curated dataset
            if preset == 'curated':
                # create admin/curated teachers/students, profiles, courses, subjects, enrollments
                from django.contrib.auth import get_user_model
                from apps.users.models import Profile
                User = get_user_model()

                self.stdout.write('Running curated seed preset...')

                # Create curated teachers
                curated_teachers = [
                    ('prof_juan', 'Juan', 'Pérez', 'juan@estudify.com'),
                    ('prof_vanessa', 'Vanessa', 'Urbano', 'vanessa.urbano@estudify.com'),
                    ('prof_carlos', 'Carlos', 'Rodríguez', 'carlos@estudify.com'),
                ]
                teachers = []
                role_val_teacher = (getattr(User, 'UserRole', None) and User.UserRole.TEACHER)
                for username, first, last, email in curated_teachers:
                    _, teacher = create_user_if_missing(
                        username,
                        email,
                        'teacher123',
                        set_staff=True,
                        role_attr='role',
                        role_value=role_val_teacher,
                        stdout=self.stdout,
                        stderr=self.stderr,
                        style=self.style,
                    )
                    if teacher:
                        try:
                            if not hasattr(teacher, 'profile') or not getattr(teacher, 'profile', None):
                                Profile.objects.get_or_create(user=teacher, defaults={'city': 'Pasto', 'country': 'Colombia'})
                        except Exception:
                            pass
                        teachers.append(teacher)

                # Curated students
                curated_students = [
                    ('natalia_mendez', 'Natalia', 'Méndez'),
                    ('ana_lopez', 'Ana', 'López'),
                    ('pedro_martinez', 'Pedro', 'Martínez'),
                    ('lucia_garcia', 'Lucía', 'García'),
                    ('diego_sanchez', 'Diego', 'Sánchez'),
                    ('sofia_torres', 'Sofía', 'Torres'),
                    ('miguel_ramirez', 'Miguel', 'Ramírez'),
                    ('valentina_castro', 'Valentina', 'Castro'),
                ]
                students = []
                role_val_student = (getattr(User, 'UserRole', None) and User.UserRole.STUDENT)
                for username, first, last in curated_students:
                    _, student = create_user_if_missing(
                        username,
                        f'{username}@estudify.com',
                        'student123',
                        role_attr='role',
                        role_value=role_val_student,
                        stdout=self.stdout,
                        stderr=self.stderr,
                        style=self.style,
                    )
                    if student:
                        try:
                            if not hasattr(student, 'profile') or not getattr(student, 'profile', None):
                                Profile.objects.get_or_create(user=student, defaults={'city': 'Pasto', 'country': 'Colombia'})
                        except Exception:
                            pass
                        students.append(student)

                # Create curated courses
                courses = []
                course_data = [
                    ('Matemáticas 11A', 'MAT11A', teachers[0] if teachers else None),
                    ('Biología 10B', 'BIO10B', teachers[1] if len(teachers) > 1 else None),
                    ('Química 11C', 'QUI11C', teachers[2] if len(teachers) > 2 else None),
                    ('Programación Avanzada', 'PRG201', teachers[0] if teachers else None),
                ]
                for name, code, teacher_obj in course_data:
                    defaults = {'name': name, 'max_students': 30, 'teacher': teacher_obj}
                    course, _ = Course.objects.get_or_create(code=code, academic_year=2025, semester=1, defaults=defaults)
                    courses.append(course)

                # Create two subjects per curated course
                all_subjects = []
                for course in courses:
                    subj_infos = [
                        (f"{course.code}-S1", f"{course.name} - Fundamentos", 3, course.teacher),
                        (f"{course.code}-S2", f"{course.name} - Avanzado", 2, course.teacher),
                    ]
                    subjects = create_subjects_for_course(course, subj_infos)
                    all_subjects.extend(subjects)

                # Enroll curated students in courses
                for course in courses:
                    enroll_students_in_course(course, students)

                # Create grades and attendance
                for course in courses:
                    course_subjects = [s for s in all_subjects if s.course_id == course.id]
                    if not course_subjects:
                        continue
                    grader = course.teacher
                    create_grades_for_subjects(course_subjects, students, graded_by=grader)
                    create_attendance_for_course(course, students, days=3, recorded_by=grader)

                self.stdout.write(self.style.SUCCESS('Curated seed completed'))
                return
            teacher = None
            student = None
            # attempt to find created teacher/student by the seeded usernames
            teacher_username = env_or_default('SEED_TEACHER_USERNAME', 'teacher1')
            student_username = env_or_default('SEED_STUDENT_USERNAME', 'student1')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                teacher = User.objects.get(username=teacher_username)
            except User.DoesNotExist:
                teacher = None
            try:
                student = User.objects.get(username=student_username)
            except User.DoesNotExist:
                student = None

            # pick a teacher for the course if available
            demo_teacher = teachers[0] if teachers else teacher
            course, created_course = Course.objects.get_or_create(
                code='DEMO101',
                defaults={'name': 'Curso Demo', 'academic_year': 2025, 'semester': 1, 'teacher': demo_teacher}
            )
            if created_course:
                self.stdout.write(self.style.SUCCESS(f'Created demo course: {course.code}'))

            # subjects
            # Create a small set of demo subjects and assign teachers round-robin
            subject_count = int(env_or_default('SEED_SUBJECT_COUNT', '7'))
            subject_infos = []
            for idx in range(1, subject_count + 1):
                code = f'DEMO-S{idx}'
                name = f'Demo Subject {idx}'
                credits = 2 + (idx % 3)
                assigned_teacher = teachers[(idx - 1) % len(teachers)] if teachers else None
                subject_infos.append((code, name, credits, assigned_teacher))

            subjects = create_subjects_for_course(course, subject_infos)
            self.stdout.write(f'Ensured {len(subjects)} demo subjects')

            # enroll all demo students
            if students:
                enroll_students_in_course(course, students)
                self.stdout.write(f'Enrolled {len(students)} demo students in demo course')

            # create a timeslot and classroom and session
            ts, _ = TimeSlot.objects.get_or_create(
                day_of_week=0,
                start_time=time(8, 0),
                end_time=time(10, 0),
            )
            clsrm, _ = Classroom.objects.get_or_create(
                name='Aula Demo',
                defaults={'location': 'Edificio Demo', 'capacity': 40},
            )
            session, _ = CourseSession.objects.get_or_create(
                course=course,
                timeslot=ts,
                defaults={'classroom_fk': clsrm},
            )
            self.stdout.write('Created demo timeslot/classroom/session')

            # create grades and attendance for demo students
            if students and subjects:
                create_grades_for_subjects(subjects, students, graded_by=demo_teacher)
                create_attendance_for_course(course, students, days=3, recorded_by=demo_teacher)
                self.stdout.write('Created demo grades and attendance for demo students')

        except Exception as exc:
            self.stderr.write(f'Error creating demo data: {exc}')
