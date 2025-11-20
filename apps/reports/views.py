from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def report_list(request):
    """
    Vista para mostrar la lista de reportes disponibles.
    Opcional: muestra solo a usuarios autenticados.
    """
    return render(request, 'reports/report_list.html', {})
