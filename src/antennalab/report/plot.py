from __future__ import annotations

from pathlib import Path

from antennalab.report.export_csv import scan_from_csv


def plot_scan_csv(input_csv: str | Path, output_png: str | Path) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise SystemExit("plot-scan requires matplotlib. Install with: pip install matplotlib") from exc

    scan = scan_from_csv(input_csv)
    freqs = [b.freq_hz / 1e6 for b in scan.bins]
    avg_vals = [b.avg_db for b in scan.bins]
    max_vals = [b.max_db for b in scan.bins]

    output_path = Path(output_png)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 4))
    plt.plot(freqs, avg_vals, label="avg_db", linewidth=1.0)
    plt.plot(freqs, max_vals, label="max_db", linewidth=0.8, alpha=0.7)
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("dB (relative)")
    plt.title("AntennaLab Scan")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()

    return output_path
