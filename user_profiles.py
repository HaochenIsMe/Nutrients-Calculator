#!/usr/bin/env python3
"""
user_profiles.py – Multi-user profile storage and per-profile RDA computation.
"""

import json
import uuid
from pathlib import Path
from typing import Any

_PROFILES_FILE = Path(__file__).parent / "profiles.json"

# ── Default profile used when no profiles exist ───────────────────────────────
_DEFAULT_PROFILE: dict[str, Any] = {
    "id":          "default",
    "name":        "默认用户",
    "gender":      "male",    # "male" | "female"
    "age":         26,
    "weight_kg":   65.0,
    "height_cm":   175.0,
    "activity":    1.375,     # 1.2=久坐 1.375=轻度 1.55=中度 1.725=积极
}

# ── Persistent state ──────────────────────────────────────────────────────────
_profiles: dict[str, dict] = {}          # id → profile dict
_current_id: str = "default"


def _load() -> None:
    global _profiles, _current_id
    if not _PROFILES_FILE.exists():
        _profiles = {"default": dict(_DEFAULT_PROFILE)}
        _current_id = "default"
        return
    try:
        data = json.loads(_PROFILES_FILE.read_text(encoding="utf-8"))
        _profiles   = {p["id"]: p for p in data.get("profiles", [])}
        _current_id = data.get("current_id", next(iter(_profiles), "default"))
        if not _profiles:
            _profiles   = {"default": dict(_DEFAULT_PROFILE)}
            _current_id = "default"
    except Exception:
        _profiles   = {"default": dict(_DEFAULT_PROFILE)}
        _current_id = "default"


def _save() -> None:
    data = {
        "current_id": _current_id,
        "profiles":   list(_profiles.values()),
    }
    _PROFILES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# Eagerly load on import
_load()


# ── CRUD ──────────────────────────────────────────────────────────────────────

def list_profiles() -> list[dict]:
    return list(_profiles.values())


def get_profile(pid: str) -> dict | None:
    return _profiles.get(pid)


def get_current_profile() -> dict:
    return _profiles.get(_current_id, _profiles[next(iter(_profiles))])


def get_current_profile_id() -> str:
    return _current_id


def set_current_profile_id(pid: str) -> None:
    global _current_id
    if pid not in _profiles:
        raise KeyError(f"Profile '{pid}' not found")
    _current_id = pid
    _save()


def create_profile(name: str, gender: str = "male", age: int = 26,
                   weight_kg: float = 65.0, height_cm: float = 175.0,
                   activity: float = 1.375) -> dict:
    pid = str(uuid.uuid4())[:8]
    profile = {
        "id":         pid,
        "name":       name,
        "gender":     gender,
        "age":        age,
        "weight_kg":  weight_kg,
        "height_cm":  height_cm,
        "activity":   activity,
    }
    _profiles[pid] = profile
    _save()
    return profile


def update_profile(pid: str, **kwargs: Any) -> dict:
    if pid not in _profiles:
        raise KeyError(f"Profile '{pid}' not found")
    allowed = {"name", "gender", "age", "weight_kg", "height_cm", "activity"}
    for k, v in kwargs.items():
        if k in allowed:
            _profiles[pid][k] = v
    _save()
    return _profiles[pid]


def delete_profile(pid: str) -> None:
    global _current_id
    if pid == "default":
        raise ValueError("Cannot delete the default profile")
    if pid not in _profiles:
        raise KeyError(f"Profile '{pid}' not found")
    del _profiles[pid]
    if _current_id == pid:
        _current_id = next(iter(_profiles), "default")
    _save()


# ── RDA computation ───────────────────────────────────────────────────────────

def _bmr_for(p: dict) -> float:
    """Mifflin-St Jeor BMR (kcal/day)."""
    w, h, a = float(p["weight_kg"]), float(p["height_cm"]), int(p["age"])
    if p["gender"].lower() in ("male", "m", "男"):
        return 10 * w + 6.25 * h - 5 * a + 5
    return 10 * w + 6.25 * h - 5 * a - 161


def _tdee_for(p: dict) -> float:
    return _bmr_for(p) * float(p["activity"])


def compute_rda(key: str, profile: dict) -> float:
    """
    Return personalized daily RDA for `key` given a profile dict.
    Falls back to nutrients_data default if key is not personalized.
    """
    from nutrients_data import NUTRIENTS

    is_male = profile["gender"].lower() in ("male", "m", "男")
    tdee    = _tdee_for(profile)
    w       = float(profile["weight_kg"])

    overrides: dict[str, float] = {
        "protein":        0.83 * w,
        "fat":            tdee * 0.30 / 9,
        "carbohydrates":  max(130.0, tdee * 0.50 / 4),
        "fiber":          tdee / 1000.0 * 14.0,
        "vitamin_b1":     max(tdee / 1000.0 * 0.5,  1.2 if is_male else 1.1),
        "vitamin_b2":     max(tdee / 1000.0 * 0.6,  1.3 if is_male else 1.1),
        "vitamin_b3":     max(tdee / 1000.0 * 6.6, 16.0 if is_male else 14.0),
        "iron":           8.0   if is_male else 18.0,
        "zinc":           11.0  if is_male else 8.0,
        "magnesium":      420.0 if is_male else 320.0,
        "vitamin_c":      90.0  if is_male else 75.0,
        "vitamin_k":      120.0 if is_male else 90.0,
        "vitamin_a":      900.0 if is_male else 700.0,
        "potassium":      3400.0 if is_male else 2600.0,
        "omega3":         1.6   if is_male else 1.1,
    }
    if key in overrides:
        return overrides[key]
    if key in NUTRIENTS:
        return NUTRIENTS[key]["rda_per_day"]
    return 0.0
