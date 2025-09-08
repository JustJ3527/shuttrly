"""
Context processors for the users app.
"""

def recommendations_context(request):
    """
    Add user recommendations to the context for all templates.
    Uses session-based rotation to keep recommendations stable during navigation.
    """
    context = {}
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            from users.tasks import get_user_recommendations_for_display
            
            # Use session-based rotation key to keep recommendations stable
            session_key = f'recommendations_rotation_{request.user.id}'
            if session_key not in request.session:
                import time
                request.session[session_key] = int(time.time())
            
            rotation_key = request.session[session_key]
            
            result = get_user_recommendations_for_display(
                request.user.id, 
                limit=4, 
                rotation_key=rotation_key
            )
            
            if result.get('status') == 'success':
                context['recommendations'] = result.get('recommendations', [])
            else:
                context['recommendations'] = []
        except Exception as e:
            # Don't fail the entire request if recommendations fail
            context['recommendations'] = []
    else:
        context['recommendations'] = []
    
    return context
