# AntennaLab (Laptop Antenna Analysis Toolkit)

## What this project is
A modular RF + antenna analysis program for a laptop.
- Works with RTL-SDR now (relative measurements, spectrum, scans).
- Designed to support more instruments later (NanoVNA, TinySA, HackRF, etc.) using plugins.

## Core idea
Build a plugin-based toolkit:
- instruments/  (RTL-SDR now, VNA later)
- analysis/      (spectrum, noise floor, A/B comparison, scoring)
- report/        (CSV exports first; plots later)

## Important note
RTL-SDR cannot directly measure SWR/impedance/S11 like a VNA.
So the first phase focuses on:
- spectrum/waterfall
- band scanning
- noise floor profiling
- repeatable A/B antenna comparisons
- alerts and logging

Later (with NanoVNA):
- SWR curves, resonance finding, return loss, matching.

## Success criteria (Phase 1)
- A CLI tool that can do a repeatable band scan and export CSV.
- A/B antenna comparison report with a simple score.
- Noise floor profile by band/time.
- Alerts on selected frequencies.

## Long-term success (Phase 2+)
- Multi-instrument support with plugins.
- Easy reporting + plots + optional GUI.
