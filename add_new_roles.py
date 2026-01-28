import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valorant_profile.settings')
django.setup()

from profiles.models import Role

roles_to_add = ['IGL', 'Leader', 'Manager']

print("Adding new roles...")
for role_name in roles_to_add:
    role, created = Role.objects.get_or_create(name=role_name)
    if created:
        print(f"Created role: {role_name}")
    else:
        print(f"Role ' {role_name} ' already exists.")

print("Done.")
