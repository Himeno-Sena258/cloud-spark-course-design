FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target /build/packages

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /build/packages /app/packages
COPY . .

ENV PYTHONPATH=/app/packages
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000

EXPOSE 5000

CMD ["python", "app.py"]
