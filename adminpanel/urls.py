from django.urls import path
from .views import *

app_name = 'adminpanel'  # Important pour le namespace

urlpatterns = [
    path('', admin_dashboard_view, name='admin_dashboard'),  # <- ce nom doit correspondre
    path('edit-user/<int:user_id>/', edit_user_view, name='edit_user'),
    path('delete-user/<int:user_id>/', delete_user_view, name='delete_user'),
    path('group/<int:group_id>/', group_dashboard_view, name='group_dashboard'),
    path('logs/', user_logs_view, name='user_logs'),
    path('logs/restore/', restore_log_action_view, name='restore_log_action'),
]