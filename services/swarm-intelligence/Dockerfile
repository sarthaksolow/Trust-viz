FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN retries=5; \
    for i in $(seq 1 $retries); do \
        pip install --no-cache-dir --default-timeout=1000 -r requirements.txt && break || \
        echo "Attempt $i failed, retrying in 5 seconds..." && sleep 5; \
    done

COPY . .

EXPOSE 5001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
