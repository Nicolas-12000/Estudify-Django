from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.academics.models import Attendance, Grade
from apps.courses.models import Course, CourseEnrollment, Subject
from apps.courses.models import TimeSlot, Classroom, CourseSession
from apps.users.models import Profile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo User.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Profile.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'user',
            'bio',
            'address',
            'city',
            'country',
            'created_at']
        read_only_fields = ['id', 'created_at']


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Course.
    """
    teacher_name = serializers.CharField(
        source='teacher.get_full_name', read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'code', 'description', 'academic_year', 'semester',
            'teacher', 'teacher_name', 'max_students', 'enrolled_count',
            'is_full', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'enrolled_count', 'is_full']


class TimeSlotSerializer(serializers.ModelSerializer):
    day = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = TimeSlot
        fields = ['id', 'day_of_week', 'day', 'start_time', 'end_time']


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ['id', 'name', 'location', 'capacity']


class CourseSessionSerializer(serializers.ModelSerializer):
    timeslot = TimeSlotSerializer(read_only=True)
    classroom = ClassroomSerializer(source='classroom_fk', read_only=True)

    class Meta:
        model = CourseSession
        fields = ['id', 'course', 'timeslot', 'classroom', 'recurrence', 'notes']


# Extend CourseSerializer to include sessions as nested (read-only)
CourseSerializer._declared_fields['sessions'] = CourseSessionSerializer(many=True, read_only=True)
CourseSerializer.Meta.fields.append('sessions')


class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Subject.
    """
    course_name = serializers.CharField(source='course.name', read_only=True)
    teacher_name = serializers.CharField(
        source='teacher.get_full_name', read_only=True)

    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'code', 'description', 'credits',
            'course', 'course_name', 'teacher', 'teacher_name',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo CourseEnrollment.
    """
    student_name = serializers.CharField(
        source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'student', 'student_name', 'course', 'course_name',
            'created_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        """
        Validar que el estudiante no esté ya inscrito en el curso.
        """
        student = data.get('student')
        course = data.get('course')

        # Verificar si ya existe inscripción activa
        if CourseEnrollment.objects.filter(
            student=student,
            course=course,
            is_active=True
        ).exists():
            raise serializers.ValidationError(
                'El estudiante ya está inscrito en este curso.'
            )

        # Verificar que el curso no esté lleno
        if course.is_full:
            raise serializers.ValidationError(
                'El curso ha alcanzado su capacidad máxima.'
            )

        return data


class GradeSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Grade.
    """
    student_name = serializers.CharField(
        source='student.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    graded_by_name = serializers.CharField(
        source='graded_by.get_full_name', read_only=True)
    is_passing = serializers.BooleanField(read_only=True)
    letter_grade = serializers.CharField(read_only=True)
    # Explicitly declare Decimal fields to avoid float-based validators
    # warnings
    value = serializers.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=Decimal('0.0'),
        max_value=Decimal('5.0')
    )
    weight = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal('0.0'),
        max_value=Decimal('100.0')
    )

    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_name', 'subject', 'subject_name',
            'value', 'grade_type', 'weight', 'comments',
            'graded_by', 'graded_by_name', 'graded_date',
            'is_passing', 'letter_grade', 'created_at'
        ]
        read_only_fields = ['id', 'graded_date', 'created_at']

    def validate(self, data):
        """
        Validar que el estudiante esté inscrito en el curso de la materia.
        """
        student = data.get('student')
        subject = data.get('subject')

        if not CourseEnrollment.objects.filter(
            student=student,
            course=subject.course,
            is_active=True
        ).exists():
            raise serializers.ValidationError(
                'El estudiante no está inscrito en el curso de esta materia.'
            )

        return data


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Attendance.
    """
    student_name = serializers.CharField(
        source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    recorded_by_name = serializers.CharField(
        source='recorded_by.get_full_name', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'course', 'course_name',
            'date', 'status', 'status_display', 'notes',
            'recorded_by', 'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        """
        Validar que el estudiante esté inscrito en el curso.
        """
        student = data.get('student')
        course = data.get('course')

        if not CourseEnrollment.objects.filter(
            student=student,
            course=course,
            is_active=True
        ).exists():
            raise serializers.ValidationError(
                'El estudiante no está inscrito en este curso.'
            )

        return data


class GradeStatisticsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de calificaciones.
    """
    subject_name = serializers.CharField()
    average = serializers.DecimalField(max_digits=3, decimal_places=2)
    min_grade = serializers.DecimalField(max_digits=3, decimal_places=1)
    max_grade = serializers.DecimalField(max_digits=3, decimal_places=1)
    passing_count = serializers.IntegerField()
    failing_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


class AttendanceStatisticsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de asistencia.
    """
    month = serializers.CharField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    excused_count = serializers.IntegerField()
    total_count = serializers.IntegerField()
    attendance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
