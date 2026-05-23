#!/bin/bash
# Launch the Network Scanner GUI app properly on macOS
cd "$(dirname "$0")/../.."
export PYTHONPATH="../src"

# Kill any existing instance
pkill -f "netadmin_gui" 2>/dev/null

# Launch as a proper macOS app process
python3 -m src.netadmin_gui
