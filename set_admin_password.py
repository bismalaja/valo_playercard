import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valorant_profile.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
try:
    u = User.objects.get(username='admin')
    u.set_password('admin')
    u.save()
    print('Admin password updated successfully!')
except User.DoesNotExist:
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Admin user created successfully!')
