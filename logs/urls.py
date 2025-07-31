from django.urls import path
from .views import logs_json_view

urlpatterns = [
    path('json/', logs_json_view, name='logs_json'),
]
