# Architecture

## Design principle
Plugin-first, so we can add more hardware without rewriting the app.

## Modules
- src/antennalab/instruments/
  - rtl_sdr: scans, IQ capture, waterfall
  - nanovna: later
  - tinysa: later
- src/antennalab/analysis/
  - spectrum: FFT to power spectrum
  - noise_floor: baseline estimation
  - compare: A/B scoring
  - alerts: thresholds + triggers
- src/antennalab/report/
  - export_csv
  - run_report_json
  - later: plots + HTML

## Plugin interface (concept)
Each plugin provides:
- info(): name, kind, description
- healthcheck(): tells if config/hardware looks OK

## Data model (Phase 1)
ScanResult:
- timestamp
- start_hz, stop_hz
- bin_hz
- bins[]:
  - freq_hz
  - avg_db (relative)
  - max_db (relative)
Optional:
- location tag
- antenna profile tag

## Why this works
RTL-SDR gives relative power levels. Repeatability comes from:
- same settings (gain/sample_rate/binning)
- calibration baseline (later)
- consistent measurement process

## Future compatibility
NanoVNA adds true S11/SWR data under same report framework.
