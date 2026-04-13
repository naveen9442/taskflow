# ---- Stage 1: Base image ----
# We use Python 3.11 slim — small and secure
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy only requirements first (Docker caches this layer)
# If requirements don't change, Docker skips reinstalling
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY app/ .

# Create a folder for the SQLite database
RUN mkdir -p /data

# Expose the port Flask runs on
EXPOSE 5000

# Run the app with Gunicorn (production-grade WSGI server)
# 4 worker processes handle multiple requests at once
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
