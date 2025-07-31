from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from pathlib import Path
import json

# Create your views here.

@staff_member_required
def logs_json_view(request):
    logs_path = Path(settings.BASE_DIR) / 'logs' / 'user_logs.json'
    if not logs_path.exists():
        logs = []
    else:
        with open(logs_path, 'r', encoding='utf-8') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    return render(request, 'json_logs.html', {'logs':logs})