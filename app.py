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

# Aggiungi il path della libreria TurboGOLDEN
sys.path.insert(0, '/home/coder/goldenbridge/lib')

from turbogolden_client import TurboGoldenClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'turbogolden-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Dizionario per gestire le sessioni attive
active_sessions = {}

class TerminalSession:
    """Gestisce una sessione terminale TurboGOLDEN"""

    def __init__(self, session_id, username):
        self.session_id = session_id
        self.username = username
        self.client = None
        self.running = False
        self.read_thread = None

    def connect(self):
        """Connette al sistema TurboGOLDEN"""
        try:
            self.client = TurboGoldenClient(debug=True)
            self.client.connect(self.username)
            self.running = True

            # Leggi l'output iniziale
            initial_output = self.client.read_output()
            socketio.emit('output', {'data': initial_output}, room=self.session_id)

            # Avvia il thread di lettura continua
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

            return True
        except Exception as e:
            socketio.emit('output', {'data': f'\r\n[ERRORE] Connessione fallita: {str(e)}\r\n'}, room=self.session_id)
            return False

    def _read_loop(self):
        """Loop di lettura continua dall'output del terminale"""
        while self.running and self.client:
            try:
                # Leggi con timeout breve per non bloccare
                output = self.client.read_output(timeout=0.5)
                if output:
                    socketio.emit('output', {'data': output}, room=self.session_id)
            except Exception as e:
                if self.running:
                    socketio.emit('output', {'data': f'\r\n[ERRORE] Lettura: {str(e)}\r\n'}, room=self.session_id)
                break
            time.sleep(0.1)

    def send_input(self, data):
        """Invia input al terminale"""
        if self.client and self.running:
            try:
                self.client.tn.write(data.encode('latin-1'))
            except Exception as e:
                socketio.emit('output', {'data': f'\r\n[ERRORE] Invio: {str(e)}\r\n'}, room=self.session_id)

    def close(self):
        """Chiude la sessione"""
        self.running = False
        if self.client:
            try:
                self.client.close()
            except:
                pass
        self.client = None


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
    print(f"Server in ascolto su: http://localhost:8080")
    print(f"Connetti con il browser a: http://localhost")
    print("=" * 60)

    # Avvia il server
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
