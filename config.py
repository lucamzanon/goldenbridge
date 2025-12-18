"""
Configurazione TurboGOLDEN Web Terminal
"""

import os

# Configurazione server TurboGOLDEN
TURBOGOLDEN_HOST = os.getenv('TURBOGOLDEN_HOST', '192.168.8.208')
TURBOGOLDEN_PORT = int(os.getenv('TURBOGOLDEN_PORT', '2323'))

# Configurazione Flask
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'turbogolden-secret-key-change-in-production')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '8080'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
