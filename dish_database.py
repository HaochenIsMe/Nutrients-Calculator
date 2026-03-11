#!/usr/bin/env python3
"""
dish_database.py – Chinese home-cooking / restaurant dish database.

Each dish stores per-serving nutrient values for the 10 user-facing SCORING_KEYS
plus calories (kcal).  Values are approximate (USDA / Chinese nutritional tables).

Override any dish via dish_overrides.json in the same directory.
"""

import json
from pathlib import Path

_OVERRIDES_FILE = Path(__file__).parent / "dish_overrides.json"

# Keys stored per dish (11 user-visible nutrients + kcal)
DISH_NUTRIENT_KEYS = [
    "protein", "fat", "carbohydrates", "fiber",
    "vitamin_a", "vitamin_c", "vitamin_d",
    "calcium", "iron", "potassium",
    "kcal",
]


def _d(name: str, serving_desc: str,
       protein: float = 0, fat: float = 0, carbs: float = 0, fiber: float = 0,
       vit_a: float = 0, vit_c: float = 0, vit_d: float = 0,
       calcium: float = 0, iron: float = 0, potassium: float = 0,
       kcal: float | None = None) -> dict:
    """Helper to build a dish entry. kcal auto-computed if None."""
    if kcal is None:
        kcal = protein * 4 + fat * 9 + carbs * 4
    return {
        "name":         name,
        "serving_desc": serving_desc,
        "nutrients": {
            "protein":        protein,
            "fat":            fat,
            "carbohydrates":  carbs,
            "fiber":          fiber,
            "vitamin_a":      vit_a,
            "vitamin_c":      vit_c,
            "vitamin_d":      vit_d,
            "calcium":        calcium,
            "iron":           iron,
            "potassium":      potassium,
            "kcal":           kcal,
        },
    }


