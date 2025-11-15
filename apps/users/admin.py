from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from apps.users.models import Profile

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	"""Admin personalizado para el modelo User."""
	list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
	list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
	search_fields = ['username', 'email', 'first_name', 'last_name']
	ordering = ['-date_joined']
	list_select_related = ()
	autocomplete_fields = ()

	fieldsets = (
		(None, {'fields': ('username', 'password')}),
		(_('Información Personal'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'avatar')}),
		(_('Permisos'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		(_('Fechas Importantes'), {'fields': ('last_login', 'date_joined')}),
	)

	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('username', 'email', 'password1', 'password2', 'role'),
		}),
	)

	actions = ['activate_users', 'deactivate_users']

	def activate_users(self, request, queryset):
		count = queryset.update(is_active=True)
		self.message_user(request, f'{count} usuarios activados.')
	activate_users.short_description = 'Activar usuarios seleccionados'

	def deactivate_users(self, request, queryset):
		count = queryset.update(is_active=False)
		self.message_user(request, f'{count} usuarios desactivados.')
	deactivate_users.short_description = 'Desactivar usuarios seleccionados'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ['user', 'city', 'country', 'created_at', 'is_active']
	list_filter = ['city', 'country', 'is_active', 'created_at']
	search_fields = ['user__username', 'user__email', 'city']
	ordering = ['-created_at']

	fieldsets = (
		(_('Usuario'), {'fields': ('user',)}),
		(_('Información'), {'fields': ('bio', 'address', 'city', 'country')}),
		(_('Estado'), {'fields': ('is_active', 'created_at', 'updated_at')}),
	)

	readonly_fields = ['created_at', 'updated_at']
