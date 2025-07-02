FROM python:3.11-slim

# Install system dependencies for file type detection and PostgreSQL
RUN apt-get update && apt-get install -y \
    libmagic1 \
    file \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "bytecrafter.main"] 