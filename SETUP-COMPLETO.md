# Setup Completo TurboGOLDEN con Traefik

Configurazione completa per esporre **golden.orofruit.com** tramite il tuo Traefik esistente.

---

## 📋 Architettura

```
Internet
   ↓
Cloudflare (SSL)
   ↓
Traefik (192.168.8.x)
   ↓
┌─────────────────────────────────────────────────────┐
│ golden.orofruit.com                                 │
│   ├─ /           → 192.168.8.113:8000 (nginx)      │
│   └─ /telnet     → 192.168.8.113:8080 (websocket)  │
└─────────────────────────────────────────────────────┘
   ↓
LXC 192.168.8.113
   ├─ nginx (porta 8000) → turbogolden-terminal.html
   └─ websocket proxy (porta 8080) → 192.168.0.8:23
```

---

## 🚀 PASSO 1: Setup LXC 192.168.8.113

Sul LXC Debian esegui:

```bash
# 1. Installa dipendenze
apt-get update
apt-get install -y git python3 python3-pip nginx

# 2. Clona repository
cd /opt
git clone https://github.com/lucamzanon/goldenbridge.git
cd goldenbridge

# 3. Installa dipendenze Python
pip3 install websockets

# 4. Crea servizio systemd per WebSocket proxy
cat > /etc/systemd/system/turbogolden-proxy.service << 'EOF'
[Unit]
Description=TurboGOLDEN WebSocket Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/goldenbridge
ExecStart=/usr/bin/python3 /opt/goldenbridge/telnet-websocket-proxy.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable turbogolden-proxy
systemctl start turbogolden-proxy

# 5. Configura nginx
cat > /etc/nginx/sites-available/turbogolden << 'EOF'
server {
    listen 8000;
    server_name 192.168.8.113 golden.orofruit.com;

    root /opt/goldenbridge;
    index turbogolden-terminal.html;

    location / {
        try_files $uri $uri/ =404;
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
nginx -t
systemctl restart nginx

# 6. Verifica che i servizi siano attivi
systemctl status turbogolden-proxy
systemctl status nginx
netstat -tlnp | grep -E '(8000|8080)'
```

---

## 🔧 PASSO 2: Configura Traefik

Sul server Traefik (dove hai `/etc/traefik/`):

```bash
# 1. Copia il file di configurazione
cat > /etc/traefik/conf.d/golden-orofruit.yaml << 'EOF'
http:
  routers:
    # Router principale per golden.orofruit.com
    golden-main:
      rule: "Host(`golden.orofruit.com`)"
      service: golden-service
      entryPoints:
        - websecure
      priority: 100
      tls: {}

    # Router per WebSocket (con priorità maggiore per matchare prima)
    golden-websocket:
      rule: "Host(`golden.orofruit.com`) && PathPrefix(`/telnet`)"
      service: golden-websocket-service
      entryPoints:
        - websecure
      priority: 200
      tls: {}

  services:
    # Servizio per interfaccia web HTML (porta 8000)
    golden-service:
      loadBalancer:
        servers:
          - url: "http://192.168.8.113:8000"
        passHostHeader: true

    # Servizio per WebSocket proxy (porta 8080)
    golden-websocket-service:
      loadBalancer:
        servers:
          - url: "http://192.168.8.113:8080"
        passHostHeader: true
EOF

# 2. Verifica che il file sia sintatticamente corretto
cat /etc/traefik/conf.d/golden-orofruit.yaml

# 3. Traefik rileverà automaticamente il file (watch: true)
# Opzionale: puoi riavviare Traefik se vuoi essere sicuro
# systemctl restart traefik
# oppure se è in Docker:
# docker restart traefik

# 4. Verifica nei log che Traefik abbia caricato la config
tail -f /var/log/traefik/traefik.log | grep golden
```

---

## 🌐 PASSO 3: Configura DNS (se non già fatto)

Assicurati che **golden.orofruit.com** punti al tuo server Traefik.

Se usi Cloudflare:
1. Vai su Cloudflare Dashboard → DNS
2. Aggiungi record:
   - **Type**: A
   - **Name**: golden
   - **IPv4 address**: IP pubblico del tuo Traefik
   - **Proxy status**: Proxied (arancione) 🟠

---

## ✅ PASSO 4: Verifica

### Test sul LXC (192.168.8.113)

