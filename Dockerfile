# Use the official Playwright Python image — Chromium + all OS deps pre-installed
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download/verify the Chromium browser at build time so it's baked into the image
RUN playwright install chromium

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Migrate, seed, and start gunicorn
CMD ["sh", "-c", "python manage.py migrate && python manage.py setup_project && gunicorn valorant_profile.wsgi --bind 0.0.0.0:8000 --log-file -"]
