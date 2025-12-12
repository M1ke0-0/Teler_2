FROM python:3.10-slim

LABEL authors="Python XXna"

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование файлов проекта
COPY . /app

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Инициализация Alembic (если не существует)
RUN if [ ! -d "source/Database/alembic" ]; then \
    cd source/Database && alembic init alembic && cd /app; \
    fi

# Указание портов для приложения
EXPOSE 8080

# Запуск миграций и приложения
CMD ["sh", "-c", "cd source/Database && alembic upgrade head && cd /app && python main.py"]
