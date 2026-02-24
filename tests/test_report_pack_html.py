from pathlib import Path

from antennalab.report.report_pack_html import write_report_pack_html


def test_report_pack_html(tmp_path: Path) -> None:
    (tmp_path / "scan.png").write_text("x", encoding="utf-8")
    (tmp_path / "waterfall.png").write_text("y", encoding="utf-8")
    (tmp_path / "scan_report.json").write_text("{}", encoding="utf-8")

    index = write_report_pack_html(tmp_path)
    content = index.read_text(encoding="utf-8")
    assert "index.html" in str(index)
    assert "scan.png" in content
    assert "waterfall.png" in content
