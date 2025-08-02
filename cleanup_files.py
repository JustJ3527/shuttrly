# cleanup_files.py
import os
import django
import sys

# 👉 Adapter le chemin vers ton projet Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuttrly.settings')
django.setup()

# Exécuter le nettoyage
from users.utils import cleanup_old_files

if __name__ == '__main__':
    deleted = cleanup_old_files()
    print(f"✅ Cleanup finished: {deleted} files deleted.")