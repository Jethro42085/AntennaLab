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

Waterfall capture:
```bash
antennalab waterfall --mode sim --slices 10 --interval-ms 100
```
Output CSV columns: `timestamp,slice_index,freq_hz,avg_db,max_db`.

Plot waterfall CSV:
```bash
antennalab plot-waterfall --in-csv data/waterfalls/waterfall.csv --out-png data/reports/waterfall.png
```

Customize waterfall colormap:
```bash
antennalab plot-waterfall --in-csv data/waterfalls/waterfall.csv --out-png data/reports/waterfall.png --cmap plasma --vmin -80 --vmax -20
```

Set default waterfall colors in config:
```yaml
waterfall_plot:
  cmap: viridis
  vmin: -80
  vmax: -20
```
Command-line flags override config.

Recommended colormaps:
- viridis (default)
- plasma
- magma
- inferno
- cividis

Bookmarks:
```bash
antennalab bookmarks add --freq-hz 100000000 --label "FM 100" --notes "local"
antennalab bookmarks list
antennalab bookmarks remove --freq-hz 100000000
```

Bookmark import/export and scan matching:
```bash
antennalab bookmarks export --out-json data/reports/bookmarks.json
antennalab bookmarks import --in-json data/reports/bookmarks.json
antennalab bookmarks match --scan-csv data/scans/scan.csv
```

Waterfall HTML viewer (no Python deps):
```bash
antennalab waterfall-html --in-csv data/waterfalls/waterfall.csv --out-html data/reports/waterfall.html --palette heat
```

Report pack:
```bash
antennalab report-pack --session my_session
```

Scan reports now include matched bookmarks if the bookmarks file exists.
You can override with:
```bash
antennalab scan --bookmarks-file config/bookmarks.csv
```

Report pack summary includes bookmark matches (if present in scan_report.json).

Report packs now include a `README.txt` with a quick file list and tip.

Monitor (repeated scans):
```bash
antennalab monitor --mode sim --interval-sec 5 --iterations 3 --session quick
```
Outputs go to `data/reports/monitor_<session>/`.

Monitor with report pack:
```bash
antennalab monitor --mode sim --interval-sec 5 --iterations 3 --session quick --report-pack
```

Baseline profiles (tags):
```bash
antennalab baseline-capture --mode sim --out-csv data/scans/baseline_night.csv
antennalab baseline-tag --tag night --csv-path data/scans/baseline_night.csv --notes "quiet"
antennalab scan --mode sim --baseline-tag night
```
