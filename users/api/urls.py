from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import recommendations

urlpatterns = [
    # Authentication
    path('auth/login/', views.login_api, name='api_login'),
    path('auth/logout/', views.logout_api, name='api_logout'),
    path('auth/refresh-session/', views.refresh_session_api, name='api_refresh_session'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('auth/resend-2fa-code/', views.resend_2fa_code_api, name='api_resend_2fa_code'),
    
    # Registration (steps)
    path('auth/register/step1/', views.register_step_1_email, name='api_register_step1'),
    path('auth/register/step2/', views.register_step_2_verifify_email, name='api_register_step2'),
    path('auth/register/step4/', views.register_step_4_username, name='api_register_step4'),
    path('auth/register/complete/', views.register_complete, name='api_register_complete'),
    path('auth/resend-code/', views.resend_verification_code, name='api_resend_code'),
    
    # User profile
    path('user/profile/', views.user_profile, name='api_user_profile'),
    path('user/profile/full/', views.user_profile_full, name='api_user_profile_full'),  # Nouvel endpoint complet
    path('user/update/', views.update_profile, name='api_update_profile'),
    
    # Utilities
    path('auth/check-username/', views.check_username_availability, name='api_check_username'),
    
    # User recommendations
    path('recommendations/', recommendations.get_user_recommendations, name='api_user_recommendations'),
    path('recommendations/trigger/', recommendations.trigger_recommendation_calculation, name='api_trigger_recommendations'),
    path('recommendations/stats/', recommendations.get_recommendation_stats, name='api_recommendation_stats'),
    path('recommendations/refresh-all/', recommendations.refresh_all_recommendations, name='api_refresh_all_recommendations'),
]