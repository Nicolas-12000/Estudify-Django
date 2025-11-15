"""
Comando personalizado de Django para crear datos iniciales de prueba.
Uso: python manage.py setup_initial_data
Nota: No elimina datos existentes. Usa get_or_create para evitar duplicados.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import Profile
from apps.courses.models import Course, Subject, CourseEnrollment
from apps.academics.models import Grade, Attendance
from datetime import date, timedelta
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos iniciales de prueba para Estudify (sin eliminar datos existentes)'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos iniciales...')
        self.stdout.write('Nota: Se usará get_or_create para evitar duplicados.')

        # 1. Crear usuarios
        self.stdout.write('Creando usuarios...')

        # Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@estudify.com',
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'role': getattr(User, 'UserRole', None) and User.UserRole.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            try:
                Profile.objects.create(user=admin, city='Pasto', country='Colombia')
            except Exception:
                # Perfil opcional si el modelo no existe o tiene otros campos
                pass

        # Docentes
        teachers = []
        teacher_data = [
            ('prof_juan', 'Juan', 'Pérez', 'juan@estudify.com'),
            ('prof_vanessa', 'Vanessa', 'Urbano', 'vanessa.urbano@estudify.com'),
            ('prof_carlos', 'Carlos', 'Rodríguez', 'carlos@estudify.com'),
        ]

        for username, first, last, email in teacher_data:
            teacher, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first,
                    'last_name': last,
                    'role': getattr(User, 'UserRole', None) and User.UserRole.TEACHER,
                }
            )
            if created:
                teacher.set_password('teacher123')
                teacher.save()
                try:
                    Profile.objects.create(user=teacher, city='Pasto', country='Colombia')
                except Exception:
                    pass
            teachers.append(teacher)

        # Estudiantes
        students = []
        student_names = [
            ('natalia_mendez', 'Natalia', 'Méndez'),
            ('ana_lopez', 'Ana', 'López'),
            ('pedro_martinez', 'Pedro', 'Martínez'),
            ('lucia_garcia', 'Lucía', 'García'),
            ('diego_sanchez', 'Diego', 'Sánchez'),
            ('sofia_torres', 'Sofía', 'Torres'),
            ('miguel_ramirez', 'Miguel', 'Ramírez'),
            ('valentina_castro', 'Valentina', 'Castro'),
        ]

        for username, first, last in student_names:
            student, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@estudify.com',
                    'first_name': first,
                    'last_name': last,
                    'role': getattr(User, 'UserRole', None) and User.UserRole.STUDENT,
                }
            )
            if created:
                student.set_password('student123')
                student.save()
                try:
                    Profile.objects.create(user=student, city='Pasto', country='Colombia')
                except Exception:
                    pass
            students.append(student)

        self.stdout.write(self.style.SUCCESS(f'✓ {len(teachers)} docentes creados'))
        self.stdout.write(self.style.SUCCESS(f'✓ {len(students)} estudiantes creados'))

        # 2. Crear cursos
        self.stdout.write('Creando cursos...')
        courses = []
        course_data = [
            ('Matemáticas 11A', 'MAT11A', teachers[0] if teachers else None),
            ('Biología 10B', 'BIO10B', teachers[1] if len(teachers) > 1 else None),
            ('Química 11C', 'QUI11C', teachers[2] if len(teachers) > 2 else None),
            ('Programación Avanzada', 'PRG201', teachers[0] if teachers else None),
        ]

        for name, code, teacher in course_data:
            defaults = {'name': name, 'max_students': 30}
            if teacher:
                defaults['teacher'] = teacher
            course, created = Course.objects.get_or_create(
                code=code,
                academic_year=2025,
                semester=1,
                defaults=defaults,
            )
            courses.append(course)

        self.stdout.write(self.style.SUCCESS(f'✓ {len(courses)} cursos creados'))

        # 3. Crear materias
        self.stdout.write('Creando materias...')
        subjects = []
        subject_data = [
            ('Álgebra', 'ALG101', courses[0], teachers[0] if teachers else None),
            ('Cálculo', 'CAL101', courses[0], teachers[0] if teachers else None),
            ('Biología Celular', 'BIO101', courses[1] if len(courses) > 1 else None, teachers[1] if len(teachers) > 1 else None),
            ('Ecología', 'ECO101', courses[1] if len(courses) > 1 else None, teachers[1] if len(teachers) > 1 else None),
            ('Química Orgánica', 'QOR101', courses[2] if len(courses) > 2 else None, teachers[2] if len(teachers) > 2 else None),
            ('Python Avanzado', 'PYT201', courses[3] if len(courses) > 3 else None, teachers[0] if teachers else None),
        ]

        for name, code, course, teacher in subject_data:
            if course is None:
                continue
            defaults = {'name': name, 'credits': 3}
            if teacher:
                defaults['teacher'] = teacher
            if course:
                defaults['course'] = course
            subject, created = Subject.objects.get_or_create(
                code=code,
                defaults=defaults,
            )
            subjects.append(subject)

        self.stdout.write(self.style.SUCCESS(f'✓ {len(subjects)} materias creadas'))

        # 4. Inscribir estudiantes
        self.stdout.write('Inscribiendo estudiantes...')
        enrollments = 0
        
        # Natalia inscrita en Programación Avanzada
        if len(courses) > 3 and students:
            CourseEnrollment.objects.get_or_create(
                student=students[0],  # Natalia
                course=courses[3],    # Programación Avanzada
            )
            enrollments += 1
        
        # Resto de estudiantes en primeros 3 cursos
        for course in courses[:3]:  # Primeros 3 cursos
            for student in students[:6]:  # 6 estudiantes por curso
                CourseEnrollment.objects.get_or_create(
                    student=student,
                    course=course,
                )
                enrollments += 1

        self.stdout.write(self.style.SUCCESS(f'✓ {enrollments} inscripciones creadas'))

        # 5. Crear calificaciones
        self.stdout.write('Creando calificaciones...')
        grades_created = 0
        grade_types = ['QUIZ', 'EXAM', 'HOMEWORK', 'PROJECT']

        for subject in subjects:
            enrolled_students = User.objects.filter(
                enrollments__course=subject.course,
                enrollments__is_active=True,
            )

            for student in enrolled_students:
                for _ in range(random.randint(2, 4)):
                    Grade.objects.create(
                        student=student,
                        subject=subject,
                        value=Decimal(str(round(random.uniform(2.0, 5.0), 1))),
                        grade_type=random.choice(grade_types),
                        weight=Decimal('20.00'),
                        graded_by=subject.teacher if hasattr(subject, 'teacher') else None,
                    )
                    grades_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ {grades_created} calificaciones creadas'))

        # 6. Crear asistencias
        self.stdout.write('Creando registros de asistencia...')
        attendances_created = 0
        statuses = ['PRESENT', 'PRESENT', 'PRESENT', 'LATE', 'ABSENT']  # Más presentes

        for course in courses[:3]:
            enrolled_students = User.objects.filter(
                enrollments__course=course,
                enrollments__is_active=True,
            )

            # Últimos 20 días
            for i in range(20):
                att_date = date.today() - timedelta(days=i)
                for student in enrolled_students:
                    Attendance.objects.create(
                        student=student,
                        course=course,
                        date=att_date,
                        status=random.choice(statuses),
                        recorded_by=course.teacher if hasattr(course, 'teacher') else None,
                    )
                    attendances_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ {attendances_created} asistencias creadas'))

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN ==='))
        self.stdout.write(f'Total usuarios: {User.objects.count()}')
        self.stdout.write(f'Total cursos: {Course.objects.count()}')
        self.stdout.write(f'Total materias: {Subject.objects.count()}')
        self.stdout.write(f'Total inscripciones: {CourseEnrollment.objects.count()}')
        self.stdout.write(f'Total calificaciones: {Grade.objects.count()}')
        self.stdout.write(f'Total asistencias: {Attendance.objects.count()}')

        self.stdout.write(self.style.SUCCESS('\n✅ Datos iniciales creados exitosamente!'))
        self.stdout.write('\nCredenciales de prueba:')
        self.stdout.write('Admin: admin / admin123')
        self.stdout.write('Docente: prof_juan / teacher123 (Matemáticas)')
        self.stdout.write('Docente: prof_vanessa / teacher123 (Biología)')
        self.stdout.write('Estudiante: natalia_mendez / student123 (Programación)')
        self.stdout.write('Estudiante: ana_lopez / student123')
