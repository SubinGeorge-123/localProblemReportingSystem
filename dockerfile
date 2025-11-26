FROM python:3.11-slim
 
ARG DJANGO_SUPERUSER_USERNAME
ARG DJANGO_SUPERUSER_EMAIL
ARG DJANGO_SUPERUSER_PASSWORD
ENV DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME}
ENV DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL}
ENV DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}
 
WORKDIR /app

# Install curl for health checks and any other tools
RUN apt-get update && apt-get install -y curl && apt-get clean
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .
 
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
 
EXPOSE 8000
 
ENTRYPOINT ["/app/entrypoint.sh"]