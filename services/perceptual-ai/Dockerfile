FROM python:3.9-slim

WORKDIR /app

# System packages for imagehash and PIL
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY src/ .

EXPOSE 5003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5003", "--reload"]