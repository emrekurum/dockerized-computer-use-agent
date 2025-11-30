FROM python:3.11-slim

# Python çıktılarını anlık görelim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Ekran ayarları (Sanal ekran için)
    DISPLAY=:1 \
    WIDTH=1024 \
    HEIGHT=768

WORKDIR /app

# 1. Linux Araçlarını Yükle (Agent'ın eli kolu bunlar)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    unzip \
    xvfb \
    x11-xserver-utils \
    xdotool \
    scrot \
    imagemagick \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# 2. Python Kütüphanelerini Yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Kodları Kopyala
COPY . .

# 4. Portları Aç (8000: API)
EXPOSE 8000

# 5. Başlatma Komutu (Sanal Ekran + Backend)
# Xvfb sanal ekranını başlatır, ardından backend'i çalıştırır.
CMD Xvfb :1 -screen 0 ${WIDTH}x${HEIGHT}x24 & \
    sleep 2 && \
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000