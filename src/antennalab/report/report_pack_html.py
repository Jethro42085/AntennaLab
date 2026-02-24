from __future__ import annotations

from pathlib import Path


def write_report_pack_html(pack_dir: str | Path) -> Path:
    pack_path = Path(pack_dir)
    summary_path = pack_path / "summary.json"
    scan_png = pack_path / "scan.png"
    waterfall_png = pack_path / "waterfall.png"
    waterfall_html = pack_path / "waterfall.html"

    def rel(path: Path) -> str:
        return path.name

    html = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\" />",
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
        "  <title>AntennaLab Report Pack</title>",
        "  <style>",
        "    body { font-family: Arial, sans-serif; margin: 16px; }",
        "    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }",
        "    .card { border: 1px solid #ddd; padding: 12px; border-radius: 6px; }",
        "    img { max-width: 100%; height: auto; }",
        "    a { text-decoration: none; color: #0a58ca; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <h2>AntennaLab Report Pack</h2>",
        "  <div class=\"grid\">",
    ]

    if scan_png.exists():
        html += [
            "    <div class=\"card\">",
            "      <h3>Scan Plot</h3>",
            f"      <img src=\"{rel(scan_png)}\" alt=\"scan\" />",
            "    </div>",
        ]

    if waterfall_png.exists():
        html += [
            "    <div class=\"card\">",
            "      <h3>Waterfall Plot</h3>",
            f"      <img src=\"{rel(waterfall_png)}\" alt=\"waterfall\" />",
            "    </div>",
        ]

    html.append("  </div>")

    html += [
        "  <h3>Files</h3>",
        "  <ul>",
    ]

    if summary_path.exists():
        html.append(f"    <li><a href=\"{rel(summary_path)}\">summary.json</a></li>")
    if (pack_path / "scan_report.json").exists():
        html.append("    <li><a href=\"scan_report.json\">scan_report.json</a></li>")
    if (pack_path / "scan.csv").exists():
        html.append("    <li><a href=\"scan.csv\">scan.csv</a></li>")
    if (pack_path / "waterfall.csv").exists():
        html.append("    <li><a href=\"waterfall.csv\">waterfall.csv</a></li>")
    if waterfall_html.exists():
        html.append(f"    <li><a href=\"{rel(waterfall_html)}\">waterfall.html</a></li>")

    html += [
        "  </ul>",
        "</body>",
        "</html>",
    ]

    output_path = pack_path / "index.html"
    output_path.write_text("\n".join(html) + "\n", encoding="utf-8")
    return output_path
