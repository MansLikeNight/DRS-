# Use Python 3.12 slim image (avoids mise extraction issues)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Create a startup script that runs migrations and creates superuser before starting gunicorn
RUN echo '#!/bin/bash\npython manage.py migrate --noinput\npython manage.py create_superuser_auto\nexec gunicorn DailyDrillReport.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120' > /app/start.sh && chmod +x /app/start.sh

# Run startup script
CMD ["/app/start.sh"]
