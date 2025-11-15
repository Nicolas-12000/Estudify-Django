from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Create initial users (admin/teacher/student) if they do not exist.'

    def handle(self, *args, **options):
        User = get_user_model()

        created = []

        # Admin (prefer environment variables)
        admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'changeme')

        if not User.objects.filter(username=admin_username).exists():
            try:
                User.objects.create_superuser(username=admin_username, email=admin_email, password=admin_password)
                created.append(('superuser', admin_username))
                self.stdout.write(self.style.SUCCESS(f'Created superuser: {admin_username}'))
            except Exception as exc:
                self.stderr.write(f'Could not create superuser {admin_username}: {exc}')
        else:
            self.stdout.write(f'Superuser {admin_username} already exists')

        # Teacher
        teacher_username = os.environ.get('SEED_TEACHER_USERNAME', 'teacher1')
        teacher_email = os.environ.get('SEED_TEACHER_EMAIL', 'teacher1@example.com')
        teacher_password = os.environ.get('SEED_TEACHER_PASSWORD', 'teacherpass')

        if not User.objects.filter(username=teacher_username).exists():
            try:
                u = User.objects.create_user(username=teacher_username, email=teacher_email, password=teacher_password)
                # attempt to set role flags if they exist on the model
                if hasattr(u, 'is_teacher'):
                    setattr(u, 'is_teacher', True)
                u.is_staff = True
                u.save()
                created.append(('teacher', teacher_username))
                self.stdout.write(self.style.SUCCESS(f'Created teacher: {teacher_username}'))
            except Exception as exc:
                self.stderr.write(f'Could not create teacher {teacher_username}: {exc}')
        else:
            self.stdout.write(f'Teacher {teacher_username} already exists')

        # Student
        student_username = os.environ.get('SEED_STUDENT_USERNAME', 'student1')
        student_email = os.environ.get('SEED_STUDENT_EMAIL', 'student1@example.com')
        student_password = os.environ.get('SEED_STUDENT_PASSWORD', 'studentpass')

        if not User.objects.filter(username=student_username).exists():
            try:
                u = User.objects.create_user(username=student_username, email=student_email, password=student_password)
                if hasattr(u, 'is_student'):
                    setattr(u, 'is_student', True)
                u.save()
                created.append(('student', student_username))
                self.stdout.write(self.style.SUCCESS(f'Created student: {student_username}'))
            except Exception as exc:
                self.stderr.write(f'Could not create student {student_username}: {exc}')
        else:
            self.stdout.write(f'Student {student_username} already exists')

        if created:
            self.stdout.write(self.style.SUCCESS(f'Initial data created: {created}'))
        else:
            self.stdout.write('No initial objects were created (all exist).')
