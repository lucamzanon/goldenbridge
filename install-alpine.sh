#!/bin/sh
# Script di installazione per Alpine Linux LXC
# TurboGOLDEN Web Terminal

set -e

echo "=========================================="
echo "Installazione TurboGOLDEN Web Terminal"
echo "Alpine Linux LXC"
echo "=========================================="
echo ""

# Aggiorna i repository
echo "[1/6] Aggiornamento repository Alpine..."
apk update

# Installa dipendenze di sistema
echo "[2/6] Installazione dipendenze di sistema..."
apk add --no-cache \
    python3 \
    py3-pip \
    nginx \
    git \
    bash

# Clona la repository
echo "[3/6] Download repository da GitHub..."
if [ -d "/opt/goldenbridge" ]; then
    echo "Directory /opt/goldenbridge già esistente, rimuovo..."
    rm -rf /opt/goldenbridge
fi

cd /opt
git clone https://github.com/YOUR_USERNAME/goldenbridge.git
cd goldenbridge

# Installa dipendenze Python
echo "[4/6] Installazione dipendenze Python..."
pip3 install --no-cache-dir -r requirements.txt

# Configura nginx
echo "[5/6] Configurazione nginx..."
cp nginx.conf /etc/nginx/http.d/goldenbridge.conf

# Rimuovi configurazione default se esiste
if [ -f /etc/nginx/http.d/default.conf ]; then
    rm /etc/nginx/http.d/default.conf
fi

# Testa la configurazione nginx
nginx -t

# Abilita e avvia nginx
echo "[6/6] Avvio servizi..."
rc-update add nginx default
rc-service nginx restart

echo ""
echo "=========================================="
echo "Installazione completata!"
echo "=========================================="
echo ""
echo "Per avviare il server TurboGOLDEN:"
echo "  cd /opt/goldenbridge"
echo "  python3 app.py"
echo ""
echo "Oppure usa lo script fornito:"
echo "  /opt/goldenbridge/start.sh"
echo ""
echo "Poi apri il browser su: http://IP_DEL_LXC"
echo "=========================================="
