#!/usr/bin/env python3
"""
WebSocket Telnet Proxy per TurboGOLDEN
Proxy WebSocket che si connette al server telnet TurboGOLDEN

Uso:
    python3 telnet-websocket-proxy.py

Poi apri turbogolden-terminal.html nel browser
"""

import asyncio
import websockets
import telnetlib
import socket
import threading
import json
import time
from typing import Optional

# Configurazione
WS_HOST = "0.0.0.0"
WS_PORT = 8080

class TelnetSession:
    """Gestisce una sessione telnet per un client WebSocket"""

    def __init__(self, websocket):
        self.websocket = websocket
        self.tn: Optional[telnetlib.Telnet] = None
        self.running = False
        self.read_thread = None

    async def connect(self, host: str, port: int, username: str, password: str = ""):
        """Connette al server telnet TurboGOLDEN"""
        try:
            print(f"[INFO] Connessione a {host}:{port} per utente {username}")

            # Crea connessione telnet
            self.tn = telnetlib.Telnet(host, port, timeout=15)

            # CRITICO: Applica TCP_NODELAY
            self.tn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"[INFO] TCP_NODELAY applicato")

            # Login Linux
            self.tn.read_until(b"login:", timeout=5)
            self.tn.write(b"cdi\n")

            # Attendi schermata autenticazione applicativa
            self.tn.read_until(b"Nome dell'utente:", timeout=15)
            self.tn.write(username.encode('latin-1') + b"\n")

            # Password
            self.tn.read_until(b"Chiave di accesso:", timeout=5)
            self.tn.write(password.encode('latin-1') + b"\n")

            # Gestione avvisi
            time.sleep(5)
            self.tn.write(b"\n")  # Avvisi
            time.sleep(2)
            self.tn.write(b" ")   # Errore frame
            time.sleep(2)
            self.tn.write(b"\n")  # Menu
            time.sleep(2)

            # Avvia thread di lettura
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

            # Notifica connessione riuscita
            await self.websocket.send(json.dumps({
                'type': 'connected'
            }))

            print(f"[INFO] Connessione completata - Menu principale raggiunto")
            return True

        except Exception as e:
            print(f"[ERRORE] Connessione fallita: {e}")
            await self.websocket.send(json.dumps({
                'type': 'error',
                'message': f'Connessione fallita: {str(e)}'
            }))
            return False

    def _read_loop(self):
        """Loop di lettura continua dall'output telnet"""
        while self.running and self.tn:
            try:
                # Leggi output disponibile
                data = self.tn.read_very_eager()
                if data:
                    # Decodifica in latin-1
                    text = data.decode('latin-1', errors='replace')

                    # Invia al client WebSocket
                    asyncio.run(self.websocket.send(json.dumps({
                        'type': 'data',
                        'data': text
                    })))

            except Exception as e:
                if self.running:
                    print(f"[ERRORE] Lettura: {e}")
                    try:
                        asyncio.run(self.websocket.send(json.dumps({
                            'type': 'error',
                            'message': f'Errore lettura: {str(e)}'
                        })))
                    except:
                        pass
                break

            time.sleep(0.05)  # 50ms

    def send_input(self, data: str):
        """Invia input al terminale telnet"""
        if self.tn and self.running:
            try:
                self.tn.write(data.encode('latin-1'))
            except Exception as e:
                print(f"[ERRORE] Invio input: {e}")

    def close(self):
        """Chiude la sessione telnet"""
        print("[INFO] Chiusura sessione telnet")
        self.running = False
        if self.tn:
            try:
                self.tn.close()
            except:
                pass
        self.tn = None


async def handle_websocket(websocket, path):
    """Gestisce una connessione WebSocket client"""
    client_id = id(websocket)
    print(f"[WebSocket] Nuovo client connesso: {client_id}")

    session = None

    try:
        async for message in websocket:
            try:
                msg = json.loads(message)
                msg_type = msg.get('type')

                if msg_type == 'connect':
                    # Richiesta di connessione al server telnet
                    host = msg.get('host', '192.168.0.8')
                    port = msg.get('port', 23)
                    username = msg.get('username', 'zanon')
                    password = msg.get('password', '')

                    # Chiudi eventuale sessione precedente
                    if session:
                        session.close()

                    # Crea nuova sessione
                    session = TelnetSession(websocket)
                    await session.connect(host, port, username, password)

                elif msg_type == 'input':
                    # Input dal client
                    if session:
                        data = msg.get('data', '')
                        session.send_input(data)
                    else:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Sessione non attiva'
                        }))

                elif msg_type == 'disconnect':
                    # Richiesta di disconnessione
                    if session:
                        session.close()
                        session = None
                    await websocket.send(json.dumps({
                        'type': 'closed'
                    }))

            except json.JSONDecodeError:
                print(f"[ERRORE] Messaggio JSON non valido: {message}")
            except Exception as e:
                print(f"[ERRORE] Gestione messaggio: {e}")

    except websockets.exceptions.ConnectionClosed:
        print(f"[WebSocket] Client disconnesso: {client_id}")
    finally:
        # Cleanup
        if session:
            session.close()


async def main():
    """Avvia il server WebSocket"""
    print("=" * 70)
    print("WebSocket Telnet Proxy per TurboGOLDEN")
    print("=" * 70)
    print(f"Server WebSocket in ascolto su: ws://{WS_HOST}:{WS_PORT}")
    print(f"")
    print(f"Apri il file turbogolden-terminal.html nel browser")
    print(f"Il proxy si connetterà a TurboGOLDEN quando richiesto")
    print("=" * 70)

    async with websockets.serve(handle_websocket, WS_HOST, WS_PORT):
        await asyncio.Future()  # Run forever


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Server arrestato")