# ── Dish list ─────────────────────────────────────────────────────────────────
# ~60 Chinese home-cooking / restaurant dishes
# Serving sizes reflect typical single-person portions
_RAW_DISHES: list[dict] = [

    # ── 主食 Staples ──────────────────────────────────────────────────────────
    _d("白米饭",        "1碗 (200g熟饭)",
       protein=5.2, fat=0.5, carbs=58.0, fiber=0.4,
       potassium=56, calcium=10),
    _d("全麦馒头",      "1个 (100g)",
       protein=8.5, fat=1.2, carbs=44.0, fiber=4.2,
       calcium=30, iron=2.5, potassium=180),
    _d("白面条",        "1碗 (200g熟面)",
       protein=7.0, fat=1.0, carbs=50.0, fiber=1.8,
       calcium=18, iron=1.2, potassium=85),
    _d("全麦面条",      "1碗 (200g熟面)",
       protein=8.0, fat=1.5, carbs=46.0, fiber=5.0,
       calcium=24, iron=2.0, potassium=140),
    _d("小米粥",        "1碗 (250ml)",
       protein=3.0, fat=0.8, carbs=24.0, fiber=0.8,
       vit_a=8, iron=0.9, potassium=120),
    _d("玉米饼",        "1个 (80g)",
       protein=3.2, fat=2.0, carbs=26.0, fiber=2.5,
       calcium=14, iron=0.8, potassium=110),
    _d("蒸红薯",        "1个 (150g)",
       protein=2.0, fat=0.1, carbs=32.0, fiber=3.0,
       vit_a=960, vit_c=25, potassium=440),
    _d("炒饭 (蛋炒饭)", "1碗 (250g)",
       protein=9.5, fat=8.0, carbs=55.0, fiber=1.0,
       vit_a=100, calcium=40, iron=1.5, potassium=130),
    _d("饺子 (猪肉白菜)", "10个 (200g)",
       protein=14.0, fat=10.0, carbs=38.0, fiber=2.5,
       vit_c=12, calcium=45, iron=2.0, potassium=220),
    _d("包子 (肉包)",   "2个 (180g)",
       protein=12.0, fat=8.0, carbs=42.0, fiber=1.5,
       calcium=38, iron=1.8, potassium=180),

    # ── 荤菜 Meat dishes ──────────────────────────────────────────────────────
    _d("红烧肉",        "1份 (150g)",
       protein=18.0, fat=28.0, carbs=12.0, fiber=0.2,
       calcium=20, iron=1.5, potassium=280,
       kcal=380),
    _d("清蒸鱼 (鲈鱼)", "1条 (250g带骨)",
       protein=28.0, fat=5.0, carbs=1.0, fiber=0,
       vit_d=12.0, calcium=120, iron=1.2, potassium=450),
    _d("宫保鸡丁",      "1份 (200g)",
       protein=24.0, fat=14.0, carbs=12.0, fiber=1.5,
       vit_c=18, calcium=30, iron=1.8, potassium=380),
    _d("番茄炒蛋",      "1份 (200g)",
       protein=10.0, fat=9.0, carbs=10.0, fiber=1.5,
       vit_a=180, vit_c=22, calcium=55, iron=1.5, potassium=400),
    _d("青椒炒肉",      "1份 (200g)",
       protein=16.0, fat=12.0, carbs=6.0, fiber=2.0,
       vit_c=60, iron=1.5, potassium=340),
    _d("回锅肉",        "1份 (180g)",
       protein=20.0, fat=22.0, carbs=8.0, fiber=1.5,
       vit_c=30, calcium=25, iron=1.8, potassium=310),
    _d("水煮肉片",      "1份 (250g)",
       protein=28.0, fat=20.0, carbs=6.0, fiber=2.0,
       vit_c=15, calcium=35, iron=2.5, potassium=420),
    _d("糖醋里脊",      "1份 (200g)",
       protein=18.0, fat=12.0, carbs=28.0, fiber=0.5,
       calcium=20, iron=1.2, potassium=250),
    _d("红烧鸡腿",      "1只 (200g带骨)",
       protein=24.0, fat=14.0, carbs=6.0, fiber=0,
       vit_d=1.0, calcium=15, iron=1.2, potassium=320),
    _d("蒜泥白肉",      "1份 (150g)",
       protein=20.0, fat=18.0, carbs=4.0, fiber=0.5,
       calcium=18, iron=1.2, potassium=280),
    _d("鱼香肉丝",      "1份 (200g)",
       protein=18.0, fat=12.0, carbs=14.0, fiber=2.0,
       vit_c=20, vit_a=80, calcium=35, iron=1.8, potassium=350),
    _d("麻婆豆腐",      "1份 (250g)",
       protein=14.0, fat=10.0, carbs=8.0, fiber=1.5,
       calcium=250, iron=2.5, potassium=320),
    _d("蛋花汤",        "1碗 (300ml)",
       protein=6.0, fat=4.0, carbs=2.0, fiber=0,
       vit_a=90, calcium=30, iron=0.8, potassium=80),
    _d("虾仁炒蛋",      "1份 (200g)",
       protein=22.0, fat=8.0, carbs=3.0, fiber=0,
       vit_d=1.5, calcium=80, iron=1.2, potassium=280),
    _d("香煎三文鱼",    "1块 (150g)",
       protein=30.0, fat=14.0, carbs=0, fiber=0,
       vit_d=18.0, calcium=20, iron=0.8, potassium=560),
    _d("蒜蓉虾",        "1份 (200g带壳)",
       protein=18.0, fat=5.0, carbs=3.0, fiber=0,
       calcium=100, iron=1.5, potassium=300),

    # ── 素菜 Vegetable dishes ─────────────────────────────────────────────────
    _d("炒菠菜",        "1份 (200g)",
       protein=4.5, fat=4.0, carbs=5.0, fiber=3.5,
       vit_a=580, vit_c=30, calcium=110, iron=3.5, potassium=480),
    _d("清炒西兰花",    "1份 (200g)",
       protein=5.0, fat=3.0, carbs=8.0, fiber=3.5,
       vit_a=60, vit_c=110, calcium=80, iron=1.2, potassium=380),
    _d("炒白菜",        "1份 (200g)",
       protein=2.5, fat=3.0, carbs=5.0, fiber=2.0,
       vit_c=40, calcium=85, iron=0.8, potassium=250),
    _d("蒜炒空心菜",    "1份 (200g)",
       protein=3.0, fat=3.5, carbs=4.5, fiber=2.5,
       vit_c=28, vit_a=310, calcium=100, iron=1.8, potassium=310),
    _d("醋溜土豆丝",    "1份 (200g)",
       protein=3.0, fat=4.0, carbs=28.0, fiber=2.5,
       vit_c=28, potassium=500, calcium=12),
    _d("清炒豆芽",      "1份 (200g)",
       protein=4.5, fat=3.0, carbs=5.0, fiber=2.0,
       vit_c=15, calcium=28, iron=1.0, potassium=180),
    _d("番茄豆腐",      "1份 (250g)",
       protein=9.0, fat=5.0, carbs=8.0, fiber=1.5,
       vit_a=80, vit_c=18, calcium=200, iron=2.0, potassium=280),
    _d("凉拌黄瓜",      "1份 (200g)",
       protein=2.0, fat=1.5, carbs=5.0, fiber=1.5,
       vit_c=10, calcium=24, potassium=190),
    _d("炒胡萝卜",      "1份 (150g)",
       protein=1.5, fat=4.0, carbs=11.0, fiber=3.0,
       vit_a=960, vit_c=8, calcium=38, iron=0.6, potassium=300),
    _d("蒜炒茄子",      "1份 (200g)",
       protein=2.5, fat=5.0, carbs=10.0, fiber=3.5,
       vit_c=5, calcium=18, iron=0.6, potassium=280),
    _d("烧南瓜",        "1份 (200g)",
       protein=1.8, fat=2.0, carbs=16.0, fiber=2.5,
       vit_a=500, vit_c=12, calcium=28, potassium=340),
    _d("清炒荷兰豆",    "1份 (150g)",
       protein=4.5, fat=3.0, carbs=10.0, fiber=3.5,
       vit_c=55, vit_a=60, calcium=38, iron=1.5, potassium=220),
    _d("炒木耳",        "1份 (100g泡发)",
       protein=1.5, fat=2.5, carbs=7.0, fiber=6.5,
       calcium=30, iron=5.5, potassium=140),
    _d("凉拌木耳",      "1份 (100g泡发)",
       protein=1.5, fat=2.0, carbs=6.5, fiber=6.5,
       calcium=30, iron=5.0, potassium=140),

    # ── 汤 Soups ──────────────────────────────────────────────────────────────
    _d("番茄蛋花汤",    "1碗 (300ml)",
       protein=5.5, fat=3.5, carbs=7.0, fiber=1.0,
       vit_a=100, vit_c=18, calcium=38, iron=0.8, potassium=320),
    _d("排骨汤",        "1碗 (300ml)",
       protein=16.0, fat=10.0, carbs=2.0, fiber=0,
       calcium=65, iron=1.5, potassium=250),
    _d("冬瓜汤",        "1碗 (300ml)",
       protein=2.0, fat=2.0, carbs=4.0, fiber=1.0,
       vit_c=15, calcium=18, potassium=120),
    _d("紫菜蛋花汤",    "1碗 (300ml)",
       protein=5.5, fat=3.5, carbs=4.0, fiber=1.0,
       vit_a=90, calcium=50, iron=1.2, potassium=180),
    _d("豆腐汤",        "1碗 (300ml)",
       protein=8.0, fat=4.0, carbs=3.0, fiber=0.5,
       calcium=160, iron=1.5, potassium=150),
    _d("酸辣汤",        "1碗 (300ml)",
       protein=8.0, fat=5.0, carbs=10.0, fiber=1.0,
       calcium=50, iron=1.2, potassium=200),
    _d("玉米排骨汤",    "1碗 (300ml)",
       protein=14.0, fat=8.0, carbs=16.0, fiber=2.0,
       calcium=55, iron=1.2, potassium=300),

    # ── 凉菜 Cold dishes ──────────────────────────────────────────────────────
    _d("麻酱拌面",      "1碗 (200g熟面)",
       protein=10.0, fat=12.0, carbs=50.0, fiber=2.5,
       calcium=80, iron=2.0, potassium=200),
    _d("拍黄瓜",        "1份 (200g)",
       protein=1.5, fat=2.0, carbs=5.0, fiber=1.5,
       vit_c=10, potassium=190, calcium=22),
    _d("凉拌豆腐",      "1份 (200g)",
       protein=10.0, fat=5.0, carbs=3.5, fiber=0.5,
       calcium=240, iron=2.0, potassium=160),
    _d("凉拌菠菜",      "1份 (200g)",
       protein=4.0, fat=2.5, carbs=5.0, fiber=3.0,
       vit_a=560, vit_c=28, calcium=105, iron=3.0, potassium=460),
    _d("口水鸡",        "1份 (200g带骨)",
       protein=24.0, fat=12.0, carbs=5.0, fiber=0.5,
       calcium=18, iron=1.2, potassium=300),

    # ── 豆制品 Legumes ────────────────────────────────────────────────────────
    _d("红烧豆腐",      "1份 (200g)",
       protein=12.0, fat=7.0, carbs=6.0, fiber=0.8,
       calcium=260, iron=2.5, potassium=200),
    _d("毛豆",          "1碟 (100g)",
       protein=11.0, fat=5.5, carbs=9.0, fiber=4.0,
       vit_c=27, calcium=65, iron=2.7, potassium=480),
    _d("炒鸡蛋",        "2个炒蛋 (120g)",
       protein=13.0, fat=12.0, carbs=1.5, fiber=0,
       vit_a=240, vit_d=2.0, calcium=56, iron=1.8, potassium=130),
    _d("荷包蛋",        "2个 (120g)",
       protein=12.5, fat=10.0, carbs=1.2, fiber=0,
       vit_a=220, vit_d=2.0, calcium=55, iron=1.6, potassium=125),
]

