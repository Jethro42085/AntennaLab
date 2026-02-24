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

## RTL-SDR (Real Mode)
Requires RTL-SDR drivers plus Python deps:
- numpy
- pyrtlsdr

Example real scan:
```bash
antennalab scan --mode real
```

Simulated scan (no hardware):
```bash
antennalab scan --mode sim --seed 42
```
