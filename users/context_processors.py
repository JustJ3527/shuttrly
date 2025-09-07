"""
Context processors for the users app.
"""

def recommendations_context(request):
    """
    Add user recommendations to the context for all templates.
    """
    context = {}
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            from users.utilsFolder.recommendations import get_recommendations_for_display
            recommendations = get_recommendations_for_display(request.user.id, limit=5)
            context['recommendations'] = recommendations
        except Exception as e:
            # Don't fail the entire request if recommendations fail
            context['recommendations'] = []
    else:
        context['recommendations'] = []
    
    return context
