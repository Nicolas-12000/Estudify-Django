import os
import sys
import django
# ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.courses.models import Subject, CourseEnrollment, CourseSession, TimeSlot, Course
from apps.academics.models import Grade, Attendance
from django.contrib.auth import get_user_model
User = get_user_model()

print('Subjects:', Subject.objects.count())
print('Courses:', Course.objects.count())
print('CourseSessions:', CourseSession.objects.count())
print('TimeSlots:', TimeSlot.objects.count())
print('Enrollments:', CourseEnrollment.objects.count())
print('Grades:', Grade.objects.count())
print('Attendances:', Attendance.objects.count())
print('Demo teacher exists:', User.objects.filter(username='demo_teacher').exists())
t = User.objects.filter(username='demo_teacher').first()
print('Subjects for demo_teacher:', Subject.objects.filter(teacher=t).count() if t else 0)
print('Demo students count:', User.objects.filter(username__startswith='demo_student_').count())

# show few sample grades and attendances counts per student
first = User.objects.filter(username__startswith='demo_student_').first()
if first:
    print('Sample grades for', first.username, Grade.objects.filter(student=first).count())
    print('Sample attendances for', first.username, Attendance.objects.filter(student=first).count())

print('\nDemo subject details:')
for s in Subject.objects.filter(code__startswith='DEMO-S'):
    print(s.code, s.name, 'teacher=', getattr(s.teacher, 'username', None))
