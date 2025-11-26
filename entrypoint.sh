#!/bin/bash
set -e
 
echo "Starting Django setup..."
python manage.py migrate --noinput
#python manage.py collectstatic --noinput
 
python manage.py shell <<END
import os
from django.contrib.auth import get_user_model
 
User = get_user_model()
username = os.getenv("DJANGO_SUPERUSER_USERNAME")
email = os.getenv("DJANGO_SUPERUSER_EMAIL")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
 
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Super user '{username}' created.")
else:
    print(f"Super user '{username}' already exists.")
END
 
exec python manage.py runserver 0.0.0.0:8000