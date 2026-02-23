# Tasks (Human-in-the-loop friendly)

## Setup tasks
- [ ] Create venv
- [ ] Install dependencies
- [ ] Run `antennalab info`
- [ ] Run `antennalab health`

## Phase 1 tasks (RTL-SDR)
### 1) Band Scanner
- [ ] Implement scan settings: start/stop/bin size
- [ ] Collect data: avg/max per bin
- [ ] Export CSV
- Human test:
  - Run the scan twice with same settings
  - Confirm roughly similar results (within reason)

### 2) Noise Floor Profiler
- [ ] Estimate baseline noise level per bin
- [ ] Export CSV
- Human test:
  - Compare night vs day scan
  - Confirm noise floor changes show up

### 3) A/B Comparator
- [ ] Accept scan A CSV + scan B CSV
- [ ] Output a difference report + score
- Human test:
  - Use two antennas, same place, same settings
  - Confirm score aligns with what you observe

### 4) Alerts
- [ ] Configurable freqs + threshold
- [ ] Log hits to a file
- Human test:
  - Set a known active freq and verify it triggers

## QA rules
- Every feature must export a CSV
- Every run can optionally export JSON “run report”
- Keep steps repeatable and documented
