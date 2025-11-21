from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator

from apps.users.forms import UserLoginForm
from apps.users.models import User


@csrf_protect
def login_view(request):
    """
    Maneja el inicio de sesión para admin, profesores y estudiantes.
    Redirige según el rol del usuario.
    """

    if request.method == "POST":
        form = UserLoginForm(request.POST)

        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            # Permitir login por username o email
            user = authenticate(request, username=username_or_email, password=password)

            if user is None:
                # Intentar autenticación usando email
                try:
                    email_user = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=email_user.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenido, {user.get_full_name()}!!")

                # ===============================
                # 🔥 REDIRECCIONES SEGÚN EL ROL
                # ===============================

                # Admin
                if user.is_superuser or user.is_staff or getattr(user, "is_admin_role", False):
                    return redirect("panel_admin")

                # Profesor
                if user.role == User.UserRole.TEACHER:
                    return redirect("panel_profesor")

                # Estudiante
                if user.role == User.UserRole.STUDENT:
                    return redirect("panel_estudiante")

                # Si no tiene un rol válido
                return redirect("home")

            else:
                messages.error(request, "Credenciales incorrectas.")
        else:
            messages.error(request, "Formulario no válido.")

    else:
        form = UserLoginForm()

    return render(request, "users/login.html", {"form": form})
