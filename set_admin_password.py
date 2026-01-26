import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valorant_profile.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'admin'

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser '{username}'...")
    User.objects.create_superuser(username, email, password)
    print("Superuser created successfully!")
else:
    print(f"Superuser '{username}' already exists. Resetting password...")
    u = User.objects.get(username=username)
    u.set_password(password)
    u.save()
    print("Password updated successfully!")

print("-" * 30)
print(f"Username: {username}")
print(f"Password: {password}")
print("-" * 30)
