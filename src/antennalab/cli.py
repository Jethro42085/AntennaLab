from __future__ import annotations

import argparse

from antennalab import __version__
from antennalab.config import load_config
from antennalab.core.registry import get_instrument_plugins


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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
