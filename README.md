# TurboGOLDEN Terminal - Interfaccia Web Standalone

Interfaccia web completamente funzionale per connettersi a TurboGOLDEN tramite xterm.js

## File Creati

1. **turbogolden-terminal.html** - File HTML singolo con interfaccia terminale
2. **telnet-websocket-proxy.py** - Server proxy WebSocket → Telnet
3. **TURBOGOLDEN-TERMINAL-README.md** - Questa documentazione

## Caratteristiche

✅ **Singolo file HTML** - Tutto il frontend in un unico file
✅ **xterm.js** - Emulazione terminale VT220 completa
✅ **Supporto completo TurboGOLDEN** - Sequenze ANSI, colori, caratteri speciali
✅ **WebSocket proxy** - Connessione real-time al server telnet
✅ **TCP_NODELAY** - Implementato correttamente per stabilità
✅ **Login automatico** - Gestione automatica della sequenza di autenticazione

## Installazione

### Requisiti

```bash
# Python 3 con websockets
pip3 install websockets
```

### Verifica Dipendenze

```bash
python3 -c "import websockets; print('websockets OK')"
```

## Utilizzo

### Passo 1: Avvia il Proxy WebSocket

```bash
cd /home/coder
python3 telnet-websocket-proxy.py
```

Output atteso:
```
======================================================================
WebSocket Telnet Proxy per TurboGOLDEN
======================================================================
Server WebSocket in ascolto su: ws://0.0.0.0:8080

Apri il file turbogolden-terminal.html nel browser
Il proxy si connetterà a TurboGOLDEN quando richiesto
======================================================================
```

### Passo 2: Apri l'Interfaccia Web

```bash
# Opzione 1: Apri direttamente il file HTML
firefox /home/coder/turbogolden-terminal.html

# Opzione 2: Usa un server HTTP
cd /home/coder
python3 -m http.server 8000
# Poi apri: http://localhost:8000/turbogolden-terminal.html
```

### Passo 3: Connetti a TurboGOLDEN

1. Compila il form:
   - **SERVER IP**: 192.168.0.8 (default)
   - **PORTA**: 23 (default)
   - **UTENTE APPLICATIVO**: CDI (o il tuo username)
   - **PASSWORD**: [lascia vuoto se non configurata]

2. Clicca **"CONNETTI"**

3. Il sistema eseguirà automaticamente:
   - Connessione telnet a 192.168.0.8:23
   - Login Linux con utente "cdi"
   - Autenticazione applicativa TurboGOLDEN
   - Gestione automatica degli avvisi di sistema
   - Accesso al menu principale

## Configurazione

### Modificare l'IP del Server

Edita `turbogolden-terminal.html` e cambia:

```javascript
connectionConfig = {
    serverIp: '192.168.0.8',  // ← Cambia qui
    serverPort: 23,
    username: 'CDI',
    password: ''
};
```

### Modificare la Porta WebSocket

Edita `telnet-websocket-proxy.py`:

```python
WS_PORT = 8080  # ← Cambia qui
```

E in `turbogolden-terminal.html`:

```javascript
const proxyUrl = `ws://${window.location.hostname}:8080/telnet`;  // ← Cambia qui
```

## Controlli Terminale

Nella barra dei controlli in basso:

- **CTRL+C** - Invia interruzione comando
- **ESC** - Invia tasto Escape
- **CLEAR** - Pulisce schermo del terminale
- **DISCONNETTI** - Chiude la connessione e torna al login

## Architettura

```
┌─────────────────┐
│    Browser      │
│                 │
│  turbogolden-   │
│  terminal.html  │
│   (xterm.js)    │
└────────┬────────┘
         │ WebSocket
         │ ws://localhost:8080
         ↓
┌─────────────────┐
│  WebSocket      │
│  Proxy Server   │
│                 │
│  telnet-        │
│  websocket-     │
│  proxy.py       │
└────────┬────────┘
         │ Telnet (TCP)
         │ 192.168.0.8:23
         │ TCP_NODELAY=1
         ↓
┌─────────────────┐
│  TurboGOLDEN    │
│  v4.4           │
│                 │
│  Sistema ERP    │
│  VT220          │
└─────────────────┘
```

## Protocollo WebSocket

### Client → Server

```json
{
  "type": "connect",
  "host": "192.168.0.8",
  "port": 23,
  "username": "CDI",
  "password": ""
}
```

```json
{
  "type": "input",
  "data": "comando\n"
}
```

```json
{
  "type": "disconnect"
}
```

### Server → Client

```json
{ "type": "connected" }
```

```json
{
  "type": "data",
  "data": "output terminale con sequenze ANSI"
}
```

```json
{
  "type": "error",
  "message": "Descrizione errore"
}
```

```json
{ "type": "closed" }
```

## Debug

### Abilitare Log Console Browser

Apri Developer Tools (F12) → Console

Vedrai log come:
```
WebSocket connesso al proxy telnet
TurboGOLDEN Terminal caricato
```

### Abilitare Log Server Proxy

Il server proxy stampa automaticamente su console:

```
[INFO] Connessione a 192.168.0.8:23 per utente CDI
[INFO] TCP_NODELAY applicato
[INFO] Connessione completata - Menu principale raggiunto
[WebSocket] Nuovo client connesso: 140234567890
```

### Test Connessione Telnet Diretta

```bash
telnet 192.168.0.8 23
```

### Verifica WebSocket

```bash
# Test con websocat (se installato)
websocat ws://localhost:8080

