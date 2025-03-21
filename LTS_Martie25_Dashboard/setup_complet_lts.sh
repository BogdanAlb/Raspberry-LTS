#!/bin/bash

echo "🔧 Instalare pachete de bază..."
sudo apt update
sudo apt install -y python3-venv python3-full python3-pip i2c-tools python3-smbus git

USERNAME=$(whoami)
PROJECT_DIR="/home/$USERNAME/LTS_Martie25_Dashboard"
PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
SCRIPT="$PROJECT_DIR/hx711_full.py"
SERVICE_FILE="/etc/systemd/system/hx711.service"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "❌ Directorul $PROJECT_DIR nu există!"
  exit 1
fi

if [ ! -f "$SCRIPT" ]; then
  echo "❌ Fișierul $SCRIPT nu există!"
  exit 1
fi

cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️ Creare serviciu systemd..."
sudo cp hx711.service $SERVICE_FILE

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable hx711.service
sudo systemctl restart hx711.service

echo "✅ Setup complet. Verifică cu:"
echo "   sudo systemctl status hx711.service"
