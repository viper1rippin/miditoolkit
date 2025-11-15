FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy parent directory miditoolkit package
COPY ../ /app/miditoolkit/
RUN pip install -e /app/miditoolkit/

# Copy backend code
COPY backend/ /app/backend/

# Create necessary directories
RUN mkdir -p /app/backend/uploads /app/backend/outputs

# Set environment variables
ENV FLASK_APP=backend/app.py
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "backend/app.py"]
