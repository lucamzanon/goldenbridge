#!/bin/bash
# Script di setup per TurboGOLDEN Web Terminal

echo "=========================================="
echo "Setup TurboGOLDEN Web Terminal"
echo "=========================================="
echo ""

# Installa dipendenze Python
echo "[1/4] Installazione dipendenze Python..."
pip3 install -r requirements.txt

echo ""

# Verifica se nginx è installato
if ! command -v nginx &> /dev/null; then
    echo "[2/4] Installazione nginx..."
    apt-get update
    apt-get install -y nginx
else
    echo "[2/4] nginx già installato"
fi

echo ""

# Copia la configurazione nginx
echo "[3/4] Configurazione nginx..."
cp nginx.conf /etc/nginx/sites-available/turbogolden
ln -sf /etc/nginx/sites-available/turbogolden /etc/nginx/sites-enabled/turbogolden

# Rimuovi configurazione default se esiste
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Testa la configurazione nginx
nginx -t

echo ""

# Riavvia nginx
echo "[4/4] Riavvio nginx..."
systemctl restart nginx
systemctl enable nginx

echo ""
echo "=========================================="
echo "Setup completato!"
echo "=========================================="
echo ""
echo "Per avviare il server:"
echo "  cd /home/coder/turbogolden-web"
echo "  python3 app.py"
echo ""
echo "Poi apri il browser su: http://localhost"
echo "=========================================="
