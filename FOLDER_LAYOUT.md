# Folder Layout (Target)

AntennaLab/
  README.md
  PROJECT_OVERVIEW.md
  PRODUCT_SPEC.md
  ARCHITECTURE.md
  FEATURE_ROADMAP.md
  FOLDER_LAYOUT.md
  TASKS.md

  config/
    antennalab.yaml
    profiles/
      antennas.yaml
      locations.yaml

  src/
    antennalab/
      cli.py
      config.py

      core/
        plugins.py
        registry.py

      instruments/
        rtlsdr.py
        nanovna.py        # placeholder
        tinysa.py         # placeholder

      analysis/
        spectrum.py
        scan.py
        noise_floor.py
        compare.py
        alerts.py

      report/
        export_csv.py
        run_report.py

  data/
    scans/
    waterfalls/
    reports/
