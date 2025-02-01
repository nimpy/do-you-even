FROM python:3.13.1-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV PORT 8080
EXPOSE 8080

WORKDIR /app
COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

COPY .env /app/.env

COPY . .

CMD ["/bin/sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]