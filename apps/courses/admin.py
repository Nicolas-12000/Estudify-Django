from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.courses.models import Course, Subject, CourseEnrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
	list_display = ['name', 'code', 'academic_year', 'semester', 'teacher', 'enrolled_count', 'max_students', 'is_active']
	list_filter = ['academic_year', 'semester', 'is_active', 'created_at']
	search_fields = ['name', 'code', 'teacher__username', 'teacher__first_name', 'teacher__last_name']
	ordering = ['-academic_year', 'semester', 'name']
	list_select_related = ('teacher',)
	autocomplete_fields = ('teacher',)

	fieldsets = (
		(_('Información Básica'), {'fields': ('name', 'code', 'description')}),
		(_('Periodo Académico'), {'fields': ('academic_year', 'semester')}),
		(_('Asignación'), {'fields': ('teacher', 'max_students')}),
		(_('Estado'), {'fields': ('is_active', 'created_at', 'updated_at')}),
	)

	readonly_fields = ['created_at', 'updated_at']

	def enrolled_count(self, obj):
		return obj.enrolled_count
	enrolled_count.short_description = 'Inscritos'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
	list_display = ['name', 'code', 'course', 'teacher', 'credits', 'is_active']
	list_filter = ['course', 'credits', 'is_active', 'created_at']
	search_fields = ['name', 'code', 'course__name', 'teacher__username']
	ordering = ['course', 'name']
	list_select_related = ('course', 'teacher')
	autocomplete_fields = ('course', 'teacher')

	fieldsets = (
		(_('Información'), {'fields': ('name', 'code', 'description', 'credits')}),
		(_('Asignación'), {'fields': ('course', 'teacher')}),
		(_('Estado'), {'fields': ('is_active', 'created_at', 'updated_at')}),
	)

	readonly_fields = ['created_at', 'updated_at']


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
	# Note: using created_at instead of enrollment_date (no DB migration required)
	list_display = ['student', 'course', 'created_at', 'is_active']
	list_filter = ['course', 'is_active', 'created_at']
	search_fields = ['student__username', 'student__first_name', 'student__last_name', 'course__name']
	ordering = ['-created_at']
	date_hierarchy = 'created_at'
	list_select_related = ('student', 'course')
	autocomplete_fields = ('student', 'course')

	fieldsets = (
		(_('Inscripción'), {'fields': ('student', 'course')}),
		(_('Estado'), {'fields': ('is_active', 'created_at')}),
	)

	readonly_fields = ['created_at']
