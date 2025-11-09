from django.shortcuts import render


def home(request):
    """Render the home page using the base template.

    Keeps a minimal view for Sprint 0 while enabling template-driven UI.
    """
    return render(request, "base.html", {})
from django.shortcuts import render

# Create your views here.
