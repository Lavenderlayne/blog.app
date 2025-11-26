# 1. Використовуємо легкий образ Python
FROM python:3.10-slim

# 2. Вимикаємо створення .pyc файлів та буферизацію виводу (корисно для логів)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Встановлюємо робочу директорію
WORKDIR /app

# 4. Встановлюємо залежності системи (потрібно для деяких python-пакетів)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Копіюємо requirements і встановлюємо бібліотеки
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# 6. Копіюємо весь код проєкту
COPY . /app/

# 7. Збираємо статику (CSS/JS)
RUN python manage.py collectstatic --noinput

# 8. Відкриваємо порт (формально для документації, Render ігнорує це і використовує PORT env)
EXPOSE 8000

# 9. Запускаємо Gunicorn
# Замініть 'myproject' на назву вашої папки з settings.py
# Приберіть python create_superuser.py && \ якщо не використовуєте Postrges
CMD python manage.py migrate && \
    python create_superuser.py && \ 
    gunicorn dlango_blog.wsgi:application --bind 0.0.0.0:8000