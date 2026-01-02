#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# Script di installazione TurboGOLDEN Web Terminal
# LXC: 192.168.8.113
# Dominio: golden.orofruit.com
# ═══════════════════════════════════════════════════════════════

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  TurboGOLDEN Web Terminal - Installazione LXC           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Rileva metodo di installazione
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker rilevato - Installazione con Docker Compose"
    METHOD="docker"
elif [ -f /.dockerenv ]; then
    echo "⚠️  Ambiente Docker rilevato ma docker-compose non disponibile"
    echo "   Procedendo con installazione nativa..."
    METHOD="native"
else
    echo "📦 Installazione nativa (senza Docker)"
    METHOD="native"
fi

echo ""
echo "Metodo: $METHOD"
echo ""

if [ "$METHOD" = "docker" ]; then
    # ═══════════════════════════════════════════════════════════════
    # INSTALLAZIONE DOCKER COMPOSE
    # ═══════════════════════════════════════════════════════════════

    echo "[1/3] Creazione rete Traefik..."
    docker network create traefik-public 2>/dev/null || echo "   Rete traefik-public già esistente"

    echo "[2/3] Avvio container..."
    docker-compose up -d

    echo "[3/3] Verifica deployment..."
    sleep 3
    docker-compose ps

    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║              INSTALLAZIONE COMPLETATA (Docker)           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 Container attivi:"
    docker-compose ps --format table
    echo ""
    echo "📝 Log in tempo reale:"
    echo "   docker-compose logs -f"
    echo ""

else
    # ═══════════════════════════════════════════════════════════════
    # INSTALLAZIONE NATIVA
    # ═══════════════════════════════════════════════════════════════

    echo "[1/6] Aggiornamento sistema..."
    apt-get update -qq

    echo "[2/6] Installazione dipendenze..."
    apt-get install -y python3 python3-pip nginx >/dev/null 2>&1

    echo "[3/6] Installazione websockets..."
    pip3 install -q websockets

    echo "[4/6] Configurazione servizio systemd..."
    cat > /etc/systemd/system/turbogolden-proxy.service << 'EOF'
[Unit]
Description=TurboGOLDEN WebSocket Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/telnet-websocket-proxy.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable turbogolden-proxy >/dev/null 2>&1
    systemctl start turbogolden-proxy

    echo "[5/6] Configurazione nginx..."
    cat > /etc/nginx/sites-available/turbogolden << EOF
server {
    listen 8000;
    server_name 192.168.8.113;

    root $(pwd);
    index turbogolden-terminal.html;

    location / {
        try_files \$uri \$uri/ =404;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/turbogolden /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t >/dev/null 2>&1
    systemctl restart nginx

    echo "[6/6] Verifica servizi..."
    sleep 2

    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║              INSTALLAZIONE COMPLETATA (Native)           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "📊 Servizi attivi:"
    systemctl status turbogolden-proxy --no-pager -l | head -3
    systemctl status nginx --no-pager -l | head -3
    echo ""
    echo "📝 Log in tempo reale:"
    echo "   journalctl -u turbogolden-proxy -f"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# INFORMAZIONI COMUNI
# ═══════════════════════════════════════════════════════════════

echo "🔧 Configurazione Traefik:"
echo ""
echo "   Opzione A - File Provider:"
echo "   ────────────────────────────"
echo "   cp traefik-config.yml /etc/traefik/dynamic/turbogolden.yml"
echo "   docker restart traefik"
echo ""
echo "   Opzione B - Docker Provider:"
echo "   ────────────────────────────"
echo "   (già configurato se usi docker-compose.yml)"
echo ""
echo "🌐 Endpoint locali:"
echo "   • HTML:      http://192.168.8.113:8000"
echo "   • WebSocket: ws://192.168.8.113:8080/telnet"
echo ""
echo "🌐 URL pubblico (dopo configurazione Traefik):"
echo "   • http://golden.orofruit.com"
echo ""
echo "📖 Documentazione completa:"
echo "   cat INSTALL-TRAEFIK.md"
echo ""
echo "✅ Installazione completata con successo!"
echo ""
