#!/bin/sh
# Script di installazione AUTOMATICA per Alpine Linux LXC
# Con avvio automatico del server come servizio

set -e

echo "=========================================="
echo "Installazione AUTOMATICA"
echo "TurboGOLDEN Web Terminal"
echo "Alpine Linux LXC"
echo "=========================================="
echo ""

# Aggiorna i repository
echo "[1/7] Aggiornamento repository Alpine..."
apk update

# Installa dipendenze di sistema
echo "[2/7] Installazione dipendenze di sistema..."
apk add --no-cache \
    python3 \
    py3-pip \
    nginx \
    git \
    bash \
    openrc

# Clona la repository
echo "[3/7] Download repository da GitHub..."
if [ -d "/opt/goldenbridge" ]; then
    echo "Directory /opt/goldenbridge già esistente, rimuovo..."
    rm -rf /opt/goldenbridge
fi

cd /opt
git clone https://github.com/YOUR_USERNAME/goldenbridge.git
cd goldenbridge

# Installa dipendenze Python
echo "[4/7] Installazione dipendenze Python..."
pip3 install --no-cache-dir -r requirements.txt

# Configura nginx
echo "[5/7] Configurazione nginx..."
cp nginx.conf /etc/nginx/http.d/goldenbridge.conf

# Rimuovi configurazione default se esiste
if [ -f /etc/nginx/http.d/default.conf ]; then
    rm /etc/nginx/http.d/default.conf
fi

# Testa la configurazione nginx
nginx -t

# Crea servizio OpenRC per il server Flask
echo "[6/7] Creazione servizio goldenbridge..."
cat > /etc/init.d/goldenbridge <<'EOF'
#!/sbin/openrc-run

name="goldenbridge"
description="TurboGOLDEN Web Terminal Server"

command="/usr/bin/python3"
command_args="/opt/goldenbridge/app.py"
command_background=true
pidfile="/run/${RC_SVCNAME}.pid"
directory="/opt/goldenbridge"

depend() {
    need net
    after nginx
}

start_pre() {
    checkpath --directory --mode 0755 /run
}
EOF

chmod +x /etc/init.d/goldenbridge

# Abilita e avvia i servizi
echo "[7/7] Avvio servizi..."
rc-update add nginx default
rc-update add goldenbridge default

rc-service nginx restart
rc-service goldenbridge start

# Mostra lo status
sleep 2
rc-service goldenbridge status
rc-service nginx status

echo ""
echo "=========================================="
echo "Installazione completata!"
echo "=========================================="
echo ""
echo "Servizi attivi:"
echo "  - goldenbridge (Flask server sulla porta 8080)"
echo "  - nginx (reverse proxy sulla porta 80)"
echo ""
echo "Il server è già attivo!"
echo "Apri il browser su: http://$(hostname -i)"
echo ""
echo "Comandi utili:"
echo "  rc-service goldenbridge start|stop|restart|status"
echo "  rc-service nginx start|stop|restart|status"
echo ""
echo "Log del server:"
echo "  tail -f /var/log/goldenbridge.log"
echo "=========================================="
