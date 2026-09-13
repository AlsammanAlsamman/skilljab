#!/usr/bin/env bash
# Re-render assets/flowchart/skilljab-loop.html -> skilljab-loop.png at 2x (needs Google Chrome + Pillow).
set -euo pipefail
cd "$(dirname "$0")/.."
google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1560,900 --virtual-time-budget=6000 --screenshot=assets/flowchart/skilljab-loop.png \
  "file://$PWD/assets/flowchart/skilljab-loop.html" >/dev/null 2>&1
python3 -c "from PIL import Image; im=Image.open('assets/flowchart/skilljab-loop.png').crop((0,0,3120,1400)); im.save('assets/flowchart/skilljab-loop.png', optimize=True); print(im.size)"
