# Dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install django psycopg2-binary

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]