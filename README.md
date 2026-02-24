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

Real scan tuning:
- `--sweeps N` averages N full sweeps across the band (default 3)
- `--dwell-ms MS` waits between center steps (default 0)

Baseline subtraction (simple calibration):
1) Capture a baseline scan in a quiet condition:
```bash
antennalab scan --mode real --out-csv data/scans/baseline.csv
```
2) Run a new scan with baseline subtraction:
```bash
antennalab scan --mode real --baseline-csv data/scans/baseline.csv
```
This subtracts baseline avg power per bin from avg/max.

Apply baseline to an existing scan file:
```bash
antennalab baseline-apply --scan-csv data/scans/scan.csv --baseline-csv data/scans/baseline.csv --out-csv data/scans/scan_adjusted.csv
```

Baseline capture shortcut:
```bash
antennalab baseline-capture --mode real
```

Sweep stability stats (min/mean/max per sweep average):
```bash
antennalab scan --mode real --sweep-stats-csv data/reports/sweep_stats.csv
```

Plot a scan CSV to PNG:
```bash
antennalab plot-scan --in-csv data/scans/scan.csv --out-png data/reports/scan.png
```
