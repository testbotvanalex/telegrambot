# Используем официальный образ Python как базовый
FROM python:3.12-slim-bookworm

# Устанавливаем рабочую директорию в /app
WORKDIR /app

# Устанавливаем необходимые инструменты сборки и зависимости для компиляции
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    gfortran && \
    rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt в рабочую директорию
COPY requirements.txt ./

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальную часть вашего приложения в рабочую директорию
COPY . ./

# Убедитесь, что папки пакетов содержат __init__.py
RUN mkdir -p db && touch db/__init__.py && \
    mkdir -p handlers && touch handlers/__init__.py && \
    mkdir -p handlers/admin && touch handlers/admin/__init__.py && \
    mkdir -p config && touch config/__init__.py && \
    mkdir -p keyboards && touch keyboards/__init__.py && \
    mkdir -p services && touch services/__init__.py && \
    mkdir -p utils && touch utils/__init__.py

# Определяем переменную окружения PORT, которую ожидает Cloud Run
ENV PORT=8080

# Команда для запуска вашего приложения
CMD ["python", "main.py"]