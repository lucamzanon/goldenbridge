#!/bin/bash

# Script di avvio TurboGOLDEN Web Terminal
# Avvia il proxy WebSocket e apre il browser

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        TurboGOLDEN WEB TERMINAL - AVVIO SISTEMA         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Verifica dipendenze
echo "[1/4] Verifica dipendenze..."

if ! command -v python3 &> /dev/null; then
    echo "❌ ERRORE: python3 non trovato!"
    exit 1
fi

if ! python3 -c "import websockets" 2>/dev/null; then
    echo "⚠️  Modulo websockets non trovato, installazione in corso..."
    pip3 install websockets
fi

echo "✅ Dipendenze OK"
echo ""

# Avvia il proxy WebSocket
echo "[2/4] Avvio proxy WebSocket..."
python3 /home/coder/telnet-websocket-proxy.py &
PROXY_PID=$!

echo "✅ Proxy avviato (PID: $PROXY_PID)"
echo ""

# Attendi che il proxy sia pronto
echo "[3/4] Attesa inizializzazione proxy..."
sleep 2
echo "✅ Proxy pronto"
echo ""

# Avvia server HTTP per servire il file HTML
echo "[4/4] Avvio server HTTP..."
cd /home/coder
python3 -m http.server 8000 &
HTTP_PID=$!

sleep 1
echo "✅ Server HTTP avviato (PID: $HTTP_PID)"
echo ""

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    SISTEMA AVVIATO                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Apri il browser su:"
echo "   → http://localhost:8000/turbogolden-terminal.html"
echo ""
echo "📊 Servizi attivi:"
echo "   → WebSocket Proxy: ws://localhost:8080 (PID: $PROXY_PID)"
echo "   → HTTP Server: http://localhost:8000 (PID: $HTTP_PID)"
echo ""
echo "🛑 Per arrestare i servizi:"
echo "   → kill $PROXY_PID $HTTP_PID"
echo "   → oppure premi CTRL+C in questa finestra"
echo ""

# Salva i PID per lo shutdown
echo "$PROXY_PID" > /tmp/turbogolden-proxy.pid
echo "$HTTP_PID" > /tmp/turbogolden-http.pid

# Funzione di cleanup
cleanup() {
    echo ""
    echo "🛑 Arresto servizi..."
    kill $PROXY_PID 2>/dev/null
    kill $HTTP_PID 2>/dev/null
    rm -f /tmp/turbogolden-proxy.pid /tmp/turbogolden-http.pid
    echo "✅ Servizi arrestati"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Tenta di aprire il browser
sleep 1
if command -v xdg-open &> /dev/null; then
    xdg-open "http://localhost:8000/turbogolden-terminal.html" 2>/dev/null &
elif command -v firefox &> /dev/null; then
    firefox "http://localhost:8000/turbogolden-terminal.html" 2>/dev/null &
elif command -v chromium &> /dev/null; then
    chromium "http://localhost:8000/turbogolden-terminal.html" 2>/dev/null &
fi

# Mantieni lo script in esecuzione
echo "⏳ Sistema in esecuzione... (premi CTRL+C per arrestare)"
echo ""

wait
