from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from antennalab import __version__
from antennalab.analysis.alerts import AlertEngine, load_alert_rules, write_alert_hits
from antennalab.analysis.calibration import apply_baseline, load_baseline
from antennalab.analysis.calibration_profiles import (
    BaselineProfile,
    get_profile,
    load_profiles,
    remove_profile,
    upsert_profile,
)
from antennalab.analysis.compare import compare_to_csv
from antennalab.analysis.monitor import MonitorSettings, run_monitor
from antennalab.analysis.noise_floor import estimate_noise_floor
from antennalab.analysis.waterfall import WaterfallSettings, run_waterfall
from antennalab.bookmarks import (
    Bookmark,
    add_bookmark,
    export_bookmarks_json,
    import_bookmarks_json,
    load_bookmarks,
    match_bookmarks_to_range,
    match_bookmarks_to_scan,
    remove_bookmark,
)
from antennalab.config import load_config
from antennalab.core.models import SweepStatsBin
from antennalab.core.registry import get_instrument_plugins
from antennalab.instruments.rtlsdr import RTLSDRPlugin
from antennalab.report.export_csv import scan_from_csv, write_scan_csv, write_sweep_stats_csv
from antennalab.report.plot import plot_scan_csv
from antennalab.report.report_pack import build_report_pack
from antennalab.report.report_pack_html import write_report_pack_html
from antennalab.report.run_report import write_run_report
from antennalab.report.monitor_plot import plot_monitor_summary
from antennalab.report.waterfall_plot import plot_waterfall_csv
from antennalab.report.waterfall_html import write_waterfall_html


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


def _resolve_path(base: Path, path: Path) -> Path:
    return path if path.is_absolute() else (base / path)


def _resolve_base_dir(config_path: Path | None) -> Path:
    if config_path:
        base_dir = config_path.parent
        if base_dir.name == "config":
            base_dir = base_dir.parent
        return base_dir
    return Path.cwd()


def _profiles_path(base_dir: Path) -> Path:
    return base_dir / "config" / "baseline_profiles.json"


