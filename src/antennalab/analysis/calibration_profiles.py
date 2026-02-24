from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BaselineProfile:
    tag: str
    csv_path: str
    created_at: str
    notes: str | None = None


def load_profiles(path: str | Path) -> list[BaselineProfile]:
    input_path = Path(path)
    if not input_path.exists():
        return []
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    profiles = [
        BaselineProfile(
            tag=item["tag"],
            csv_path=item["csv_path"],
            created_at=item["created_at"],
            notes=item.get("notes"),
        )
        for item in payload
    ]
    return profiles


def save_profiles(path: str | Path, profiles: list[BaselineProfile]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "tag": profile.tag,
            "csv_path": profile.csv_path,
            "created_at": profile.created_at,
            "notes": profile.notes,
        }
        for profile in profiles
    ]
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def upsert_profile(path: str | Path, profile: BaselineProfile) -> Path:
    profiles = [p for p in load_profiles(path) if p.tag != profile.tag]
    profiles.append(profile)
    profiles.sort(key=lambda p: p.tag)
    return save_profiles(path, profiles)


def get_profile(path: str | Path, tag: str) -> BaselineProfile | None:
    for profile in load_profiles(path):
        if profile.tag == tag:
            return profile
    return None


def remove_profile(path: str | Path, tag: str) -> bool:
    profiles = load_profiles(path)
    remaining = [p for p in profiles if p.tag != tag]
    if len(remaining) == len(profiles):
        return False
    save_profiles(path, remaining)
    return True
