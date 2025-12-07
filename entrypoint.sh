#!/bin/bash
set -e

echo "Starting Django setup..."

if [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "ERROR: DJANGO_SECRET_KEY is not set!"
    echo "For development, you can set a temporary key:"
    echo "  export DJANGO_SECRET_KEY='django-insecure-test-key-123'"
    exit 1
fi

echo "Running migrations..."
python manage.py migrate --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
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
else
    echo "Superuser credentials not provided, skipping superuser creation."
fi

echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:8000 --insecure