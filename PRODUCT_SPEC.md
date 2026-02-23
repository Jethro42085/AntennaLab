# Product Spec: AntennaLab

## Users
- You, testing antennas and RF environments with a laptop.
- Future: other hobbyists/hams.

## Use cases (RTL-SDR)
1) Scan a band and save a CSV
2) Compare Antenna A vs Antenna B over the same scan profile
3) Track noise floor over time at a location
4) Waterfall capture for later review
5) Alerts on a set of frequencies
6) Bookmark frequencies + notes
7) Create a quick “report pack” of results for a test session

## Use cases (later tools)
- NanoVNA: SWR/return loss/resonance
- TinySA: spectrum + convenience scanning
- HackRF: broader TX/RX experiments (future; safe/legal)
- Rigs: CAT control, spot checks

## Non-goals (Phase 1)
- Claiming true SWR/impedance using only RTL-SDR
- RF compliance claims

## Primary outputs
- CSV (always)
- JSON run reports (optional)
- Later: images/plots and HTML report

## UX
- CLI first
- Optional GUI later