```bash
# Test HTML locale
curl -I http://localhost:8000/turbogolden-terminal.html

# Test WebSocket locale
netstat -tlnp | grep 8080

# Test dalla rete locale
curl -I http://192.168.8.113:8000/turbogolden-terminal.html
```

### Test da Traefik

```bash
# Dal server Traefik (o altro host nella LAN)
curl -I http://192.168.8.113:8000/turbogolden-terminal.html
```

### Test pubblico

```bash
# Da qualsiasi PC
curl -I https://golden.orofruit.com
```

### Test browser

Apri: **https://golden.orofruit.com**

Dovresti vedere l'interfaccia di login. Inserisci:
- **Server IP**: 192.168.0.8
- **Porta**: 23
- **Utente**: CDI
- **Password**: [lascia vuoto]

Clicca **CONNETTI**

---

## 🐛 Troubleshooting

### 1. Servizi non raggiungibili dall'esterno

```bash
# Verifica che Traefik abbia caricato la config
docker logs traefik 2>&1 | grep golden
# oppure
journalctl -u traefik | grep golden

# Verifica le route attive
curl http://localhost:8080/api/http/routers | jq | grep golden

# Verifica i servizi
curl http://localhost:8080/api/http/services | jq | grep golden
```

### 2. WebSocket non funziona

Verifica che il proxy sia in ascolto:
```bash
# Sul LXC
netstat -tlnp | grep 8080
systemctl status turbogolden-proxy
journalctl -u turbogolden-proxy -f
```

### 3. Cloudflare blocca WebSocket

Se usi Cloudflare proxy (🟠), potrebbe bloccare i WebSocket.

Soluzione:
- Opzione A: Disabilita proxy per golden.orofruit.com (⚫ DNS only)
- Opzione B: Assicurati che Cloudflare sia configurato per WebSocket

### 4. Certificato SSL

I certificati vengono gestiti automaticamente da Cloudflare Origin Certificates (configurazione che hai già).

Verifica che `/etc/traefik/ssl/cloudflare-origin.crt` sia valido per `*.orofruit.com`.

---

## 📊 Comandi Utili

### Sul LXC 192.168.8.113

```bash
# Restart proxy WebSocket
systemctl restart turbogolden-proxy

# Log proxy
journalctl -u turbogolden-proxy -f

# Restart nginx
systemctl restart nginx

# Log nginx
tail -f /var/log/nginx/access.log

# Stato servizi
systemctl status turbogolden-proxy nginx
```

### Sul server Traefik

```bash
# Verifica configurazione caricata
ls -lh /etc/traefik/conf.d/golden-orofruit.yaml

# Log Traefik
tail -f /var/log/traefik/traefik.log

# Restart Traefik (se necessario)
systemctl restart traefik
# oppure
docker restart traefik
```

---

## 🔄 Aggiornamento

Per aggiornare il sistema:

```bash
# Sul LXC
cd /opt/goldenbridge
git pull
systemctl restart turbogolden-proxy nginx
```

---

## 📁 File Repository

Il file `golden-orofruit.yaml` è nel repository:
```bash
https://github.com/lucamzanon/goldenbridge/blob/main/golden-orofruit.yaml
```

Per copiarlo direttamente sul server Traefik:
```bash
cd /etc/traefik/conf.d/
wget https://raw.githubusercontent.com/lucamzanon/goldenbridge/main/golden-orofruit.yaml
```

---

## 🎯 Riepilogo Porte

| Servizio          | Porta | Protocollo | Descrizione                |
|-------------------|-------|------------|----------------------------|
| nginx (HTML)      | 8000  | HTTP       | Interfaccia web            |
| WebSocket proxy   | 8080  | HTTP/WS    | Proxy verso TurboGOLDEN    |
| TurboGOLDEN       | 23    | Telnet     | Server gestionale (remoto) |

---

## ✅ Checklist Installazione

- [ ] LXC 192.168.8.113 configurato
- [ ] nginx in ascolto su porta 8000
- [ ] turbogolden-proxy in ascolto su porta 8080
- [ ] File `/etc/traefik/conf.d/golden-orofruit.yaml` creato
- [ ] Traefik ha rilevato la nuova configurazione
- [ ] DNS golden.orofruit.com configurato
- [ ] Test locale funzionante
- [ ] Test pubblico funzionante
- [ ] WebSocket funzionante
- [ ] Login a TurboGOLDEN riuscito

---

**Pronto! 🚀**

Accedi a: **https://golden.orofruit.com**
