from django.urls import path
from .views import logs_json_view

urlpatterns = [
    path("logs/json/", logs_json_view, name="logs_json"),
]
