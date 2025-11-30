FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DISPLAY=:1 \
    WIDTH=1024 \
    HEIGHT=768

WORKDIR /app

# 1. Linux Araçlarını, Masaüstünü ve Firefox'u Yükle
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
    x11vnc \
    # YENİ EKLENENLER:
    fluxbox \
    xterm \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# 2. noVNC Kurulumu
RUN git clone https://github.com/novnc/noVNC.git /opt/novnc \
    && git clone https://github.com/novnc/websockify /opt/novnc/utils/websockify \
    && ln -s /opt/novnc/vnc.html /opt/novnc/index.html

# 3. Python Kütüphaneleri
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Proje Dosyaları
COPY . .

# 5. Portlar
EXPOSE 8000 6080

# 6. BAŞLATMA KOMUTU (GÜNCELLENDİ)
# Xvfb -> Fluxbox (Masaüstü) -> VNC -> Proxy -> Backend
CMD Xvfb :1 -screen 0 ${WIDTH}x${HEIGHT}x24 & \
    sleep 2 && \
    fluxbox & \
    sleep 2 && \
    x11vnc -display :1 -nopw -forever -quiet & \
    sleep 2 && \
    /opt/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 6080 & \
    sleep 2 && \
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000