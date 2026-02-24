from __future__ import annotations

import csv
from pathlib import Path


PALETTES = {
    "gray": "gray",
    "heat": "heat",
}


def _build_grid(rows: list[tuple[int, float, float]]) -> tuple[list[float], list[list[float]]]:
    freqs = sorted({freq for _, freq, _ in rows})
    freq_index = {f: i for i, f in enumerate(freqs)}
    max_slice = max(slice_idx for slice_idx, _, _ in rows) if rows else -1
    slices = max_slice + 1

    grid = [[float("nan") for _ in freqs] for _ in range(slices)]
    for slice_idx, freq_hz, avg_db in rows:
        grid[slice_idx][freq_index[freq_hz]] = avg_db
    return freqs, grid


def write_waterfall_html(
    input_csv: str | Path,
    output_html: str | Path,
    *,
    palette: str = "heat",
    vmin: float | None = None,
    vmax: float | None = None,
) -> Path:
    if palette not in PALETTES:
        raise ValueError(f"unsupported palette: {palette}")

    input_path = Path(input_csv)
    rows: list[tuple[int, float, float]] = []

    with input_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if header[:3] != ["timestamp", "slice_index", "freq_hz"]:
            raise ValueError("unexpected waterfall CSV header")
        for row in reader:
            if not row:
                continue
            rows.append((int(row[1]), float(row[2]), float(row[3])))

    freqs, grid = _build_grid(rows)
    flat_values = [val for row in grid for val in row if val == val]
    if not flat_values:
        raise ValueError("waterfall CSV has no data")

    data_min = min(flat_values)
    data_max = max(flat_values)
    vmin = data_min if vmin is None else vmin
    vmax = data_max if vmax is None else vmax

    output_path = Path(output_html)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>AntennaLab Waterfall</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 16px; }}
    canvas {{ border: 1px solid #ccc; width: 100%; height: auto; }}
    .controls {{ display: flex; gap: 12px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
    .meta {{ color: #555; font-size: 12px; }}
  </style>
</head>
<body>
  <h2>AntennaLab Waterfall</h2>
  <div class=\"controls\">
    <label>Palette
      <select id=\"palette\">
        <option value=\"heat\">heat</option>
        <option value=\"gray\">gray</option>
      </select>
    </label>
    <span class=\"meta\">Data range: {data_min:.2f} to {data_max:.2f}</span>
    <span class=\"meta\">Scale: vmin {vmin:.2f} / vmax {vmax:.2f}</span>
  </div>
  <canvas id=\"wf\" width=\"{len(freqs)}\" height=\"{len(grid)}\"></canvas>

  <script>
    const data = {grid};
    const vmin = {vmin};
    const vmax = {vmax};
    const paletteSelect = document.getElementById('palette');
    paletteSelect.value = '{palette}';
    const canvas = document.getElementById('wf');
    const ctx = canvas.getContext('2d');

    function clamp(val, min, max) {{
      return Math.max(min, Math.min(max, val));
    }}

    function colorFor(value, palette) {{
      const t = (value - vmin) / (vmax - vmin);
      const c = clamp(t, 0, 1);
      if (palette === 'gray') {{
        const g = Math.floor(c * 255);
        return [g, g, g];
      }}
      // heat: blue -> red
      const hue = (1 - c) * 240; // 240 blue to 0 red
      const [r, g, b] = hslToRgb(hue / 360, 1.0, 0.5);
      return [r, g, b];
    }}

    function hslToRgb(h, s, l) {{
      let r, g, b;
      if (s === 0) {{
        r = g = b = l;
      }} else {{
        const hue2rgb = function hue2rgb(p, q, t) {{
          if (t < 0) t += 1;
          if (t > 1) t -= 1;
          if (t < 1/6) return p + (q - p) * 6 * t;
          if (t < 1/2) return q;
          if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
          return p;
        }};
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
      }}
      return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
    }}

    function render() {{
      const img = ctx.createImageData(canvas.width, canvas.height);
      let idx = 0;
      for (let y = 0; y < canvas.height; y++) {{
        const row = data[y];
        for (let x = 0; x < canvas.width; x++) {{
          const val = row[x];
          const [r, g, b] = colorFor(val, paletteSelect.value);
          img.data[idx++] = r;
          img.data[idx++] = g;
          img.data[idx++] = b;
          img.data[idx++] = 255;
        }}
      }}
      ctx.putImageData(img, 0, 0);
    }}

    paletteSelect.addEventListener('change', render);
    render();
  </script>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    return output_path
