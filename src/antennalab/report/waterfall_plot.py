from __future__ import annotations

import csv
from pathlib import Path


def plot_waterfall_csv(
    input_csv: str | Path,
    output_png: str | Path,
    *,
    cmap: str = "viridis",
    vmin: float | None = None,
    vmax: float | None = None,
) -> Path:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise SystemExit(
            "plot-waterfall requires matplotlib and numpy. Install with: pip install matplotlib numpy"
        ) from exc

    input_path = Path(input_csv)
    rows: list[tuple[int, float, float]] = []
    freqs: list[float] = []
    max_slice = -1

    with input_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if header[:3] != ["timestamp", "slice_index", "freq_hz"]:
            raise ValueError("unexpected waterfall CSV header")
        for row in reader:
            if not row:
                continue
            slice_index = int(row[1])
            freq_hz = float(row[2])
            avg_db = float(row[3])
            rows.append((slice_index, freq_hz, avg_db))
            if freq_hz not in freqs:
                freqs.append(freq_hz)
            if slice_index > max_slice:
                max_slice = slice_index

    freqs = sorted(freqs)
    freq_index = {f: i for i, f in enumerate(freqs)}
    slices = max_slice + 1

    grid = np.full((slices, len(freqs)), np.nan, dtype=float)
    for slice_index, freq_hz, avg_db in rows:
        grid[slice_index, freq_index[freq_hz]] = avg_db

    output_path = Path(output_png)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 5))
    extent = [freqs[0] / 1e6, freqs[-1] / 1e6, slices, 0]
    plt.imshow(
        grid,
        aspect="auto",
        extent=extent,
        interpolation="nearest",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )
    plt.colorbar(label="avg_db")
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Slice Index")
    plt.title("AntennaLab Waterfall")
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()

    return output_path
