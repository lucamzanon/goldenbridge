#!/bin/bash
# Script per avviare il server TurboGOLDEN Web Terminal

cd /home/coder/turbogolden-web

echo "=========================================="
echo "Avvio TurboGOLDEN Web Terminal"
echo "=========================================="
echo ""
echo "Server Flask: http://localhost:8080"
echo "Server nginx:  http://localhost"
echo ""
echo "Premi Ctrl+C per terminare"
echo "=========================================="
echo ""

# Avvia il server Flask
python3 app.py