def cmd_scan(args: argparse.Namespace) -> int:
    config, config_path = load_config(args.config)
    scan_cfg = config.get("scan", {}) if isinstance(config, dict) else {}
    device_cfg = config.get("device", {}) if isinstance(config, dict) else {}
    output_cfg = config.get("output", {}) if isinstance(config, dict) else {}

    start_hz = args.start_hz or scan_cfg.get("start_hz")
    stop_hz = args.stop_hz or scan_cfg.get("stop_hz")
    bin_hz = args.bin_hz or scan_cfg.get("bin_hz")
    if start_hz is None or stop_hz is None or bin_hz is None:
        raise SystemExit("scan settings missing; provide --start-hz/--stop-hz/--bin-hz")

    mode = args.mode or scan_cfg.get("mode", "real")

    base_dir = _resolve_base_dir(config_path)

    scans_dir = _resolve_path(base_dir, Path(output_cfg.get("scans_dir", "data/scans")))
    reports_dir = _resolve_path(base_dir, Path(output_cfg.get("reports_dir", "data/reports")))

    out_csv = Path(args.out_csv) if args.out_csv else scans_dir / "scan.csv"
    out_json = Path(args.out_json) if args.out_json else None

    plugin = RTLSDRPlugin()
    sweep_stats: tuple[SweepStatsBin, ...] | None = None

    if mode == "sim":
        scan = plugin.scan_simulated(
            start_hz=float(start_hz),
            stop_hz=float(stop_hz),
            bin_hz=float(bin_hz),
            antenna_tag=args.antenna,
            location_tag=args.location,
            seed=args.seed,
        )
        if args.sweep_stats_csv:
            sweep_stats = tuple(
                SweepStatsBin(
                    freq_hz=b.freq_hz,
                    sweep_avg_min_db=b.avg_db,
                    sweep_avg_mean_db=b.avg_db,
                    sweep_avg_max_db=b.avg_db,
                )
                for b in scan.bins
            )
    else:
        sample_rate_hz = args.sample_rate or device_cfg.get("sample_rate_hz", 2_400_000)
        gain_db = args.gain if args.gain is not None else device_cfg.get("gain_db", "auto")
        fft_size = args.fft_size or device_cfg.get("fft_size", 4096)
        step_hz = args.step_hz if args.step_hz is not None else device_cfg.get("step_hz")
        sweeps = args.sweeps or device_cfg.get("sweeps", 3)
        dwell_ms = args.dwell_ms if args.dwell_ms is not None else device_cfg.get("dwell_ms", 0)
        missing_db = device_cfg.get("missing_db", -120.0)

        sweep_stats_path = getattr(args, "sweep_stats_csv", None)
        if sweep_stats_path:
            scan, sweep_stats = plugin.scan_real_with_sweep_stats(
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
        else:
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

    baseline_csv = getattr(args, "baseline_csv", None)
    baseline_tag = getattr(args, "baseline_tag", None)
    if baseline_tag:
        profile = get_profile(_profiles_path(base_dir), baseline_tag)
        if profile is None:
            raise SystemExit(f"Baseline tag not found: {baseline_tag}")
        baseline_csv = profile.csv_path

    if baseline_csv:
        baseline = load_baseline(baseline_csv)
        scan = apply_baseline(scan, baseline)

    write_scan_csv(scan, out_csv)
    print(f"Scan CSV: {out_csv}")

    sweep_stats_path = getattr(args, "sweep_stats_csv", None)
    if sweep_stats is not None and sweep_stats_path:
        out_stats = Path(sweep_stats_path)
        write_sweep_stats_csv(sweep_stats, out_stats)
        print(f"Sweep stats CSV: {out_stats}")

    bookmarks_file = getattr(args, "bookmarks_file", None)
    bookmarks_payload = None
    if bookmarks_file:
        bookmarks = load_bookmarks(bookmarks_file)
        matched = match_bookmarks_to_range(bookmarks, scan.start_hz, scan.stop_hz)
        bookmarks_payload = [
            {"freq_hz": bm.freq_hz, "label": bm.label, "notes": bm.notes}
            for bm in matched
        ]

    if out_json:
        write_run_report(scan, out_json, bookmarks=bookmarks_payload)
        print(f"Run report: {out_json}")
    else:
        default_report = reports_dir / "scan_report.json"
        write_run_report(scan, default_report, bookmarks=bookmarks_payload)
        print(f"Run report: {default_report}")

    return 0


def cmd_baseline_capture(args: argparse.Namespace) -> int:
    if args.out_csv is None:
        config, _ = load_config(args.config)
        output_cfg = config.get("output", {}) if isinstance(config, dict) else {}
        scans_dir = Path(output_cfg.get("scans_dir", "data/scans"))
        args.out_csv = str(scans_dir / "baseline.csv")
    return cmd_scan(args)


def cmd_baseline_tag(args: argparse.Namespace) -> int:
    base_dir = _resolve_base_dir(load_config(args.config)[1])
    profiles_path = _profiles_path(base_dir)
    profile = BaselineProfile(
        tag=args.tag,
        csv_path=args.csv_path,
        created_at=datetime.now(timezone.utc).isoformat(),
        notes=args.notes,
    )
    upsert_profile(profiles_path, profile)
    print(f"Baseline tag saved: {args.tag} -> {args.csv_path}")
    return 0


def cmd_baseline_list(args: argparse.Namespace) -> int:
    base_dir = _resolve_base_dir(load_config(args.config)[1])
    profiles = load_profiles(_profiles_path(base_dir))
    if not profiles:
        print("No baseline profiles found")
        return 0
    for profile in profiles:
        notes = f" - {profile.notes}" if profile.notes else ""
        print(f"{profile.tag}: {profile.csv_path}{notes}")
    return 0


def cmd_baseline_remove(args: argparse.Namespace) -> int:
    base_dir = _resolve_base_dir(load_config(args.config)[1])
    removed = remove_profile(_profiles_path(base_dir), args.tag)
    if removed:
        print(f"Baseline tag removed: {args.tag}")
        return 0
    print(f"Baseline tag not found: {args.tag}")
    return 1


def cmd_baseline_apply(args: argparse.Namespace) -> int:
    scan = scan_from_csv(args.scan_csv)
    baseline = load_baseline(args.baseline_csv)
    adjusted = apply_baseline(scan, baseline)
    write_scan_csv(adjusted, args.out_csv)
    print(f"Baseline-adjusted CSV: {args.out_csv}")
    return 0


def cmd_plot_scan(args: argparse.Namespace) -> int:
    output_path = plot_scan_csv(args.in_csv, args.out_png)
    print(f"Plot image: {output_path}")
    return 0


def cmd_waterfall(args: argparse.Namespace) -> int:
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
    waterfalls_dir = Path(output_cfg.get("waterfalls_dir", "data/waterfalls"))
    out_csv = Path(args.out_csv) if args.out_csv else waterfalls_dir / "waterfall.csv"

    sample_rate_hz = args.sample_rate or device_cfg.get("sample_rate_hz", 2_400_000)
    gain_db = args.gain if args.gain is not None else device_cfg.get("gain_db", "auto")
    fft_size = args.fft_size or device_cfg.get("fft_size", 4096)
    step_hz = args.step_hz if args.step_hz is not None else device_cfg.get("step_hz")
    sweeps = args.sweeps or device_cfg.get("sweeps", 3)
    dwell_ms = args.dwell_ms if args.dwell_ms is not None else device_cfg.get("dwell_ms", 0)
    missing_db = device_cfg.get("missing_db", -120.0)

    settings = WaterfallSettings(
        mode=mode,
        start_hz=float(start_hz),
        stop_hz=float(stop_hz),
        bin_hz=float(bin_hz),
        slices=int(args.slices),
        interval_ms=int(args.interval_ms),
        sample_rate_hz=float(sample_rate_hz),
        gain_db=gain_db,
        fft_size=int(fft_size),
        step_hz=float(step_hz) if step_hz is not None else None,
        sweeps=int(sweeps),
        dwell_ms=int(dwell_ms),
        missing_db=float(missing_db),
        seed=args.seed,
    )

    out_path = run_waterfall(settings, out_csv)
    print(f"Waterfall CSV: {out_path}")
    return 0


def cmd_plot_waterfall(args: argparse.Namespace) -> int:
    config, _ = load_config(args.config)
    plot_cfg = config.get("waterfall_plot", {}) if isinstance(config, dict) else {}
    cmap = args.cmap if args.cmap is not None else plot_cfg.get("cmap", "viridis")
    vmin = args.vmin if args.vmin is not None else plot_cfg.get("vmin")
    vmax = args.vmax if args.vmax is not None else plot_cfg.get("vmax")

    output_path = plot_waterfall_csv(
        args.in_csv,
        args.out_png,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )
    print(f"Waterfall image: {output_path}")
    return 0


def cmd_waterfall_html(args: argparse.Namespace) -> int:
    output_path = write_waterfall_html(
        args.in_csv,
        args.out_html,
        palette=args.palette,
        vmin=args.vmin,
        vmax=args.vmax,
    )
    print(f"Waterfall HTML: {output_path}")
    return 0


def cmd_bookmark_add(args: argparse.Namespace) -> int:
    bookmark = Bookmark(freq_hz=float(args.freq_hz), label=args.label or "", notes=args.notes or "")
    add_bookmark(args.file, bookmark)
    print(f"Bookmark added: {args.freq_hz} Hz")
    return 0


def cmd_bookmark_list(args: argparse.Namespace) -> int:
    bookmarks = load_bookmarks(args.file)
    if not bookmarks:
        print("No bookmarks found")
        return 0
    for bm in bookmarks:
        label = f" [{bm.label}]" if bm.label else ""
        notes = f" - {bm.notes}" if bm.notes else ""
        print(f"{bm.freq_hz:.0f} Hz{label}{notes}")
    return 0


def cmd_bookmark_remove(args: argparse.Namespace) -> int:
    freq_hz = float(args.freq_hz) if args.freq_hz is not None else None
    _, removed = remove_bookmark(args.file, freq_hz=freq_hz, label=args.label)
    print(f"Removed {removed} bookmark(s)")
    return 0


def cmd_bookmark_export(args: argparse.Namespace) -> int:
    output = export_bookmarks_json(args.file, args.out_json)
    print(f"Exported bookmarks: {output}")
    return 0


def cmd_bookmark_import(args: argparse.Namespace) -> int:
    output = import_bookmarks_json(args.file, args.in_json)
    print(f"Imported bookmarks: {output}")
    return 0


def cmd_bookmark_match(args: argparse.Namespace) -> int:
    matches = match_bookmarks_to_scan(args.scan_csv, args.file)
    if not matches:
        print("No bookmarks in scan range")
        return 0
    for bm in matches:
        label = f" [{bm.label}]" if bm.label else ""
        notes = f" - {bm.notes}" if bm.notes else ""
        print(f"{bm.freq_hz:.0f} Hz{label}{notes}")
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


def cmd_report_pack(args: argparse.Namespace) -> int:
    config, config_path = load_config(args.config)
    output_cfg = config.get("output", {}) if isinstance(config, dict) else {}

    base_dir = _resolve_base_dir(config_path)

    scans_dir = _resolve_path(base_dir, Path(output_cfg.get("scans_dir", "data/scans")))
    reports_dir = _resolve_path(base_dir, Path(output_cfg.get("reports_dir", "data/reports")))
    waterfalls_dir = _resolve_path(base_dir, Path(output_cfg.get("waterfalls_dir", "data/waterfalls")))
    out_dir = _resolve_path(base_dir, Path(args.out_dir)) if args.out_dir else reports_dir

    pack_dir, copied = build_report_pack(
        session_name=args.session,
        scans_dir=scans_dir,
        reports_dir=reports_dir,
        waterfalls_dir=waterfalls_dir,
        out_dir=out_dir,
    )
    html_path = write_report_pack_html(pack_dir)
    print(f"Report pack: {pack_dir} ({copied} file(s) copied)")
    print(f"Report index: {html_path}")
    if copied == 0:
        print("Warning: report pack is empty. Run scans or plots first.")
    return 0


def cmd_monitor_plot(args: argparse.Namespace) -> int:
    output = plot_monitor_summary(args.in_json, args.out_png)
    print(f"Monitor plot: {output}")
    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    config, config_path = load_config(args.config)
    scan_cfg = config.get("scan", {}) if isinstance(config, dict) else {}
    device_cfg = config.get("device", {}) if isinstance(config, dict) else {}
    output_cfg = config.get("output", {}) if isinstance(config, dict) else {}

    start_hz = args.start_hz or scan_cfg.get("start_hz")
    stop_hz = args.stop_hz or scan_cfg.get("stop_hz")
    bin_hz = args.bin_hz or scan_cfg.get("bin_hz")
    if start_hz is None or stop_hz is None or bin_hz is None:
        raise SystemExit("scan settings missing; provide --start-hz/--stop-hz/--bin-hz")

    mode = args.mode or scan_cfg.get("mode", "real")

    interval_sec = int(args.interval_sec)
    if args.duration_min is not None:
        iterations = max(1, int((args.duration_min * 60) // interval_sec))
    else:
        iterations = int(args.iterations)

    base_dir = _resolve_base_dir(config_path)
    reports_dir = _resolve_path(base_dir, Path(output_cfg.get("reports_dir", "data/reports")))

    session = args.session or "monitor"
    out_dir = reports_dir / f"monitor_{session}"

    settings = MonitorSettings(
        mode=mode,
        start_hz=float(start_hz),
        stop_hz=float(stop_hz),
        bin_hz=float(bin_hz),
        sample_rate_hz=float(args.sample_rate or device_cfg.get("sample_rate_hz", 2_400_000)),
        gain_db=args.gain if args.gain is not None else device_cfg.get("gain_db", "auto"),
        fft_size=int(args.fft_size or device_cfg.get("fft_size", 4096)),
        step_hz=float(args.step_hz) if args.step_hz is not None else device_cfg.get("step_hz"),
        sweeps=int(args.sweeps or device_cfg.get("sweeps", 3)),
        dwell_ms=int(args.dwell_ms if args.dwell_ms is not None else device_cfg.get("dwell_ms", 0)),
        missing_db=float(device_cfg.get("missing_db", -120.0)),
        interval_sec=interval_sec,
        iterations=iterations,
        seed=args.seed,
        bookmarks_file=Path(args.bookmarks_file) if args.bookmarks_file else None,
    )

    summary_path = run_monitor(settings, out_dir=out_dir)
    print(f"Monitor summary: {summary_path}")
    if args.report_pack:
        pack_dir, copied = build_report_pack(
            session_name=args.report_pack_session or f"{session}_pack",
            scans_dir=out_dir / "scans",
            reports_dir=out_dir / "reports",
            waterfalls_dir=out_dir / "waterfalls",
            out_dir=out_dir,
        )
        print(f"Monitor report pack: {pack_dir} ({copied} file(s) copied)")
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
    scan_parser.add_argument("--baseline-csv", help="Baseline scan CSV to subtract")
    scan_parser.add_argument("--baseline-tag", help="Baseline tag to apply")
    scan_parser.add_argument("--sweep-stats-csv", help="Output sweep stats CSV path")
    scan_parser.add_argument("--bookmarks-file", default="config/bookmarks.csv", help="Bookmarks CSV file")
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

    baseline_capture_parser = subparsers.add_parser(
        "baseline-capture", help="Capture a baseline scan"
    )
    baseline_capture_parser.add_argument("--mode", choices=["real", "sim"], help="Scan mode")
    baseline_capture_parser.add_argument("--start-hz", type=float, help="Scan start frequency (Hz)")
    baseline_capture_parser.add_argument("--stop-hz", type=float, help="Scan stop frequency (Hz)")
    baseline_capture_parser.add_argument("--bin-hz", type=float, help="Bin size (Hz)")
    baseline_capture_parser.add_argument("--out-csv", help="Output CSV path")
    baseline_capture_parser.add_argument("--out-json", help="Output JSON run report path")
    baseline_capture_parser.add_argument("--sweep-stats-csv", help="Output sweep stats CSV path")
    baseline_capture_parser.add_argument("--antenna", help="Antenna profile tag")
    baseline_capture_parser.add_argument("--location", help="Location profile tag")
    baseline_capture_parser.add_argument("--seed", type=int, help="Random seed for simulated scan")
    baseline_capture_parser.add_argument("--sample-rate", type=float, help="RTL-SDR sample rate (Hz)")
    baseline_capture_parser.add_argument("--gain", help="RTL-SDR gain (auto or dB)")
    baseline_capture_parser.add_argument("--fft-size", type=int, help="FFT size per sweep")
    baseline_capture_parser.add_argument("--step-hz", type=float, help="Sweep step size (Hz)")
    baseline_capture_parser.add_argument("--sweeps", type=int, help="Number of sweeps to average")
    baseline_capture_parser.add_argument("--dwell-ms", type=int, help="Delay between center steps (ms)")
    baseline_capture_parser.set_defaults(func=cmd_baseline_capture)

    baseline_tag_parser = subparsers.add_parser(
        "baseline-tag", help="Tag a baseline CSV for later use"
    )
    baseline_tag_parser.add_argument("--tag", required=True, help="Tag name")
    baseline_tag_parser.add_argument("--csv-path", required=True, help="Baseline CSV path")
    baseline_tag_parser.add_argument("--notes", help="Notes")
    baseline_tag_parser.set_defaults(func=cmd_baseline_tag)

    baseline_list_parser = subparsers.add_parser(
        "baseline-list", help="List baseline profiles"
    )
    baseline_list_parser.set_defaults(func=cmd_baseline_list)

    baseline_remove_parser = subparsers.add_parser(
        "baseline-remove", help="Remove a baseline profile"
    )
    baseline_remove_parser.add_argument("--tag", required=True, help="Tag name")
    baseline_remove_parser.set_defaults(func=cmd_baseline_remove)

    baseline_parser = subparsers.add_parser(
        "baseline-apply", help="Apply baseline to an existing scan CSV"
    )
    baseline_parser.add_argument("--scan-csv", required=True, help="Input scan CSV")
    baseline_parser.add_argument("--baseline-csv", required=True, help="Baseline CSV")
    baseline_parser.add_argument("--out-csv", required=True, help="Output CSV")
    baseline_parser.set_defaults(func=cmd_baseline_apply)

    plot_parser = subparsers.add_parser("plot-scan", help="Plot a scan CSV to PNG")
    plot_parser.add_argument("--in-csv", required=True, help="Input scan CSV")
    plot_parser.add_argument(
        "--out-png",
        default="data/reports/scan.png",
        help="Output PNG path",
    )
    plot_parser.set_defaults(func=cmd_plot_scan)

    waterfall_parser = subparsers.add_parser("waterfall", help="Capture a waterfall CSV")
    waterfall_parser.add_argument("--mode", choices=["real", "sim"], help="Scan mode")
    waterfall_parser.add_argument("--start-hz", type=float, help="Scan start frequency (Hz)")
    waterfall_parser.add_argument("--stop-hz", type=float, help="Scan stop frequency (Hz)")
    waterfall_parser.add_argument("--bin-hz", type=float, help="Bin size (Hz)")
    waterfall_parser.add_argument("--slices", type=int, default=20, help="Number of time slices")
    waterfall_parser.add_argument(
        "--interval-ms",
        type=int,
        default=0,
        help="Delay between slices (ms)",
    )
    waterfall_parser.add_argument("--out-csv", help="Output waterfall CSV path")
    waterfall_parser.add_argument("--seed", type=int, help="Random seed for simulated mode")
    waterfall_parser.add_argument("--sample-rate", type=float, help="RTL-SDR sample rate (Hz)")
    waterfall_parser.add_argument("--gain", help="RTL-SDR gain (auto or dB)")
    waterfall_parser.add_argument("--fft-size", type=int, help="FFT size per sweep")
    waterfall_parser.add_argument("--step-hz", type=float, help="Sweep step size (Hz)")
    waterfall_parser.add_argument("--sweeps", type=int, help="Number of sweeps to average")
    waterfall_parser.add_argument("--dwell-ms", type=int, help="Delay between center steps (ms)")
    waterfall_parser.set_defaults(func=cmd_waterfall)

    waterfall_plot_parser = subparsers.add_parser(
        "plot-waterfall", help="Plot a waterfall CSV to PNG"
    )
    waterfall_plot_parser.add_argument("--in-csv", required=True, help="Input waterfall CSV")
    waterfall_plot_parser.add_argument(
        "--out-png",
        default="data/reports/waterfall.png",
        help="Output PNG path",
    )
    waterfall_plot_parser.add_argument(
        "--cmap",
        help="Matplotlib colormap (e.g., viridis, plasma, magma)",
    )
    waterfall_plot_parser.add_argument(
        "--vmin",
        type=float,
        help="Lower bound for color scale",
    )
    waterfall_plot_parser.add_argument(
        "--vmax",
        type=float,
        help="Upper bound for color scale",
    )
    waterfall_plot_parser.set_defaults(func=cmd_plot_waterfall)

    waterfall_html_parser = subparsers.add_parser(
        "waterfall-html", help="Generate a self-contained HTML waterfall viewer"
    )
    waterfall_html_parser.add_argument("--in-csv", required=True, help="Input waterfall CSV")
    waterfall_html_parser.add_argument(
        "--out-html",
        default="data/reports/waterfall.html",
        help="Output HTML path",
    )
    waterfall_html_parser.add_argument(
        "--palette",
        choices=["heat", "gray"],
        default="heat",
        help="Color palette",
    )
    waterfall_html_parser.add_argument(
        "--vmin",
        type=float,
        help="Lower bound for color scale",
    )
    waterfall_html_parser.add_argument(
        "--vmax",
        type=float,
        help="Upper bound for color scale",
    )
    waterfall_html_parser.set_defaults(func=cmd_waterfall_html)

    bookmarks_parser = subparsers.add_parser("bookmarks", help="Manage frequency bookmarks")
    bookmarks_sub = bookmarks_parser.add_subparsers(dest="bookmarks_cmd", required=True)

    bookmarks_add = bookmarks_sub.add_parser("add", help="Add a bookmark")
    bookmarks_add.add_argument("--freq-hz", required=True, type=float, help="Frequency in Hz")
    bookmarks_add.add_argument("--label", help="Short label")
    bookmarks_add.add_argument("--notes", help="Notes")
    bookmarks_add.add_argument(
        "--file",
        default="config/bookmarks.csv",
        help="Bookmarks CSV file",
    )
    bookmarks_add.set_defaults(func=cmd_bookmark_add)

    bookmarks_list = bookmarks_sub.add_parser("list", help="List bookmarks")
    bookmarks_list.add_argument(
        "--file",
        default="config/bookmarks.csv",
        help="Bookmarks CSV file",
    )
    bookmarks_list.set_defaults(func=cmd_bookmark_list)

    bookmarks_remove = bookmarks_sub.add_parser("remove", help="Remove bookmarks")
    bookmarks_remove.add_argument("--freq-hz", type=float, help="Frequency in Hz")
    bookmarks_remove.add_argument("--label", help="Label match")
    bookmarks_remove.add_argument(
        "--file",
        default="config/bookmarks.csv",
        help="Bookmarks CSV file",
    )
    bookmarks_remove.set_defaults(func=cmd_bookmark_remove)

    bookmarks_export = bookmarks_sub.add_parser("export", help="Export bookmarks to JSON")
    bookmarks_export.add_argument(
        "--file",
        default="config/bookmarks.csv",
        help="Bookmarks CSV file",
    )
    bookmarks_export.add_argument(
        "--out-json",
        default="data/reports/bookmarks.json",
        help="Output JSON path",
    )
    bookmarks_export.set_defaults(func=cmd_bookmark_export)

    bookmarks_import = bookmarks_sub.add_parser("import", help="Import bookmarks from JSON")
    bookmarks_import.add_argument(
        "--file",
        default="config/bookmarks.csv",
        help="Bookmarks CSV file",
    )
    bookmarks_import.add_argument(
        "--in-json",
        required=True,
        help="Input JSON path",
    )
    bookmarks_import.set_defaults(func=cmd_bookmark_import)

    bookmarks_match = bookmarks_sub.add_parser(
        "match", help="List bookmarks that fall within a scan's range"
    )
    bookmarks_match.add_argument("--scan-csv", required=True, help="Scan CSV path")
    bookmarks_match.add_argument(
        "--file",
        default="config/bookmarks.csv",
        help="Bookmarks CSV file",
    )
    bookmarks_match.set_defaults(func=cmd_bookmark_match)

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

    report_pack_parser = subparsers.add_parser(
        "report-pack", help="Bundle latest outputs into a session folder"
    )
    report_pack_parser.add_argument("--session", help="Session name (folder)")
    report_pack_parser.add_argument(
        "--out-dir",
        help="Output base directory (default: reports dir)",
    )
    report_pack_parser.set_defaults(func=cmd_report_pack)

    monitor_plot_parser = subparsers.add_parser(
        "monitor-plot", help="Plot monitor summary JSON to PNG"
    )
    monitor_plot_parser.add_argument("--in-json", required=True, help="Monitor summary JSON")
    monitor_plot_parser.add_argument(
        "--out-png",
        default="data/reports/monitor_plot.png",
        help="Output PNG path",
    )
    monitor_plot_parser.set_defaults(func=cmd_monitor_plot)

    monitor_parser = subparsers.add_parser(
        "monitor", help="Run repeated scans over time"
    )
    monitor_parser.add_argument("--mode", choices=["real", "sim"], help="Scan mode")
    monitor_parser.add_argument("--start-hz", type=float, help="Scan start frequency (Hz)")
    monitor_parser.add_argument("--stop-hz", type=float, help="Scan stop frequency (Hz)")
    monitor_parser.add_argument("--bin-hz", type=float, help="Bin size (Hz)")
    monitor_parser.add_argument("--interval-sec", type=int, default=60, help="Interval seconds")
    monitor_parser.add_argument("--iterations", type=int, default=10, help="Number of scans")
    monitor_parser.add_argument("--duration-min", type=int, help="Total duration in minutes")
    monitor_parser.add_argument("--session", help="Session name")
    monitor_parser.add_argument("--seed", type=int, help="Random seed for simulated scan")
    monitor_parser.add_argument("--bookmarks-file", default="config/bookmarks.csv", help="Bookmarks CSV file")
    monitor_parser.add_argument("--sample-rate", type=float, help="RTL-SDR sample rate (Hz)")
    monitor_parser.add_argument("--gain", help="RTL-SDR gain (auto or dB)")
    monitor_parser.add_argument("--fft-size", type=int, help="FFT size per sweep")
    monitor_parser.add_argument("--step-hz", type=float, help="Sweep step size (Hz)")
    monitor_parser.add_argument("--sweeps", type=int, help="Number of sweeps to average")
    monitor_parser.add_argument("--dwell-ms", type=int, help="Delay between center steps (ms)")
    monitor_parser.add_argument(
        "--report-pack",
        action="store_true",
        help="Create a report pack in the monitor folder after completion",
    )
    monitor_parser.add_argument(
        "--report-pack-session",
        help="Override report pack session name",
    )
    monitor_parser.set_defaults(func=cmd_monitor)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
