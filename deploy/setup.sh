#!/usr/bin/env bash
# Habib OS — one-shot Hetzner setup script
#
# Run this AS ROOT on a fresh Ubuntu 24.04 VPS:
#   sudo bash deploy/setup.sh
#
# Prerequisites before running:
#   1. Code is already in /home/habib/anabtawi-os/  (via rsync — see below)
#   2. .env is already in /home/habib/anabtawi-os/.env
#
# Rsync command to run from your Mac (before this script):
#   rsync -avz --exclude '.git' --exclude 'habib-os' --exclude '__pycache__' \
#     --exclude '*.pyc' --exclude 'venv' \
#     /Users/mareekhalila/Documents/anabtawi-os/ \
#     habib@<HETZNER_IP>:/home/habib/anabtawi-os/

set -euo pipefail

APP_DIR="/home/habib/anabtawi-os"
APP_USER="habib"
LOG_DIR="/var/log/habib"
VENV="$APP_DIR/venv"
SYSTEMD_DIR="/etc/systemd/system"

echo "══════════════════════════════════════════"
echo " Habib OS — Hetzner Setup"
echo "══════════════════════════════════════════"

# ─── 1. System packages ───────────────────────────────────────────────────────
echo ""
echo "[1/7] Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3.12 python3.12-venv python3-pip git curl

# ─── 2. Create habib user if missing ─────────────────────────────────────────
echo ""
echo "[2/7] Ensuring habib user exists..."
if ! id "$APP_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" "$APP_USER"
    echo "  Created user: $APP_USER"
else
    echo "  User $APP_USER already exists — skipping"
fi

# ─── 3. Verify code + .env are in place ──────────────────────────────────────
echo ""
echo "[3/7] Checking code and .env..."
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    echo "  ❌ $APP_DIR/requirements.txt not found."
    echo "     Run the rsync command from your Mac first:"
    echo ""
    echo "     rsync -avz --exclude '.git' --exclude 'habib-os' \\"
    echo "       --exclude '__pycache__' --exclude '*.pyc' --exclude 'venv' \\"
    echo "       /Users/mareekhalila/Documents/anabtawi-os/ \\"
    echo "       habib@<HETZNER_IP>:/home/habib/anabtawi-os/"
    exit 1
fi

if [ ! -f "$APP_DIR/.env" ]; then
    echo "  ❌ $APP_DIR/.env not found."
    echo "     Copy your .env from Mac:"
    echo "     scp /Users/mareekhalila/Documents/anabtawi-os/.env habib@<HETZNER_IP>:$APP_DIR/.env"
    exit 1
fi
echo "  ✅ Code and .env present"

# ─── 4. Python venv + dependencies ───────────────────────────────────────────
echo ""
echo "[4/7] Setting up Python venv..."
if [ ! -d "$VENV" ]; then
    sudo -u "$APP_USER" python3.12 -m venv "$VENV"
    echo "  Created venv at $VENV"
fi

echo "  Installing requirements (this takes ~2 min)..."
sudo -u "$APP_USER" "$VENV/bin/pip" install --quiet --upgrade pip
sudo -u "$APP_USER" "$VENV/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
echo "  ✅ Dependencies installed"

# ─── 5. Log directory ────────────────────────────────────────────────────────
echo ""
echo "[5/7] Creating log directory $LOG_DIR..."
mkdir -p "$LOG_DIR"
chown "$APP_USER:$APP_USER" "$LOG_DIR"
echo "  ✅ $LOG_DIR ready"

# Fix ownership of app dir
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# ─── 6. Systemd services ─────────────────────────────────────────────────────
echo ""
echo "[6/7] Installing systemd services..."

cp "$APP_DIR/deploy/habib-tgbot.service"    "$SYSTEMD_DIR/"
cp "$APP_DIR/deploy/habib-executor.service" "$SYSTEMD_DIR/"

systemctl daemon-reload

systemctl enable habib-tgbot
systemctl enable habib-executor

systemctl restart habib-tgbot
systemctl restart habib-executor

echo "  ✅ habib-tgbot.service  — $(systemctl is-active habib-tgbot)"
echo "  ✅ habib-executor.service — $(systemctl is-active habib-executor)"

# ─── 7. Crontab ──────────────────────────────────────────────────────────────
echo ""
echo "[7/7] Installing crontab for $APP_USER..."
crontab -u "$APP_USER" "$APP_DIR/deploy/crontab"
echo "  ✅ Crontab installed"

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
echo " Setup complete!"
echo "══════════════════════════════════════════"
echo ""
echo "Check service logs:"
echo "  journalctl -u habib-tgbot -f"
echo "  journalctl -u habib-executor -f"
echo ""
echo "Check crontab:"
echo "  crontab -u habib -l"
echo ""
echo "Quick smoke test (as habib user):"
echo "  sudo -u habib bash -c 'cd $APP_DIR && $VENV/bin/python3 -c \"from core.supabase_client import get_supabase; s=get_supabase(); print(s.table(\\\"products\\\").select(\\\"id\\\").limit(1).execute().data)\"'"
