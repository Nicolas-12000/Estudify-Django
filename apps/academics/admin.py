from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.academics.models import Attendance, Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'subject',
        'value',
        'grade_type',
        'weight',
        'is_passing',
        'letter_grade',
        'graded_date']
    list_filter = ['grade_type', 'graded_date', 'subject__course', 'is_active']
    search_fields = [
        'student__username',
        'student__first_name',
        'student__last_name',
        'subject__name']
    ordering = ['-graded_date']
    date_hierarchy = 'graded_date'
    list_select_related = ('student', 'subject', 'graded_by')
    autocomplete_fields = ('student', 'subject', 'graded_by')

    fieldsets = (
        (_('Calificación'), {
            'fields': (
                'student', 'subject', 'value', 'grade_type', 'weight')}), (_('Detalles'), {
                    'fields': (
                        'comments', 'graded_by')}), (_('Estado'), {
                            'fields': (
                                'is_active', 'graded_date', 'created_at')}), )

    readonly_fields = ['graded_date', 'created_at']

    def is_passing(self, obj):
        """Return boolean for passing status so admin displays a checkbox."""
        return bool(obj.is_passing)
    is_passing.short_description = 'Aprobado'
    is_passing.boolean = True

    def letter_grade(self, obj):
        return obj.letter_grade
    letter_grade.short_description = 'Letra'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student',
        'course',
        'date',
        'status',
        'recorded_by',
        'is_active']
    list_filter = ['status', 'date', 'course', 'is_active']
    search_fields = [
        'student__username',
        'student__first_name',
        'student__last_name',
        'course__name']
    ordering = ['-date']
    date_hierarchy = 'date'
    list_select_related = ('student', 'course', 'recorded_by')
    autocomplete_fields = ('student', 'course', 'recorded_by')

    fieldsets = (
        (_('Asistencia'), {'fields': ('student', 'course', 'date', 'status')}),
        (_('Detalles'), {'fields': ('notes', 'recorded_by')}),
        (_('Estado'), {'fields': ('is_active', 'created_at')}),
    )

    readonly_fields = ['created_at']

    actions = ['mark_as_present', 'mark_as_absent']

    def mark_as_present(self, request, queryset):
        count = queryset.update(status='PRESENT')
        self.message_user(
            request, f'{count} registros marcados como presente.')
    mark_as_present.short_description = 'Marcar como presente'

    def mark_as_absent(self, request, queryset):
        count = queryset.update(status='ABSENT')
        self.message_user(request, f'{count} registros marcados como ausente.')
    mark_as_absent.short_description = 'Marcar como ausente'
