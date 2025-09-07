from django.shortcuts import render
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from users.utilsFolder.recommendations import get_recommendations_for_display
import logging

logger = logging.getLogger(__name__)

def home_view(request):
    context = {}
    
    # Add user recommendations if user is authenticated
    if request.user.is_authenticated:
        try:
            recommendations = get_recommendations_for_display(request.user.id, limit=5)
            context['recommendations'] = recommendations
            logger.debug(f"Loaded {len(recommendations)} recommendations for user {request.user.id}")
        except Exception as exc:
            logger.error(f"Error loading recommendations for user {request.user.id}: {exc}")
            context['recommendations'] = []
    
    if request.headers.get('Hx-Request'):
        return render(request, 'partials/home_partial.html', context)
    return render(request, 'home.html', context)