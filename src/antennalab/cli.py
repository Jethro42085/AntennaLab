from __future__ import annotations

import argparse
from pathlib import Path

from antennalab import __version__
from antennalab.analysis.alerts import AlertEngine, load_alert_rules, write_alert_hits
from antennalab.analysis.compare import compare_to_csv
from antennalab.analysis.noise_floor import estimate_noise_floor
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
    device_cfg = config.get("device", {}) if isinstance(config, dict) else {}
    output_cfg = config.get("output", {}) if isinstance(config, dict) else {}

    start_hz = args.start_hz or scan_cfg.get("start_hz")
    stop_hz = args.stop_hz or scan_cfg.get("stop_hz")
    bin_hz = args.bin_hz or scan_cfg.get("bin_hz")
    if start_hz is None or stop_hz is None or bin_hz is None:
        raise SystemExit("scan settings missing; provide --start-hz/--stop-hz/--bin-hz")

    mode = args.mode or scan_cfg.get("mode", "real")

    scans_dir = Path(output_cfg.get("scans_dir", "data/scans"))
    reports_dir = Path(output_cfg.get("reports_dir", "data/reports"))

    out_csv = Path(args.out_csv) if args.out_csv else scans_dir / "scan.csv"
    out_json = Path(args.out_json) if args.out_json else None

    plugin = RTLSDRPlugin()
    if mode == "sim":
        scan = plugin.scan_simulated(
            start_hz=float(start_hz),
            stop_hz=float(stop_hz),
            bin_hz=float(bin_hz),
            antenna_tag=args.antenna,
            location_tag=args.location,
            seed=args.seed,
        )
    else:
        sample_rate_hz = args.sample_rate or device_cfg.get("sample_rate_hz", 2_400_000)
        gain_db = args.gain if args.gain is not None else device_cfg.get("gain_db", "auto")
        fft_size = args.fft_size or device_cfg.get("fft_size", 4096)
        step_hz = args.step_hz if args.step_hz is not None else device_cfg.get("step_hz")
        sweeps = args.sweeps or device_cfg.get("sweeps", 3)
        dwell_ms = args.dwell_ms if args.dwell_ms is not None else device_cfg.get("dwell_ms", 0)
        missing_db = device_cfg.get("missing_db", -120.0)

        scan = plugin.scan_real(
            start_hz=float(start_hz),
            stop_hz=float(stop_hz),
            bin_hz=float(bin_hz),
            sample_rate_hz=float(sample_rate_hz),
            gain_db=gain_db,
            fft_size=int(fft_size),
            step_hz=float(step_hz) if step_hz is not None else None,
            sweeps=int(sweeps),
            dwell_ms=int(dwell_ms),
            missing_db=float(missing_db),
            antenna_tag=args.antenna,
            location_tag=args.location,
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


def cmd_noise_floor(args: argparse.Namespace) -> int:
    config, _ = load_config(args.config)
    output_cfg = config.get("output", {}) if isinstance(config, dict) else {}
    reports_dir = Path(output_cfg.get("reports_dir", "data/reports"))

    out_csv = Path(args.out_csv) if args.out_csv else reports_dir / "noise_floor.csv"
    estimate_noise_floor(
        scan_csv=args.in_csv,
        out_csv=out_csv,
        strategy=args.strategy,
    )
    print(f"Noise floor CSV: {out_csv}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    config, _ = load_config(args.config)
    output_cfg = config.get("output", {}) if isinstance(config, dict) else {}
    reports_dir = Path(output_cfg.get("reports_dir", "data/reports"))

    out_csv = Path(args.out_csv) if args.out_csv else reports_dir / "compare.csv"
    compare_to_csv(args.scan_a, args.scan_b, out_csv)
    print(f"Compare CSV: {out_csv}")
    return 0


def cmd_alerts(args: argparse.Namespace) -> int:
    output_path = Path(args.out_log)
    rules = load_alert_rules(args.rules)
    engine = AlertEngine(rules)
    hits = engine.evaluate(args.scan_csv)
    write_alert_hits(hits, output_path)
    print(f"Alert log: {output_path} ({len(hits)} hits)")
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

    scan_parser = subparsers.add_parser("scan", help="Run a band scan")
    scan_parser.add_argument("--mode", choices=["real", "sim"], help="Scan mode")
    scan_parser.add_argument("--start-hz", type=float, help="Scan start frequency (Hz)")
    scan_parser.add_argument("--stop-hz", type=float, help="Scan stop frequency (Hz)")
    scan_parser.add_argument("--bin-hz", type=float, help="Bin size (Hz)")
    scan_parser.add_argument("--out-csv", help="Output CSV path")
    scan_parser.add_argument("--out-json", help="Output JSON run report path")
    scan_parser.add_argument("--antenna", help="Antenna profile tag")
    scan_parser.add_argument("--location", help="Location profile tag")
    scan_parser.add_argument("--seed", type=int, help="Random seed for simulated scan")
    scan_parser.add_argument("--sample-rate", type=float, help="RTL-SDR sample rate (Hz)")
    scan_parser.add_argument("--gain", help="RTL-SDR gain (auto or dB)")
    scan_parser.add_argument("--fft-size", type=int, help="FFT size per sweep")
    scan_parser.add_argument("--step-hz", type=float, help="Sweep step size (Hz)")
    scan_parser.add_argument("--sweeps", type=int, help="Number of sweeps to average")
    scan_parser.add_argument("--dwell-ms", type=int, help="Delay between center steps (ms)")
    scan_parser.set_defaults(func=cmd_scan)

    noise_parser = subparsers.add_parser("noise-floor", help="Estimate noise floor")
    noise_parser.add_argument("--in-csv", required=True, help="Input scan CSV path")
    noise_parser.add_argument("--out-csv", help="Output noise floor CSV path")
    noise_parser.add_argument(
        "--strategy",
        default="avg",
        help="Noise floor strategy (avg)",
    )
    noise_parser.set_defaults(func=cmd_noise_floor)

    compare_parser = subparsers.add_parser("compare", help="Compare two scans")
    compare_parser.add_argument("--scan-a", required=True, help="Scan A CSV path")
    compare_parser.add_argument("--scan-b", required=True, help="Scan B CSV path")
    compare_parser.add_argument("--out-csv", help="Output compare CSV path")
    compare_parser.set_defaults(func=cmd_compare)

    alerts_parser = subparsers.add_parser("alerts", help="Run alert rules on a scan")
    alerts_parser.add_argument("--scan-csv", required=True, help="Input scan CSV path")
    alerts_parser.add_argument(
        "--rules",
        default="config/alerts.csv",
        help="Alert rules CSV (freq_hz,threshold_db)",
    )
    alerts_parser.add_argument(
        "--out-log",
        default="data/reports/alerts.csv",
        help="Output alerts CSV path",
    )
    alerts_parser.set_defaults(func=cmd_alerts)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
