FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip list | grep -E "boto3|langchain" || exit 1

# Copy application
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