# Patch: remove the vit_b12 key that slipped through in red-pork / also strip unknown keys
for _dish in _RAW_DISHES:
    _dish["nutrients"] = {k: v for k, v in _dish["nutrients"].items()
                          if k in DISH_NUTRIENT_KEYS}
    for k in DISH_NUTRIENT_KEYS:
        _dish["nutrients"].setdefault(k, 0.0)


# ── Override system ───────────────────────────────────────────────────────────

def _load_overrides() -> dict[str, dict]:
    if not _OVERRIDES_FILE.exists():
        return {}
    try:
        return json.loads(_OVERRIDES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_overrides(overrides: dict[str, dict]) -> None:
    _OVERRIDES_FILE.write_text(json.dumps(overrides, ensure_ascii=False, indent=2),
                               encoding="utf-8")


def save_dish_override(dish_name: str, nutrients: dict) -> None:
    """Persist custom nutrient values for a dish (merged on top of defaults)."""
    overrides = _load_overrides()
    overrides[dish_name] = {k: float(nutrients.get(k, 0)) for k in DISH_NUTRIENT_KEYS}
    _save_overrides(overrides)


def reset_dish_override(dish_name: str) -> None:
    overrides = _load_overrides()
    overrides.pop(dish_name, None)
    _save_overrides(overrides)


# ── Public API ────────────────────────────────────────────────────────────────

def _build_index() -> dict[str, dict]:
    overrides = _load_overrides()
    index: dict[str, dict] = {}
    for dish in _RAW_DISHES:
        name = dish["name"]
        effective = dict(dish)
        if name in overrides:
            effective = dict(dish)
            effective["nutrients"] = {**dish["nutrients"], **overrides[name]}
            effective["_overridden"] = True
        index[name] = effective
    return index


def get_dish(name: str) -> dict | None:
    """Return effective dish dict (applying overrides) or None if not found."""
    return _build_index().get(name)


def list_dishes() -> list[dict]:
    """Return all dishes (with overrides applied)."""
    return list(_build_index().values())


# Convenience: index rebuilt lazily on each call (overrides may change at runtime)
def DISH_INDEX() -> dict[str, dict]:
    return _build_index()
