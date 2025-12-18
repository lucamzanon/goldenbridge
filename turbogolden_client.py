#!/usr/bin/env python3
"""
TurboGOLDEN Client Library
Libreria Python per interfacciarsi con il sistema TurboGOLDEN

Autore: Analisi Sistema TurboGOLDEN
Versione: 1.0
Data: 18 Dicembre 2025
"""

import telnetlib
import socket
import time
from typing import Optional


class TurboGoldenError(Exception):
    """Eccezione base per errori TurboGOLDEN"""
    pass


class TurboGoldenConnectionError(TurboGoldenError):
    """Errore di connessione"""
    pass


class TurboGoldenAuthError(TurboGoldenError):
    """Errore di autenticazione"""
    pass


class TurboGoldenClient:
    """
    Client per interagire con il sistema TurboGOLDEN

    Esempio:
        >>> client = TurboGoldenClient()
        >>> client.connect("myuser")
        >>> client.send_command("menu")
        >>> output = client.read_output()
        >>> client.close()

    Oppure con context manager:
        >>> with TurboGoldenClient() as client:
        ...     client.connect("myuser")
        ...     output = client.read_output()
    """

    # Configurazione predefinita
    DEFAULT_HOST = "192.168.0.8"
    DEFAULT_PORT = 23
    LINUX_USER = "cdi"

    # Timeout (in secondi)
    TIMEOUT_LOGIN = 5
    TIMEOUT_APP_START = 15
    TIMEOUT_PROMPT = 5
    TIMEOUT_READ = 2

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, debug: bool = False):
        """
        Inizializza client

        Args:
            host: Indirizzo IP/hostname del server
            port: Porta telnet (default: 23)
            debug: Abilita output di debug
        """
        self.host = host
        self.port = port
        self.debug = debug
        self.tn: Optional[telnetlib.Telnet] = None
        self._connected = False

    def _log(self, message: str):
        """Stampa messaggio di debug"""
        if self.debug:
            print(f"[TurboGOLDEN] {message}")

    def connect(self, username: str, password: str = "") -> bool:
        """
        Connette al sistema TurboGOLDEN e esegue autenticazione completa

        Args:
            username: Nome utente applicativo TurboGOLDEN
            password: Password applicativa (opzionale, default: vuota)

        Returns:
            True se connessione riuscita

        Raises:
            TurboGoldenConnectionError: Errore di connessione
            TurboGoldenAuthError: Errore di autenticazione
        """
        try:
            self._log(f"Connessione a {self.host}:{self.port}...")

            # Crea connessione telnet
            self.tn = telnetlib.Telnet(self.host, self.port, timeout=self.TIMEOUT_APP_START)

            # CRITICO: Applica TCP_NODELAY per disabilitare algoritmo di Nagle
            self.tn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._log("TCP_NODELAY applicato")

            # === FASE 1: Login Linux ===
            self._log("Attesa prompt login Linux...")
            self.tn.read_until(b"login:", timeout=self.TIMEOUT_LOGIN)

            self._log(f"Invio username Linux: {self.LINUX_USER}")
            self.tn.write(self.LINUX_USER.encode('latin-1') + b"\n")

            # === FASE 2: Avvio Applicazione ===
            self._log("Attesa avvio applicazione TurboGOLDEN (8-15s)...")
            self.tn.read_until(b"Nome dell'utente:", timeout=self.TIMEOUT_APP_START)

            # === FASE 3: Autenticazione Applicativa ===
            self._log(f"Invio username applicativo: {username}")
            self.tn.write(username.encode('latin-1') + b"\n")

            self._log("Attesa prompt password...")
            self.tn.read_until(b"Chiave di accesso:", timeout=self.TIMEOUT_PROMPT)

            self._log("Invio password (blank)" if not password else f"Invio password")
            self.tn.write(password.encode('latin-1') + b"\n")

            # === FASE 4: Gestione Avvisi ===
            self._log("Gestione avvisi sistema...")
            self._skip_system_warnings()

            self._connected = True
            self._log("Connessione e autenticazione completate - Menu principale raggiunto")
            return True

        except EOFError as e:
            raise TurboGoldenConnectionError(f"Connessione chiusa dal server: {e}")
        except socket.timeout as e:
            raise TurboGoldenConnectionError(f"Timeout connessione: {e}")
        except Exception as e:
            raise TurboGoldenError(f"Errore generico: {e}")

    def _skip_system_warnings(self):
        """
        Gestisce automaticamente gli avvisi di sistema post-login
        - Avviso adeguamenti fine anno
        - Controllo copie programmi
        - Errore frame (opzionale)
        """
        # Attendi che il sistema mostri gli avvisi
        time.sleep(5)

        # INVIO per avviso adeguamenti/backup
        self._log("Invio INVIO per bypass avvisi...")
        self.tn.write(b"\n")
        time.sleep(2)

        # SPAZIO per eventuale errore frame
        self._log("Invio SPAZIO per bypass errore frame...")
        self.tn.write(b" ")
        time.sleep(2)

        # INVIO finale per accedere al menu
        self._log("Invio INVIO finale per menu...")
        self.tn.write(b"\n")
        time.sleep(3)

    def send_command(self, command: str):
        """
        Invia comando al sistema

        Args:
            command: Comando da inviare (senza \\n finale)
        """
        if not self._connected:
            raise TurboGoldenError("Non connesso - chiamare connect() prima")

        self._log(f"Invio comando: {command}")
        self.tn.write(command.encode('latin-1') + b"\n")

    def send_keys(self, keys: str):
        """
        Invia sequenza di tasti (senza INVIO automatico)

        Args:
            keys: Tasti da inviare
        """
        if not self._connected:
            raise TurboGoldenError("Non connesso - chiamare connect() prima")

        self._log(f"Invio tasti: {keys}")
        self.tn.write(keys.encode('latin-1'))

    def send_enter(self):
        """Invia INVIO"""
        self.send_keys("\n")

    def send_space(self):
        """Invia SPAZIO"""
        self.send_keys(" ")

    def read_output(self, timeout: float = None) -> str:
        """
        Legge output disponibile dal terminale

        Args:
            timeout: Secondi di attesa prima di leggere (default: TIMEOUT_READ)

        Returns:
            Output ricevuto come stringa
        """
        if not self._connected:
            raise TurboGoldenError("Non connesso - chiamare connect() prima")

        if timeout is None:
            timeout = self.TIMEOUT_READ

        self._log(f"Lettura output (attesa {timeout}s)...")
        time.sleep(timeout)

        data = self.tn.read_very_eager()
        output = data.decode('latin-1', errors='replace')

        self._log(f"Ricevuti {len(data)} bytes")
        return output

    def read_until(self, expected: str, timeout: float = None) -> str:
        """
        Legge output fino a trovare stringa attesa

        Args:
            expected: Stringa da attendere
            timeout: Timeout in secondi

        Returns:
            Output ricevuto fino alla stringa attesa
        """
        if not self._connected:
            raise TurboGoldenError("Non connesso - chiamare connect() prima")

        if timeout is None:
            timeout = self.TIMEOUT_PROMPT

        self._log(f"Lettura fino a: {expected}")
        data = self.tn.read_until(expected.encode('latin-1'), timeout=timeout)
        return data.decode('latin-1', errors='replace')

    def keepalive(self):
        """Invia INVIO per mantenere sessione attiva"""
        self._log("Keepalive...")
        self.tn.write(b"\n")

    def close(self):
        """Chiude connessione"""
        if self.tn:
            self._log("Chiusura connessione...")
            try:
                self.tn.close()
            except:
                pass
            self._connected = False

    def is_connected(self) -> bool:
        """Verifica se connesso"""
        return self._connected

    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class TurboGoldenSession:
    """
    Context manager per sessioni TurboGOLDEN con autenticazione automatica

    Esempio:
        >>> with TurboGoldenSession("myuser") as client:
        ...     client.send_command("menu")
        ...     output = client.read_output()
        ...     print(output)
    """

    def __init__(self, username: str, password: str = "", host: str = TurboGoldenClient.DEFAULT_HOST,
                 port: int = TurboGoldenClient.DEFAULT_PORT, debug: bool = False):
        """
        Inizializza sessione

        Args:
            username: Nome utente applicativo
            password: Password applicativa (opzionale)
            host: Host TurboGOLDEN
            port: Porta telnet
            debug: Abilita debug
        """
        self.username = username
        self.password = password
        self.client = TurboGoldenClient(host, port, debug)

    def __enter__(self) -> TurboGoldenClient:
        """Apre connessione e autentica"""
        self.client.connect(self.username, self.password)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Chiude connessione"""
        self.client.close()


# === Esempi di utilizzo ===

def example_basic():
    """Esempio base: connessione e lettura menu"""
    print("=== Esempio 1: Connessione Base ===\n")

    client = TurboGoldenClient(debug=True)

    try:
        # Connessione
        client.connect("username")

        # Lettura output menu
        output = client.read_output()
        print("\n--- OUTPUT ---")
        print(output)

    finally:
        client.close()


def example_context_manager():
    """Esempio con context manager"""
    print("\n=== Esempio 2: Context Manager ===\n")

    with TurboGoldenSession("username", debug=True) as client:
        # Invia comando
        client.send_command("help")

        # Leggi risposta
        output = client.read_output()
        print("\n--- OUTPUT ---")
        print(output)


def example_interactive():
    """Esempio interattivo"""
    print("\n=== Esempio 3: Interazione ===\n")

    with TurboGoldenSession("username", debug=True) as client:
        # Invia sequenza di comandi
        client.send_command("menu1")
        time.sleep(1)

        client.send_enter()
        time.sleep(1)

        client.send_command("633")
        time.sleep(2)

        # Leggi output finale
        output = client.read_output()
        print("\n--- OUTPUT ---")
        print(output[-500:])  # Ultimi 500 caratteri


def example_keepalive():
    """Esempio con keepalive"""
    print("\n=== Esempio 4: Keepalive ===\n")

    with TurboGoldenSession("username", debug=True) as client:
        # Sessione lunga con keepalive
        for i in range(5):
            print(f"\nIterazione {i+1}")

            # Operazione
            client.send_command("status")
            output = client.read_output(timeout=1)

            # Keepalive ogni 30 secondi
            if i % 2 == 0:
                client.keepalive()

            time.sleep(5)


if __name__ == "__main__":
    # Decommentare per testare
    # example_basic()
    # example_context_manager()
    # example_interactive()
    # example_keepalive()

    print("TurboGOLDEN Client Library caricata")
    print("Utilizzare TurboGoldenClient o TurboGoldenSession")
    print("\nEsempi disponibili:")
    print("  - example_basic()")
    print("  - example_context_manager()")
    print("  - example_interactive()")
    print("  - example_keepalive()")
