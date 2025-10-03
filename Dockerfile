FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

ENV DJANGO_SETTINGS_MODULE=compliance.settings

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV GITLEAKS_VERSION=8.18.3

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates git \
    && curl -L https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz | tar xz -C /usr/local/bin \
    && chmod +x /usr/local/bin/gitleaks \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]