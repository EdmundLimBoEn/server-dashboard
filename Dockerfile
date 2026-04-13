FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn psutil jinja2 httpx

COPY app.py .
COPY templates/ ./templates/

EXPOSE 0310

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "0310"]