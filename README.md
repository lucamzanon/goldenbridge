# TurboGOLDEN Web Terminal

Server web che espone il sistema TurboGOLDEN tramite un terminale web basato su xterm.js.

## Architettura

```
┌─────────────┐     ┌─────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser   │────▶│  nginx  │────▶│ Flask+Socket │────▶│ TurboGOLDEN  │
│  (xterm.js) │     │  :80    │     │     :8080    │     │  192.168.0.8 │
└─────────────┘     └─────────┘     └──────────────┘     └──────────────┘
```

## Componenti

- **Frontend**: HTML + xterm.js (terminale web)
- **Backend**: Flask + Flask-SocketIO (server WebSocket)
- **Reverse Proxy**: nginx (porta 80)
- **Libreria**: turbogolden_client.py (connessione al sistema)

## Installazione

### Requisiti

- Python 3
- nginx
- Accesso alla rete con il server TurboGOLDEN (192.168.0.8)

### Setup

```bash
cd /home/coder/turbogolden-web
sudo ./setup.sh
```

Lo script:
1. Installa le dipendenze Python
2. Installa nginx (se non presente)
3. Configura nginx come reverse proxy
4. Riavvia nginx

## Utilizzo

### Avvio del server

```bash
cd /home/coder/turbogolden-web
./start.sh
```

Oppure manualmente:

```bash
python3 app.py
```

### Accesso

Apri il browser su:
- **http://localhost** (tramite nginx)
- **http://localhost:8080** (diretto al Flask)

### Login

1. Inserisci il nome utente TurboGOLDEN
2. Clicca "Connetti"
3. Il sistema si connetterà automaticamente

## Configurazione

### Porte

- **Flask**: 8080 (configurabile in `app.py`)
- **nginx**: 80 (configurabile in `nginx.conf`)

### File di configurazione

- `app.py`: Server Flask
- `templates/index.html`: Frontend con xterm.js
- `nginx.conf`: Configurazione nginx
- `requirements.txt`: Dipendenze Python

## Funzionalità

- Terminale web completo con xterm.js
- Connessione WebSocket real-time
- Supporto VT220 con codici di controllo
- Dimensione terminale: 80x24 (standard TurboGOLDEN)
- Gestione automatica della sessione
- Riconnessione in caso di errore

## Debug

### Abilitare debug nel backend

Modifica `app.py`:

```python
self.client = TurboGoldenClient(debug=True)
```

### Log nginx

```bash
tail -f /var/log/nginx/turbogolden_access.log
tail -f /var/log/nginx/turbogolden_error.log
```

### Test connessione diretta

```bash
# Test Flask diretto
curl http://localhost:8080

# Test nginx
curl http://localhost
```

## Tunnel Cloudflare (da configurare)

Per esporre il servizio su internet tramite Cloudflare Tunnel:

```bash
# Installa cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login a Cloudflare
cloudflared tunnel login

# Crea il tunnel
cloudflared tunnel create turbogolden

# Configura il tunnel per puntare a localhost:80
cloudflared tunnel route dns turbogolden turbogolden.tuodominio.com

# Avvia il tunnel
cloudflared tunnel run turbogolden
```

## Troubleshooting

### Errore: "Sessione non attiva"

Il server Flask non è in esecuzione. Avvia con `./start.sh`

### Errore: "Connessione fallita"

- Verifica che il server TurboGOLDEN sia raggiungibile (192.168.0.8)
- Controlla i log del backend
- Verifica il nome utente

### nginx non parte

```bash
# Verifica la configurazione
sudo nginx -t

# Controlla i log
sudo tail -f /var/log/nginx/error.log
```

### WebSocket non funziona

- Verifica che nginx abbia il supporto WebSocket
- Controlla la configurazione proxy in `nginx.conf`
- Verifica i timeout

## Struttura File

```
turbogolden-web/
├── app.py                 # Server Flask + WebSocket
├── templates/
│   └── index.html        # Frontend con xterm.js
├── static/               # File statici (vuoto)
├── requirements.txt      # Dipendenze Python
├── nginx.conf           # Configurazione nginx
├── setup.sh             # Script installazione
├── start.sh             # Script avvio
└── README.md            # Questa documentazione
```

## Sicurezza

⚠️ **IMPORTANTE**: Questa configurazione è per uso locale/sviluppo.

Per produzione:
- Implementare autenticazione
- Usare HTTPS
- Configurare firewall
- Limitare accessi
- Usare secret key sicura in Flask

## Licenza

Basato su TurboGOLDEN v4.4 e libreria turbogolden_client.py
