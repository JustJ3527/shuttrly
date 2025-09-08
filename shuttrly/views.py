from django.shortcuts import render
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from users.utilsFolder.recommendations import get_recommendations_for_display
import logging

logger = logging.getLogger(__name__)

def home_view(request):
    context = {}
    
    if request.headers.get('Hx-Request'):
        return render(request, 'partials/home_partial.html', context)
    return render(request, 'home.html', context)