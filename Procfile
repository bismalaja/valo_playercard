web: pip install -r requirements.txt && python manage.py migrate && python manage.py setup_project && gunicorn valorant_profile.wsgi --log-file -
dev: python manage.py migrate && python manage.py setup_project && python manage.py runserver
