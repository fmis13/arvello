FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /opt/arvello

RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libharfbuzz0b \
    libffi-dev \
    libpangoft2-1.0-0 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    python3-venv \
    python3-pip \
    && apt-get clean

COPY . /opt/arvello

RUN pip install --upgrade pip \
    && pip install pillow==10.2.0 \
    && pip install -r /opt/arvello/requirements.txt \
    && pip install gunicorn psycopg2-binary python-decouple

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "arvello.wsgi:application"]
