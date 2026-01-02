# Installazione TurboGOLDEN con Traefik

Guida completa per esporre TurboGOLDEN su **golden.orofruit.com** tramite Traefik.

## Informazioni Sistema

- **Dominio**: golden.orofruit.com
- **IP LXC**: 192.168.8.113
- **Server TurboGOLDEN**: 192.168.0.8:23

---

## Opzione 1: Deploy con Docker Compose (RACCOMANDATO)

### Prerequisiti

```bash
# Installa Docker e Docker Compose
apt-get update
apt-get install -y docker.io docker-compose git

# Avvia Docker
systemctl enable docker
systemctl start docker
```

### Crea rete Traefik (se non esiste)

```bash
docker network create traefik-public
```

### Deploy

```bash
# Clona repository
cd /opt
git clone https://github.com/lucamzanon/goldenbridge.git
cd goldenbridge

# Avvia i container
docker-compose up -d

# Verifica
docker-compose ps
docker-compose logs -f
```

### Labels Traefik

I servizi sono già configurati con le labels Traefik nel `docker-compose.yml`:

- **turbogolden-web**: Serve l'HTML su `golden.orofruit.com`
- **turbogolden-proxy**: WebSocket proxy su `golden.orofruit.com/telnet`

---

## Opzione 2: Installazione Nativa (senza Docker)

### 1. Installa dipendenze

```bash
apt-get update
apt-get install -y git python3 python3-pip nginx
cd /root
git clone https://github.com/lucamzanon/goldenbridge.git
cd goldenbridge
pip3 install websockets
chmod +x *.sh *.py
```

### 2. Crea servizio systemd per il proxy

```bash
cat > /etc/systemd/system/turbogolden-proxy.service << 'EOF'
[Unit]
Description=TurboGOLDEN WebSocket Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/goldenbridge
ExecStart=/usr/bin/python3 /root/goldenbridge/telnet-websocket-proxy.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable turbogolden-proxy
systemctl start turbogolden-proxy
```

### 3. Configura nginx

```bash
cat > /etc/nginx/sites-available/turbogolden << 'EOF'
server {
    listen 8000;
    server_name 192.168.8.113;

    root /root/goldenbridge;
    index turbogolden-terminal.html;

    location / {
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-cache";
    }
}
EOF

ln -sf /etc/nginx/sites-available/turbogolden /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### 4. Configura Traefik (File Provider)

Copia il file di configurazione Traefik:

```bash
# Se hai Traefik configurato con file provider
cp traefik-config.yml /etc/traefik/dynamic/turbogolden.yml

# Ricarica Traefik (dipende dalla tua configurazione)
docker restart traefik
# oppure
systemctl restart traefik
```

Il file `traefik-config.yml` contiene:
- Router per `golden.orofruit.com` → 192.168.8.113:8000 (nginx)
- Router per `golden.orofruit.com/telnet` → 192.168.8.113:8080 (websocket)

---

## Opzione 3: Traefik con Docker Labels (se Traefik monitora Docker)

Se il tuo Traefik è configurato per usare il provider Docker, usa il `docker-compose.yml` fornito.

Le labels sono già configurate:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.turbogolden-web.rule=Host(`golden.orofruit.com`)"
  - "traefik.http.routers.turbogolden-web.entrypoints=web"
  # ... etc
```

---

## Verifica Installazione

### Test locale (sul LXC 192.168.8.113)

```bash
# Test nginx
curl -I http://localhost:8000/turbogolden-terminal.html

# Test WebSocket proxy
netstat -tlnp | grep 8080

# Log proxy
journalctl -u turbogolden-proxy -f
# oppure
docker-compose logs -f turbogolden-proxy
```

### Test da esterno

```bash
# Da un altro host
curl -I http://golden.orofruit.com

# Test WebSocket (con websocat)
websocat ws://golden.orofruit.com/telnet
```

### Accesso browser

Apri: **http://golden.orofruit.com**

Inserisci:
- Server IP: `192.168.0.8`
- Porta: `23`
- Utente: `CDI`
- Password: [lascia vuoto]

Clicca **CONNETTI**

---

## Configurazione Traefik (Riferimento)

### File Provider

Se usi Traefik con file provider, la configurazione statica deve includere:

```yaml
# /etc/traefik/traefik.yml
providers:
  file:
    directory: /etc/traefik/dynamic
    watch: true

entryPoints:
  web:
    address: ":80"
```

Poi copia `traefik-config.yml` in `/etc/traefik/dynamic/turbogolden.yml`.

### Docker Provider

Se usi Traefik con Docker provider:

```yaml
# /etc/traefik/traefik.yml
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: traefik-public

entryPoints:
  web:
    address: ":80"
```

Poi usa `docker-compose up -d`.

---

## Troubleshooting

### Servizi non raggiungibili

```bash
# Verifica che Traefik veda i servizi
# Con Docker:
docker logs traefik | grep turbogolden

# Verifica DNS
nslookup golden.orofruit.com

# Verifica porte locali
netstat -tlnp | grep -E '(8000|8080)'
```

### WebSocket non funziona

Assicurati che Traefik supporti WebSocket:

```yaml
# Nel router Traefik
http:
  routers:
    turbogolden-websocket:
      rule: "Host(`golden.orofruit.com`) && PathPrefix(`/telnet`)"
      # ...
```

### Log

```bash
# Docker
docker-compose logs -f

# Systemd
journalctl -u turbogolden-proxy -f

# Nginx
tail -f /var/log/nginx/access.log
```

---

## Comandi Utili

### Docker Compose

```bash
# Avvia
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Log
docker-compose logs -f

# Rebuild
docker-compose up -d --build
```

### Systemd

```bash
# Status
systemctl status turbogolden-proxy

# Restart
systemctl restart turbogolden-proxy

# Log
journalctl -u turbogolden-proxy -f
```

### Nginx

```bash
# Test config
nginx -t

# Reload
systemctl reload nginx

# Restart
systemctl restart nginx
```

---

## Architettura

```
┌─────────────────┐
│   Browser       │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────────────────────────┐
│  Traefik (reverse proxy)            │
│  golden.orofruit.com                │
└────────┬────────────────────────────┘
         │
         ├─→ /              → nginx:8000 (HTML)
         │   192.168.8.113
         │
         └─→ /telnet        → proxy:8080 (WebSocket)
             192.168.8.113
                    │
                    ↓ Telnet
             ┌──────────────┐
             │ TurboGOLDEN  │
             │ 192.168.0.8  │
             └──────────────┘
```

---

## File Creati

- `docker-compose.yml` - Configurazione Docker Compose
- `nginx-simple.conf` - Configurazione nginx per container
- `traefik-config.yml` - Configurazione Traefik (file provider)
- `INSTALL-TRAEFIK.md` - Questa guida

---

## URL Finale

**🌐 http://golden.orofruit.com**

Pronto all'uso! 🚀
