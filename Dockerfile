FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy python requirements and install
COPY iptv/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY iptv /app/iptv

WORKDIR /app/iptv

EXPOSE 5000

# Set default CMD to Flask Web App
CMD ["python", "app.py"]
