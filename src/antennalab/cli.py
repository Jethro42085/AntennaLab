from __future__ import annotations

import argparse
from pathlib import Path

from antennalab import __version__
from antennalab.config import load_config
from antennalab.core.registry import get_instrument_plugins
from antennalab.instruments.rtlsdr import RTLSDRPlugin
from antennalab.report.export_csv import write_scan_csv
from antennalab.report.run_report import write_run_report


def cmd_info(args: argparse.Namespace) -> int:
    config, config_path = load_config(args.config)
    print(f"AntennaLab {__version__}")
    print(f"Config: {config_path if config_path else 'not found'}")
    print("Plugins:")
    for plugin in get_instrument_plugins():
        info = plugin.info()
        print(f"- {info.name} ({info.kind}): {info.description}")
    if not config:
        print("Config contents: empty")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    config, config_path = load_config(args.config)
    print(f"Config: {config_path if config_path else 'not found'}")
    overall_ok = True
    for plugin in get_instrument_plugins():
        info = plugin.info()
        health = plugin.healthcheck(config)
        status = "OK" if health.ok else "ERROR"
        print(f"{info.name}: {status} - {health.detail}")
        if not health.ok:
            overall_ok = False
    return 0 if overall_ok else 1


def cmd_scan(args: argparse.Namespace) -> int:
    config, _ = load_config(args.config)
    scan_cfg = config.get("scan", {}) if isinstance(config, dict) else {}
    output_cfg = config.get("output", {}) if isinstance(config, dict) else {}

    start_hz = args.start_hz or scan_cfg.get("start_hz")
    stop_hz = args.stop_hz or scan_cfg.get("stop_hz")
    bin_hz = args.bin_hz or scan_cfg.get("bin_hz")
    if start_hz is None or stop_hz is None or bin_hz is None:
        raise SystemExit("scan settings missing; provide --start-hz/--stop-hz/--bin-hz")

    scans_dir = Path(output_cfg.get("scans_dir", "data/scans"))
    reports_dir = Path(output_cfg.get("reports_dir", "data/reports"))

    out_csv = Path(args.out_csv) if args.out_csv else scans_dir / "scan.csv"
    out_json = Path(args.out_json) if args.out_json else None

    plugin = RTLSDRPlugin()
    scan = plugin.scan_simulated(
        start_hz=float(start_hz),
        stop_hz=float(stop_hz),
        bin_hz=float(bin_hz),
        antenna_tag=args.antenna,
        location_tag=args.location,
        seed=args.seed,
    )

    write_scan_csv(scan, out_csv)
    print(f"Scan CSV: {out_csv}")

    if out_json:
        write_run_report(scan, out_json)
        print(f"Run report: {out_json}")
    else:
        default_report = reports_dir / "scan_report.json"
        write_run_report(scan, default_report)
        print(f"Run report: {default_report}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="antennalab",
        description="Laptop-based antenna/RF toolkit",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config file (default: ./config/antennalab.yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="Show project info")
    info_parser.set_defaults(func=cmd_info)

    health_parser = subparsers.add_parser("health", help="Run health checks")
    health_parser.set_defaults(func=cmd_health)

    scan_parser = subparsers.add_parser("scan", help="Run a simulated band scan")
    scan_parser.add_argument("--start-hz", type=float, help="Scan start frequency (Hz)")
    scan_parser.add_argument("--stop-hz", type=float, help="Scan stop frequency (Hz)")
    scan_parser.add_argument("--bin-hz", type=float, help="Bin size (Hz)")
    scan_parser.add_argument("--out-csv", help="Output CSV path")
    scan_parser.add_argument("--out-json", help="Output JSON run report path")
    scan_parser.add_argument("--antenna", help="Antenna profile tag")
    scan_parser.add_argument("--location", help="Location profile tag")
    scan_parser.add_argument("--seed", type=int, help="Random seed for simulated scan")
    scan_parser.set_defaults(func=cmd_scan)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
