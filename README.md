# AntennaLab

Laptop-based antenna/RF toolkit:
- RTL-SDR supported first (relative scans, spectrum, comparisons).
- Plugin-based design to add NanoVNA/TinySA/HackRF later.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

antennalab info
antennalab health
