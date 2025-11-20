from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from apps.users.models import Profile

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    """
    Formulario de registro de usuarios.
    Permite elegir rol: Estudiante o Profesor.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        })
    )
    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        })
    )
    role = forms.ChoiceField(
        choices=User.UserRole.choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Tipo de usuario"
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'password1',
            'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })

    def clean_email(self):
        """Validar que el email sea único."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email ya está registrado.')
        return email


class PublicUserRegistrationForm(UserCreationForm):
    """
    Formulario público para registro desde la landing.
    Campos: nombre (first_name), email, password1, password2 y role (docente/estudiante).
    Genera automáticamente un `username` a partir del email si no se proporciona.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo'})
    )
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'})
    )
    # Limitamos las opciones de rol para registro público (no permitir ADMIN)
    role = forms.ChoiceField(
        choices=[(User.UserRole.TEACHER, User.UserRole.TEACHER.label),
                 (User.UserRole.STUDENT, User.UserRole.STUDENT.label)],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Rol"
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # password widgets
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return email

    def _generate_unique_username(self, base):
        """Genera un username único a partir de base."""
        username = base
        suffix = 0
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base}{suffix}"
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        # generar username a partir del email
        email = self.cleaned_data.get('email')
        local = email.split('@')[0]
        # normalizar y permitir solo caracteres válidos
        base = local.replace('.', '').replace('-', '').lower()
        base = base[:30] if len(base) > 30 else base
        user.username = self._generate_unique_username(base)
        user.first_name = self.cleaned_data.get('first_name', '')
        # last_name se deja vacío por defecto
        user.email = email
        user.role = self.cleaned_data.get('role', User.UserRole.STUDENT)
        if commit:
            user.save()
        return user

class UserLoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario o Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )

    def clean_username(self):
        """Permitir iniciar sesión usando email."""
        username = self.cleaned_data.get('username')
        if username and '@' in username:
            try:
                user = User.objects.get(email__iexact=username)
                return user.username
            except User.DoesNotExist:
                return username
        return username

class UserProfileForm(forms.ModelForm):
    """
    Formulario para editar el perfil de usuario y profile.
    """
    first_name = forms.CharField(
        required=False, max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(
        required=False, max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(
        required=False, max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = Profile
        fields = ['bio', 'address', 'city', 'country']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['phone'].initial = getattr(self.instance.user, 'phone', '')
            self.fields['date_of_birth'].initial = getattr(self.instance.user, 'date_of_birth', None)

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        user.phone = self.cleaned_data.get('phone', '')
        user.date_of_birth = self.cleaned_data.get('date_of_birth')
        if commit:
            user.save()
            profile.save()
        return profile
