from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count, Q, Min, Max
from django.contrib.auth import get_user_model

from apps.api.serializers import (
    UserSerializer, ProfileSerializer, CourseSerializer,
    SubjectSerializer, CourseEnrollmentSerializer, GradeSerializer,
    AttendanceSerializer, GradeStatisticsSerializer,
    AttendanceStatisticsSerializer
)
from apps.users.models import Profile
from apps.courses.models import Course, Subject, CourseEnrollment
from apps.academics.models import Grade, Attendance

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios.
    CRUD completo + acciones personalizadas.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'last_name']
    ordering = ['-date_joined']
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Obtener información del usuario actual."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Activar/desactivar usuario."""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({
            'status': 'active' if user.is_active else 'inactive',
            'message': f'Usuario {"activado" if user.is_active else "desactivado"} correctamente'
        })


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de cursos."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['academic_year', 'semester', 'teacher', 'is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'academic_year', 'created_at']
    ordering = ['-academic_year', 'semester', 'name']
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Obtener estudiantes inscritos en el curso."""
        course = self.get_object()
        enrollments = course.enrollments.filter(is_active=True)
        students = User.objects.filter(
            id__in=enrollments.values_list('student_id', flat=True)
        )
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        """Obtener materias del curso."""
        course = self.get_object()
        subjects = course.subjects.filter(is_active=True)
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)


class SubjectViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de materias."""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'teacher', 'is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'credits', 'created_at']
    ordering = ['course', 'name']


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de inscripciones."""
    queryset = CourseEnrollment.objects.all()
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'course', 'is_active']
    ordering_fields = ['enrollment_date']
    ordering = ['-enrollment_date']
    
    @action(detail=False, methods=['post'])
    def bulk_enroll(self, request):
        """
        Inscripción masiva de estudiantes.
        Espera: {"course_id": 1, "student_ids": [1, 2, 3]}
        """
        course_id = request.data.get('course_id')
        student_ids = request.data.get('student_ids', [])
        
        if not course_id or not student_ids:
            return Response(
                {'error': 'Se requiere course_id y student_ids'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Curso no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        enrolled = []
        errors = []
        
        for student_id in student_ids:
            try:
                student = User.objects.get(id=student_id, role=User.UserRole.STUDENT)
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={'is_active': True}
                )
                if created:
                    enrolled.append(student_id)
                else:
                    errors.append({
                        'student_id': student_id,
                        'error': 'Ya inscrito'
                    })
            except User.DoesNotExist:
                errors.append({
                    'student_id': student_id,
                    'error': 'Estudiante no encontrado'
                })
        
        return Response({
            'enrolled_count': len(enrolled),
            'enrolled_ids': enrolled,
            'errors': errors
        })


class GradeViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de calificaciones."""
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'subject', 'grade_type', 'graded_by']
    search_fields = ['student__first_name', 'student__last_name', 'subject__name']
    ordering_fields = ['graded_date', 'value']
    ordering = ['-graded_date']
    
    def perform_create(self, serializer):
        """Asignar automáticamente el docente que califica."""
        serializer.save(graded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Obtener estadísticas de calificaciones.
        Filtros opcionales: student_id, course_id, subject_id
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Aplicar filtros adicionales
        student_id = request.query_params.get('student_id')
        course_id = request.query_params.get('course_id')
        subject_id = request.query_params.get('subject_id')
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        if course_id:
            queryset = queryset.filter(subject__course_id=course_id)
        
        # Calcular estadísticas por materia
        stats_qs = queryset.values('subject__name').annotate(
            average=Avg('value'),
            min_grade=Min('value'),
            max_grade=Max('value'),
            total_count=Count('id'),
            passing_count=Count('id', filter=Q(value__gte=3.0)),
            failing_count=Count('id', filter=Q(value__lt=3.0))
        ).order_by('subject__name')
        
        stats = list(stats_qs)
        # Normalizar clave 'subject__name' -> 'subject_name' para el serializer
        for s in stats:
            s['subject_name'] = s.pop('subject__name', None)

        serializer = GradeStatisticsSerializer(stats, many=True)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de asistencia."""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'course', 'status', 'date']
    ordering_fields = ['date']
    ordering = ['-date']
    
    def perform_create(self, serializer):
        """Asignar automáticamente el docente que registra."""
        serializer.save(recorded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Obtener estadísticas de asistencia.
        Filtros: student_id, course_id
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        student_id = request.query_params.get('student_id')
        course_id = request.query_params.get('course_id')
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Estadísticas por mes
        from django.db.models.functions import TruncMonth
        stats_qs = queryset.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            present_count=Count('id', filter=Q(status='PRESENT')),
            absent_count=Count('id', filter=Q(status='ABSENT')),
            late_count=Count('id', filter=Q(status='LATE')),
            excused_count=Count('id', filter=Q(status='EXCUSED')),
            total_count=Count('id')
        ).order_by('month')
        
        stats = list(stats_qs)
        # Calcular tasa de asistencia
        for stat in stats:
            total = stat.get('total_count', 0) or 0
            present = (stat.get('present_count', 0) or 0) + (stat.get('late_count', 0) or 0)
            stat['attendance_rate'] = (present / total * 100) if total > 0 else 0
            # Normalizar month a string ISO para serializar fácilmente
            month_val = stat.get('month')
            stat['month'] = month_val.isoformat() if hasattr(month_val, 'isoformat') else str(month_val)
        
        serializer = AttendanceStatisticsSerializer(stats, many=True)
        return Response(serializer.data)