# O con wscat
wscat -c ws://localhost:8080
```

## Troubleshooting

### Errore: "Impossibile connettersi al server proxy"

**Causa**: Il server proxy non è in esecuzione

**Soluzione**:
```bash
python3 telnet-websocket-proxy.py
```

### Errore: "Connessione fallita: [Errno 111] Connection refused"

**Causa**: TurboGOLDEN non raggiungibile all'IP 192.168.0.8

**Soluzione**:
- Verifica che il server sia acceso
- Verifica la connettività di rete: `ping 192.168.0.8`
- Verifica che la porta 23 sia aperta: `telnet 192.168.0.8 23`

### Caratteri Strani nel Terminale

**Causa**: Problema di encoding

**Soluzione**: Il proxy usa già `latin-1`, verifica che xterm.js riceva i dati correttamente

### Timeout Durante il Login

**Causa**: Sequenza di timing non rispettata

**Soluzione**: Modifica i `time.sleep()` in `telnet-websocket-proxy.py`:

```python
# Gestione avvisi - aumenta i tempi se necessario
time.sleep(5)   # ← Aumenta a 8 se troppo veloce
self.tn.write(b"\n")
time.sleep(2)   # ← Aumenta a 3 se necessario
self.tn.write(b" ")
time.sleep(2)   # ← Aumenta a 3 se necessario
self.tn.write(b"\n")
```

### WebSocket si Disconnette Subito

**Causa**: Errore nel proxy durante la connessione telnet

**Soluzione**: Verifica i log del proxy per dettagli dell'errore

## Personalizzazione

### Cambiare Colori Terminale

Edita `turbogolden-terminal.html`, sezione `theme`:

```javascript
theme: {
    background: '#000000',    // Sfondo nero
    foreground: '#00ff00',    // Testo verde
    cursor: '#00ff00',        // Cursore verde
    // ... altri colori
}
```

### Cambiare Dimensioni Terminale

```javascript
cols: 80,  // ← Colonne (TurboGOLDEN usa 80)
rows: 24   // ← Righe (TurboGOLDEN usa 24)
```

⚠️ **ATTENZIONE**: TurboGOLDEN è progettato per 80×24, non modificare!

### Aggiungere Autenticazione al Proxy

Edita `telnet-websocket-proxy.py` e aggiungi verifica token:

```python
async def handle_websocket(websocket, path):
    # Richiedi autenticazione
    auth_msg = await websocket.recv()
    auth = json.loads(auth_msg)

    if auth.get('token') != 'SECRET_TOKEN':
        await websocket.close(1008, "Non autorizzato")
        return

    # ... resto del codice
```

## Deployment in Produzione

### Usa HTTPS con WSS (WebSocket Secure)

1. Configura nginx con SSL
2. Proxy verso il server WebSocket
3. Usa `wss://` invece di `ws://`

### Configurazione nginx

```nginx
server {
    listen 443 ssl;
    server_name turbogolden.tuodominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        root /home/coder;
        try_files $uri $uri/ =404;
    }

    location /telnet {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }
}
```

### Servizio systemd

Crea `/etc/systemd/system/turbogolden-proxy.service`:

```ini
[Unit]
Description=TurboGOLDEN WebSocket Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/coder
ExecStart=/usr/bin/python3 /home/coder/telnet-websocket-proxy.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Abilita e avvia:

```bash
sudo systemctl enable turbogolden-proxy
sudo systemctl start turbogolden-proxy
sudo systemctl status turbogolden-proxy
```

## Sicurezza

⚠️ **IMPORTANTE**: Questa è una configurazione base per sviluppo/uso interno.

Per produzione:

- [ ] Implementare autenticazione utente
- [ ] Usare HTTPS/WSS
- [ ] Limitare accessi per IP
- [ ] Implementare rate limiting
- [ ] Aggiungere logging delle sessioni
- [ ] Crittografare le password
- [ ] Configurare firewall
- [ ] Usare reverse proxy (nginx)

## Vantaggi di Questa Soluzione

✅ **Un solo file HTML** - Facile da distribuire
✅ **Proxy standalone** - Non richiede Flask o dipendenze pesanti
✅ **WebSocket nativo** - Connessione real-time bidirezionale
✅ **xterm.js** - Emulazione terminale professionale
✅ **Configurazione semplice** - Pochi parametri da modificare
✅ **Debug facile** - Log chiari su console e server

## Alternative

### Usare il Server Flask Esistente

Se preferisci Flask:

```bash
cd /home/coder/turbogolden-web
python3 app.py
```

Poi apri: http://localhost:8080

### Usare SSH + Web Terminal

Se TurboGOLDEN fosse accessibile via SSH:

```bash
# Installa ttyd
apt-get install ttyd

# Avvia
ttyd -p 8080 ssh cdi@192.168.0.8
```

## Link Utili

- **xterm.js**: https://xtermjs.org/
- **WebSockets Python**: https://websockets.readthedocs.io/
- **Documentazione TurboGOLDEN**: [/home/coder/goldenbridge/docs/](../goldenbridge/docs/)
- **Configurazioni AnzioWIN**: [/home/coder/anziowin/](../anziowin/)

## Versione

- **Versione**: 1.0
- **Data**: 1 Gennaio 2026
- **Autore**: Sistema TurboGOLDEN Web Terminal
- **Compatibilità**: TurboGOLDEN v4.4

---

**Pronto all'uso!** 🚀

Avvia il proxy e apri il file HTML nel browser per connetterti a TurboGOLDEN.
