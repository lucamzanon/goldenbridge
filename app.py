#!/usr/bin/env python3
"""
TurboGOLDEN Web Terminal Server
Server Flask con WebSocket per esporre TurboGOLDEN tramite xterm.js
"""

import sys
import os
import asyncio
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading
import time

# Importa la configurazione
from config import TURBOGOLDEN_HOST, TURBOGOLDEN_PORT, FLASK_SECRET_KEY, FLASK_HOST, FLASK_PORT, FLASK_DEBUG

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Dizionario per gestire le sessioni attive
active_sessions = {}

class TerminalSession:
    """Gestisce una sessione terminale TurboGOLDEN"""

    def __init__(self, session_id, username):
        self.session_id = session_id
        self.username = username
        self.tn = None  # Connessione telnet diretta
        self.running = False
        self.read_thread = None

    def connect(self):
        """Connette direttamente al telnet senza autenticazione"""
        try:
            import telnetlib
            import socket

            # Connessione telnet diretta
            self.tn = telnetlib.Telnet(TURBOGOLDEN_HOST, TURBOGOLDEN_PORT, timeout=15)

            # Abilita TCP_NODELAY
            self.tn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            self.running = True

            print(f"[INFO] Connesso a {TURBOGOLDEN_HOST}:{TURBOGOLDEN_PORT}")

            # Leggi output iniziale (prompt login)
            time.sleep(1)
            initial_output = self.tn.read_very_eager().decode('latin-1', errors='replace')
            print(f"[DEBUG] Output iniziale ({len(initial_output)} bytes)")
            if initial_output:
                socketio.emit('output', {'data': initial_output}, room=self.session_id)

            # Avvia il thread di lettura continua
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

            return True
        except Exception as e:
            print(f"[ERRORE] Connessione fallita: {e}")
            socketio.emit('output', {'data': f'\r\n[ERRORE] Connessione fallita: {str(e)}\r\n'}, room=self.session_id)
            return False

    def _read_loop(self):
        """Loop di lettura continua dall'output del terminale"""
        while self.running and self.tn:
            try:
                # Leggi output disponibile
                output = self.tn.read_very_eager().decode('latin-1', errors='replace')
                if output:
                    print(f"[DEBUG] Output loop ({len(output)} bytes)")
                    socketio.emit('output', {'data': output}, room=self.session_id)
            except Exception as e:
                if self.running:
                    print(f"[ERRORE] Lettura: {e}")
                    socketio.emit('output', {'data': f'\r\n[ERRORE] Lettura: {str(e)}\r\n'}, room=self.session_id)
                break
            time.sleep(0.1)

    def send_input(self, data):
        """Invia input al terminale"""
        if self.tn and self.running:
            try:
                print(f"[DEBUG] Input ricevuto ({len(data)} bytes): {repr(data)}")
                self.tn.write(data.encode('latin-1'))
            except Exception as e:
                socketio.emit('output', {'data': f'\r\n[ERRORE] Invio: {str(e)}\r\n'}, room=self.session_id)

    def close(self):
        """Chiude la sessione"""
        self.running = False
        if self.tn:
            try:
                self.tn.close()
            except:
                pass
        self.tn = None


@app.route('/')
def index():
    """Pagina principale con il terminale"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Gestisce la connessione WebSocket"""
    session_id = request.sid
    print(f"[WebSocket] Client connesso: {session_id}")
    emit('connected', {'session_id': session_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Gestisce la disconnessione WebSocket"""
    session_id = request.sid
    print(f"[WebSocket] Client disconnesso: {session_id}")

    # Chiudi la sessione se esiste
    if session_id in active_sessions:
        active_sessions[session_id].close()
        del active_sessions[session_id]


@socketio.on('start_session')
def handle_start_session(data):
    """Avvia una nuova sessione TurboGOLDEN"""
    session_id = request.sid
    username = data.get('username', 'username')

    print(f"[WebSocket] Avvio sessione per utente: {username}")

    # Chiudi eventuali sessioni precedenti
    if session_id in active_sessions:
        active_sessions[session_id].close()

    # Crea e avvia la nuova sessione
    session = TerminalSession(session_id, username)
    active_sessions[session_id] = session

    if session.connect():
        emit('session_started', {'status': 'ok'})
    else:
        emit('session_started', {'status': 'error'})
        if session_id in active_sessions:
            del active_sessions[session_id]


@socketio.on('input')
def handle_input(data):
    """Gestisce l'input dal terminale web"""
    session_id = request.sid
    input_data = data.get('data', '')

    if session_id in active_sessions:
        active_sessions[session_id].send_input(input_data)
    else:
        emit('output', {'data': '\r\n[ERRORE] Sessione non attiva\r\n'})


@socketio.on('resize')
def handle_resize(data):
    """Gestisce il resize del terminale (opzionale)"""
    # Il sistema TurboGOLDEN usa dimensioni fisse 80x24
    # Questa funzione è qui per compatibilità futura
    pass


if __name__ == '__main__':
    print("=" * 60)
    print("TurboGOLDEN Web Terminal Server")
    print("=" * 60)
    print(f"Server TurboGOLDEN: {TURBOGOLDEN_HOST}:{TURBOGOLDEN_PORT}")
    print(f"Server in ascolto su: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"Connetti con il browser a: http://localhost")
    print("=" * 60)

    # Avvia il server
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, allow_unsafe_werkzeug=True)
