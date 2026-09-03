#!/usr/bin/env bash
# Headless Chromium für abstimmung_social.py in der Cowork-Sandbox einrichten.
# Die Sandbox hat kein Root und kein apt-get install; die fehlenden
# Systembibliotheken werden darum als .deb geladen und nach ~/libs entpackt.
# abstimmung_social.py setzt LD_LIBRARY_PATH selbst. Dauer: rund zwei Minuten.
# Idempotent: was da ist, wird übersprungen.
set -e
L="$HOME/libs"
python3 -c "import playwright" 2>/dev/null || pip install -q playwright --break-system-packages
ls -d "$HOME"/.cache/ms-playwright/chromium_headless_shell-* >/dev/null 2>&1 || python3 -m playwright install chromium
if [ ! -f "$L/usr/lib/x86_64-linux-gnu/libXdamage.so.1" ]; then
  mkdir -p "$L" /tmp/debs && cd /tmp/debs
  apt-get download libxdamage1 libxcomposite1 libxrandr2 libgbm1 libxkbcommon0 \
    libatk-bridge2.0-0 libatk1.0-0 libcups2 libnss3 libnspr4 libasound2 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 libdrm2 libxfixes3 libxext6 libx11-xcb1 libxcb1 \
    libwayland-client0 libwayland-server0 libdbus-1-3 libexpat1 libxshmfence1 libgl1 >/dev/null
  for f in *.deb; do dpkg-deb -x "$f" "$L" 2>/dev/null || true; done
fi
echo "Browser bereit."
