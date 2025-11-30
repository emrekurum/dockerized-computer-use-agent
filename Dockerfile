FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Sistem bağımlılıklarını yükle (Linux Tool'ları için)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    unzip \
    xvfb \
    x11-xserver-utils \
    xdotool \
    scrot \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Python kütüphanelerini yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Portları aç (8000: FastAPI, 6080: VNC opsiyonel)
EXPOSE 8000

# Uygulamayı başlat
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
