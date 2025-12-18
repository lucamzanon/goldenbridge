#!/bin/sh
# Script di installazione per Alpine Linux LXC

set -e

echo "=========================================="
echo "Setup TurboGOLDEN Web Terminal"
echo "=========================================="
echo ""

# Aggiorna i repository
echo "[1/6] Aggiornamento repository Alpine..."
apk update

# Installa dipendenze di sistema
echo "[2/6] Installazione dipendenze di sistema..."
apk add --no-cache python3 py3-pip nginx git bash py3-flask py3-flask-socketio

# Clona la repository
echo "[3/6] Download repository da GitHub..."
if [ -d "/opt/goldenbridge" ]; then
    echo "Directory /opt/goldenbridge gia esistente, rimuovo..."
    rm -rf /opt/goldenbridge
fi

cd /opt
git clone https://github.com/lucamzanon/goldenbridge.git
cd goldenbridge

# Installa dipendenze Python mancanti
echo "[4/6] Installazione dipendenze Python..."
pip3 install --break-system-packages -r requirements.txt 2>/dev/null || echo "Dipendenze gia installate"

# Configura nginx
echo "[5/6] Configurazione nginx..."
cp nginx.conf /etc/nginx/http.d/goldenbridge.conf

# Rimuovi configurazione default se esiste
if [ -f /etc/nginx/http.d/default.conf ]; then
    rm /etc/nginx/http.d/default.conf
fi

# Testa la configurazione nginx
nginx -t

# Riavvia nginx
echo "[6/6] Riavvio nginx..."
rc-service nginx restart
rc-update add nginx default

echo ""
echo "=========================================="
echo "Setup completato!"
echo "=========================================="
echo ""
echo "Per avviare il server:"
echo "  cd /opt/goldenbridge"
echo "  python3 app.py"
echo ""
echo "Poi apri il browser su: http://$(hostname -i)"
echo "=========================================="
