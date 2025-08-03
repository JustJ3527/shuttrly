from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from pathlib import Path
import json


@staff_member_required
def logs_json_view(request):
    print("File exists:", logs_path.exists())
    with open(logs_path, "r", encoding="utf-8") as f:
        content = f.read()
        print("Raw content:", content)
        try:
            logs = json.loads(content)
        except json.JSONDecodeError:
            print("⚠️ JSON error")
            logs = []

    print("Logs parsed:", logs)
    logs_path = Path(settings.BASE_DIR) / "logs" / "user_logs.json"
    if not logs_path.exists():
        logs = []
    else:
        with open(logs_path, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs_data_json = json.dumps(logs)  # ← serialize les logs pour JS

    return render(
        request,
        "json_logs.html",
        {
            "logs": logs,  # si tu veux encore l’utiliser côté Django
            "logs_data_json": logs_data_json,  # pour JS
        },
    )
