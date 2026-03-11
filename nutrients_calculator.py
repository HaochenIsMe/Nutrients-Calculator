#!/usr/bin/env python3
# nutrients_calculator.py
# Tracks human nutrient intake and reports deficiencies based on scientifically-appropriate time windows.

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure stdout/stderr use UTF-8 on all platforms (important on Windows GBK terminals)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from nutrients_data import ALL_NUTRIENT_KEYS, NUTRIENTS
from food_database import lookup_food

# ── File paths ────────────────────────────────────────────────────────────────
CWD = Path.cwd()
MEAL_INPUT_FILE = CWD / "meal_input.json"
INTAKE_LOG_FILE = CWD / "intake_log.jsonl"
OUTPUTS_DIR     = CWD / "outputs"

# ── Personal constants ────────────────────────────────────────────────────────
# Adjust these to match your body. RDA will be recalculated for your profile.
GENDER     = "male"   # "male" | "female"
AGE        = 26       # years
WEIGHT_KG  = 65.0     # kg
HEIGHT_CM  = 175.0    # cm
# Activity factor: 1.2=sedentary, 1.375=light exercise, 1.55=moderate, 1.725=active
ACTIVITY   = 1.375


def _bmr() -> float:
    """Mifflin-St Jeor BMR (kcal/day). Reference: Mifflin et al., JADA 1990."""
    w, h, a = WEIGHT_KG, HEIGHT_CM, AGE
    if GENDER.lower() in ("male", "m", "男"):
        return 10 * w + 6.25 * h - 5 * a + 5
    return 10 * w + 6.25 * h - 5 * a - 161


def _tdee() -> float:
    """Total daily energy expenditure = BMR × activity factor."""
    return _bmr() * ACTIVITY


def _personalized_rda() -> dict[str, float]:
    """
    Calculate individualized RDA overrides based on personal constants.

    Scientific basis:
    - Protein: WHO/FAO 2007 — 0.83 g/kg/day (minimum); linear with body weight.
    - Fat/Carbs/Fiber: IOM AMDR — % of TDEE; fiber 14g/1000 kcal (IOM DRI 2002).
    - B1/B2/B3: IOM — energy-dependent (0.5/0.6/6.6 per 1000 kcal); floor = gender RDA.
    - Gender-specific: Iron, Zinc, Magnesium, Vitamin C/K/A, B1/B2/B3, Potassium,
      Omega-3 — from IOM/WHO DRI tables for adults 19-50.
    Nutrients not listed here retain the values from nutrients_data.py.
    """
    is_male = GENDER.lower() in ("male", "m", "男")
    tdee = _tdee()

    rda: dict[str, float] = {}

    # Weight-proportional
    rda["protein"]      = 0.83 * WEIGHT_KG          # g/day (WHO 0.83 g/kg)

    # Energy-proportional (IOM DRI)
    rda["fat"]          = tdee * 0.30 / 9            # 30% of calories
    rda["carbohydrates"]= max(130.0, tdee * 0.50 / 4)# 50% of calories, min 130g
    rda["fiber"]        = tdee / 1000.0 * 14.0       # 14 g per 1000 kcal

    # B-vitamins (energy-dependent, with gender floor)
    rda["vitamin_b1"] = max(tdee / 1000.0 * 0.5,  1.2 if is_male else 1.1)
    rda["vitamin_b2"] = max(tdee / 1000.0 * 0.6,  1.3 if is_male else 1.1)
    rda["vitamin_b3"] = max(tdee / 1000.0 * 6.6, 16.0 if is_male else 14.0)

    # Gender-specific (IOM DRI for adults 19-50)
    rda["iron"]       = 8.0   if is_male else 18.0   # mg
    rda["zinc"]       = 11.0  if is_male else 8.0    # mg
    rda["magnesium"]  = 420.0 if is_male else 320.0  # mg
    rda["vitamin_c"]  = 90.0  if is_male else 75.0   # mg
    rda["vitamin_k"]  = 120.0 if is_male else 90.0   # mcg
    rda["vitamin_a"]  = 900.0 if is_male else 700.0  # mcg RAE
    rda["potassium"]  = 3400.0 if is_male else 2600.0 # mg
    rda["omega3"]     = 1.6   if is_male else 1.1    # g (ALA)

    return rda


def _get_rda(key: str) -> float:
    """Get personalized RDA for a nutrient key, falling back to nutrients_data value."""
    return _personalized_rda().get(key, NUTRIENTS[key]["rda_per_day"])

# ── Template format examples ──────────────────────────────────────────────────
_TEMPLATE_EXAMPLES = {
    "格式1_数据库查找": {
        "_说明": "只填名称和克重，程序自动查内置数据库（68种常见食物）",
        "name": "鸡胸肉",
        "amount_g": 150,
    },
    "格式2_液体食物": {
        "_说明": "液体用 amount_ml（毫升）或 amount_l（升），程序自动换算密度和营养",
        "name": "牛奶",
        "amount_ml": 250,
    },
    "格式3a_手动填写_每100g固体": {
        "_说明": "散装固体食物，填 amount_g（实际克数），nutrients_per_100g 为每100g含量",
        "name": "自定义食物",
        "amount_g": 100,
        "nutrients_per_100g": {k: 0.0 for k in ALL_NUTRIENT_KEYS},
    },
    "格式3b_手动填写_每Xml液体": {
        "_说明": "饮料/液体，填 amount_ml（实际毫升数）+ serving_ml（标签参考量，如200）",
        "name": "番茄汁",
        "amount_ml": 300,
        "serving_ml": 200,
        "nutrients_per_100g": {k: 0.0 for k in ALL_NUTRIENT_KEYS},
    },
    "格式3c_手动填写_每Xg固体": {
        "_说明": "标签以非100g为参考量时（如每28g），填 serving_g 覆盖默认的100",
        "name": "谷物棒",
        "amount_g": 56,
        "serving_g": 28,
        "nutrients_per_100g": {k: 0.0 for k in ALL_NUTRIENT_KEYS},
    },
    "格式4_产品标签_直接填总量": {
        "_说明": "直接填写产品营养表上的数值（本次份量的总量），不需要填重量",
        "name": "蛋白棒",
        "nutrients_total": {k: 0.0 for k in ALL_NUTRIENT_KEYS},
    },
}

# ── Formatting helpers ─────────────────────────────────────────────────────────

def _fmt(value: float, unit: str) -> str:
    match unit:
        case "g":        return f"{value:.1f}g"
        case "mg":       return f"{value:.1f}mg"
        case "mg_ne":    return f"{value:.1f}mg(NE)"
        case "mcg" | "mcg_rae" | "mcg_dfe": return f"{value:.1f}mcg"
        case _:          return f"{value:.1f}{unit}"


def _window_label(window_days: int) -> str:
    return "今日" if window_days == 1 else f"近{window_days}天"


def _has_user_nutrients(food: dict) -> bool:
    """Return True if the food has at least one explicitly set non-zero nutrient."""
    total_n = food.get("nutrients_total")
    if isinstance(total_n, dict) and any(v not in (None, 0, 0.0, "") for v in total_n.values()):
        return True
    per100 = food.get("nutrients_per_100g")
    if not isinstance(per100, dict) or not per100:
        return False
    return any(v not in (None, 0, 0.0, "") for v in per100.values())


def _resolve_food(food: dict) -> tuple[dict, str | None]:
    """
    Resolve one food entry:
    - If nutrients_total present: use as-is (product-label mode, no weight needed)
    - Convert amount_l → amount_ml → amount_g (using DB density for liquids)
    - If no user nutrients provided, fill from built-in food database
    Returns (resolved_food_dict, note_string_or_None)
    """
    food = dict(food)
    name = food.get("name", "?")

    # Format 4: product label — nutrients already totalled, skip all weight logic
    if isinstance(food.get("nutrients_total"), dict):
        food["_amount_display"] = "（产品标签）"
        return food, None

    # Look up DB (needed for both nutrients and liquid density)
    db_entry = lookup_food(name)
    density = db_entry.get("density_g_per_ml", 1.0) if db_entry else 1.0

    # Liquid volume → grams
    if "amount_l" in food and "amount_ml" not in food:
        food["amount_ml"] = float(food["amount_l"]) * 1000.0

    # Format 3 with serving_ml: user specifies ml consumed, no g conversion needed
    if "serving_ml" in food:
        food.setdefault("amount_ml", 0.0)
        food["_amount_display"] = f"{float(food['amount_ml']):.0f}ml"
    elif "amount_ml" in food and "amount_g" not in food:
        food["amount_g"] = float(food["amount_ml"]) * density
        food["_amount_display"] = f"{food['amount_ml']:.0f}ml"
    else:
        food.setdefault("amount_g", 0.0)
        food["_amount_display"] = f"{float(food['amount_g']):.0f}g"

    # Fill nutrients
    note = None
    if not _has_user_nutrients(food):
        if db_entry:
            food["nutrients_per_100g"] = db_entry["nutrients_per_100g"]
            liquid_tag = f"（液体，密度 {density}g/ml）" if db_entry.get("is_liquid") else ""
            note = f"📗 {name}{liquid_tag}：内置数据库"
        else:
            food["nutrients_per_100g"] = {k: 0.0 for k in ALL_NUTRIENT_KEYS}
            note = f"⚠ {name}：未在数据库中找到，营养素已置零，请手动填写"

    return food, note


def _parse_ts(ts_raw: str) -> datetime | None:
    try:
        ts = datetime.fromisoformat(ts_raw)
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


# ── Core calculation functions ─────────────────────────────────────────────────

def _apply_salt_equivalent(nutrients: dict) -> dict:
    """
    Convert salt_equivalent (g) → sodium (mg) if present.
    食盐相当量(g) × 400 = 钠(mg)  [WHO/GB 28050-2011]
    If both are provided, they are additive (unlikely but safe).
    """
    salt_g = float(nutrients.pop("salt_equivalent", 0.0) or 0.0)
    if salt_g:
        nutrients["sodium"] = float(nutrients.get("sodium", 0.0)) + salt_g * 400.0
    return nutrients


def compute_meal_totals(foods: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = {key: 0.0 for key in ALL_NUTRIENT_KEYS}
    for food in foods:
        if isinstance(food.get("nutrients_total"), dict):
            # Format 4: direct total values from product label
            n = _apply_salt_equivalent(dict(food["nutrients_total"]))
            for key in ALL_NUTRIENT_KEYS:
                totals[key] += float(n.get(key, 0.0))
        else:
            per_serving = _apply_salt_equivalent(dict(food.get("nutrients_per_100g") or {}))
            # serving_ml: label shows per N ml (e.g. per 200ml for a juice)
            # serving_g:  label shows per N g other than 100 (e.g. per 28g)
            # default:    per 100g
            if "serving_ml" in food:
                ref_ml = float(food["serving_ml"])
                amt_ml = float(food.get("amount_ml", 0.0))
                ratio  = amt_ml / ref_ml if ref_ml > 0 else 0.0
            else:
                ref_g  = float(food.get("serving_g", 100.0))
                amt_g  = float(food.get("amount_g", 0.0))
                ratio  = amt_g / ref_g if ref_g > 0 else 0.0
            for key in ALL_NUTRIENT_KEYS:
                totals[key] += float(per_serving.get(key, 0.0)) * ratio
    return totals


def get_window_intake(log: list[dict], nutrient_key: str, window_days: int) -> float:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    total = 0.0
    for entry in log:
        ts = _parse_ts(entry.get("timestamp", ""))
        if ts and ts >= cutoff:
            total += float(entry.get("totals", {}).get(nutrient_key, 0.0))
    return total


def _get_recent_foods(log: list[dict], days: int = 7) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = [e for e in log if (ts := _parse_ts(e.get("timestamp", ""))) and ts >= cutoff]
    recent.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return recent


# ── File I/O ──────────────────────────────────────────────────────────────────

def _create_template() -> None:
    template = {
        "_instructions": (
            "在 foods[] 中填入本次吃的食物，支持四种格式（见 _format_examples）：\n"
            "  格式1：只填 name + amount_g → 自动查内置数据库（68种常见食物）\n"
            "  格式2：液体用 amount_ml 或 amount_l → 自动换算密度\n"
            "  格式3：用 nutrients_per_100g 手动填写含量；固体默认每100g；液体加 serving_ml（如200）；非100g固体加 serving_g\n"
            "  格式4：用 nutrients_total 直接填产品标签上的总量，不需要填重量\n"
            "Run: python -X utf8 nutrients_calculator.py"
        ),
        "_format_examples": _TEMPLATE_EXAMPLES,
        "foods": [],
    }
    MEAL_INPUT_FILE.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  已创建模板文件 / Template created: {MEAL_INPUT_FILE}")
    print("  请填写 foods[] 后重新运行 / Fill in foods[] and run again.")


def load_log() -> list[dict]:
    if not INTAKE_LOG_FILE.exists():
        return []
    entries = []
    for line in INTAKE_LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def append_log(entry: dict) -> None:
    with INTAKE_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def save_log(entries: list[dict]) -> None:
    """Overwrite the log file with the given list of entries."""
    INTAKE_LOG_FILE.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + ("\n" if entries else ""),
        encoding="utf-8",
    )


# ── Meal processing ───────────────────────────────────────────────────────────

def process_meal_input() -> tuple[bool, dict | None]:
    if not MEAL_INPUT_FILE.exists():
        _create_template()
        return False, None

    try:
        data = json.loads(MEAL_INPUT_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"  错误 / Error: meal_input.json 解析失败 / parse failed: {exc}")
        return False, None

    raw_foods = [f for f in data.get("foods", []) if isinstance(f, dict)]

    if not raw_foods:
        print("  meal_input.json 中没有食物条目 / No food entries found.")
        return False, None

    resolved_foods, notes = [], []
    for food in raw_foods:
        resolved, note = _resolve_food(food)
        resolved_foods.append(resolved)
        if note:
            notes.append(note)

    totals = compute_meal_totals(resolved_foods)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "foods": resolved_foods,
        "totals": totals,
        "lookup_notes": notes,
    }
    return True, entry


# ── HTML report builder ───────────────────────────────────────────────────────

_CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
       background: #f0f2f5; color: #333; margin: 0; padding: 24px; }
.container { max-width: 980px; margin: 0 auto; }
h1 { color: #1a1a2e; border-bottom: 3px solid #3498db; padding-bottom: 12px; margin-bottom: 4px; }
h2 { color: #2c3e50; margin-top: 36px; margin-bottom: 12px; font-size: 1.15em; }
.meta { color: #888; font-size: 0.88em; margin-bottom: 24px; }

table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px;
        overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 20px; }
th { background: #2c3e50; color: white; padding: 11px 14px; text-align: left;
     font-weight: 600; font-size: 0.88em; }
td { padding: 9px 14px; border-bottom: 1px solid #f0f0f0; font-size: 0.88em; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #fafafa; }

.progress-wrap { width: 100%; background: #e9ecef; border-radius: 4px; height: 13px; }
.bar { height: 13px; border-radius: 4px; min-width: 2px; }
.green  { background: linear-gradient(90deg, #27ae60, #2ecc71); }
.yellow { background: linear-gradient(90deg, #e67e22, #f39c12); }
.red    { background: linear-gradient(90deg, #c0392b, #e74c3c); }

.badge { display:inline-block; padding:2px 9px; border-radius:12px;
         font-size:0.76em; font-weight:700; white-space:nowrap; }
.bg { background:#d4edda; color:#155724; }
.by { background:#fff3cd; color:#856404; }
.br { background:#f8d7da; color:#721c24; }

/* window-group section headers in status table */
.group-header td { background:#f0f4f8; color:#5a6a7a; font-size:0.8em;
                   font-weight:700; letter-spacing:0.04em; padding:6px 14px; }

.card { background:white; border-radius:8px; padding:18px 20px; margin-bottom:14px;
        box-shadow:0 1px 4px rgba(0,0,0,.08); border-left:4px solid #e74c3c; }
.card.warn { border-left-color:#f39c12; }
.card h3 { margin:0 0 6px 0; color:#2c3e50; font-size:1.05em; }
.mrow { display:flex; gap:18px; color:#666; font-size:0.88em; margin-bottom:8px; flex-wrap:wrap; }
.ftable { width:100%; border-collapse:collapse; }
.ftable th { background:#f8f9fa; color:#555; padding:7px 11px; text-align:left;
             font-weight:600; font-size:0.83em; border-bottom:2px solid #dee2e6; }
.ftable td { padding:6px 11px; border-bottom:1px solid #f5f5f5; font-size:0.86em; }
.ftable tr:last-child td { border-bottom:none; }
.eff { display:inline-block; height:7px; background:#3498db; border-radius:3px;
       vertical-align:middle; margin-left:6px; opacity:0.65; }
.meal-banner { background:#d4edda; border-left:4px solid #27ae60; border-radius:6px;
               padding:13px 18px; margin-bottom:20px; font-size:0.92em; }

/* unit conversion box */
.unit-box { background:white; border-radius:8px; padding:16px 20px;
            box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:20px; }
.unit-box table { box-shadow:none; margin-bottom:0; }
.unit-box th { background:#4a5568; }

/* disease section */
.disease-table { width:100%; border-collapse:collapse; background:white;
                 border-radius:8px; overflow:hidden;
                 box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:20px; }
.disease-table th { background:#7f1d1d; color:white; padding:10px 14px;
                    font-size:0.88em; font-weight:600; }
.disease-table td { padding:9px 14px; border-bottom:1px solid #f5f5f5;
                    font-size:0.86em; vertical-align:top; }
.disease-table tr:last-child td { border-bottom:none; }
.disease-table tr:hover td { background:#fef2f2; }
.dis-tag { display:inline-block; background:#fee2e2; color:#991b1b;
           border-radius:4px; padding:1px 7px; font-size:0.82em;
           margin:2px 3px 2px 0; }

/* window section dividers inside deficiency area */
.window-section-title { font-size:0.9em; font-weight:700; color:#4a5568;
                        background:#eef2f7; border-radius:6px;
                        padding:6px 14px; margin:20px 0 10px; }

/* previous period comparison */
.prev-card { background:white; border-radius:8px; padding:14px 18px; margin-bottom:12px;
             box-shadow:0 1px 4px rgba(0,0,0,.08); border-left:4px solid #e74c3c; }
.prev-card.prev-ok    { border-left-color:#27ae60; }
.prev-card.prev-empty { border-left-color:#dee2e6; padding:10px 18px; }
.prev-header { display:flex; align-items:baseline; gap:12px; margin-bottom:10px; }
.prev-label  { font-weight:700; color:#2c3e50; font-size:0.95em; }
.prev-date   { color:#888; font-size:0.85em; }
.prev-defs   { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }
.prev-ndef   { background:#fee2e2; color:#991b1b; border-radius:12px;
               padding:2px 10px; font-size:0.82em; white-space:nowrap; }
.prev-sug    { margin-top:8px; display:flex; flex-wrap:wrap; align-items:center;
               gap:6px; font-size:0.88em; }
.prev-food   { background:#dbeafe; color:#1e40af; border-radius:12px;
               padding:2px 10px; font-size:0.85em; white-space:nowrap; }
"""

def _recent_foods_html(recent: list[dict]) -> str:
    if not recent:
        return '<p style="color:#aaa;font-size:0.9em">近7天无摄入记录 / No entries in the last 7 days.</p>'
    rows = []
    for entry in recent:
        ts = _parse_ts(entry.get("timestamp", ""))
        ts_str = ts.astimezone().strftime("%m-%d %H:%M") if ts else "?"
        food_parts = []
        for f in entry.get("foods", []):
            disp = f.get("_amount_display") or f"{float(f.get('amount_g', 0)):.0f}g"
            food_parts.append(f"{f.get('name', '?')} {disp}")
        names = "、".join(food_parts)
        t = entry.get("totals", {})
        p, fat, carb = t.get("protein", 0), t.get("fat", 0), t.get("carbohydrates", 0)
        kcal = p * 4 + fat * 9 + carb * 4
        rows.append(
            f"<tr><td>{ts_str}</td><td>{names}</td>"
            f"<td>{p:.1f}g</td><td>{fat:.1f}g</td><td>{carb:.1f}g</td>"
            f"<td>~{kcal:.0f} kcal</td></tr>"
        )
    head = "<tr><th>时间</th><th>食物 (摄入量)</th><th>蛋白质</th><th>脂肪</th><th>碳水</th><th>估算热量</th></tr>"
    return f"<table><thead>{head}</thead><tbody>{''.join(rows)}</tbody></table>"


def _nutrients_table_html(stats: list[dict]) -> str:
    # Sort by time_window_days ascending (daily first), then by pct ascending within group
    sorted_stats = sorted(stats, key=lambda s: (s["window"], s["pct"]))

    _WINDOW_LABELS = {1: "每日 Daily", 7: "每周 Weekly", 14: "每两周 Bi-weekly", 30: "每月 Monthly"}
    rows = []
    current_window = None
    for s in sorted_stats:
        # Insert group header row when window changes
        if s["window"] != current_window:
            current_window = s["window"]
            label = _WINDOW_LABELS.get(current_window, f"近{current_window}天")
            rows.append(f"<tr class='group-header'><td colspan='6'>{label}</td></tr>")

        pct = s["pct"]
        bar_w = min(pct, 100)
        if pct >= 100:
            cls, bcls, btxt = "green", "bg", "✓ 达标"
        elif pct >= 70:
            cls, bcls, btxt = "yellow", "by", "~ 接近"
        else:
            cls, bcls, btxt = "red", "br", "✗ 不足"
        rows.append(
            f"<tr>"
            f"<td>{s['info']['name']}</td>"
            f"<td>{s['label']}</td>"
            f"<td>{_fmt(s['actual'], s['unit'])}</td>"
            f"<td>{_fmt(s['target'], s['unit'])}</td>"
            f"<td><div class='progress-wrap'><div class='bar {cls}' style='width:{bar_w:.1f}%'></div></div></td>"
            f"<td><span class='badge {bcls}'>{btxt} {pct:.0f}%</span></td>"
            f"</tr>"
        )
    head = ("<tr><th>营养素</th><th>时间窗口</th><th>摄入量</th>"
            "<th>目标</th><th style='min-width:110px'>进度</th><th>状态</th></tr>")
    return f"<table><thead>{head}</thead><tbody>{''.join(rows)}</tbody></table>"


def _deficiencies_html(deficient: list[dict]) -> str:
    if not deficient:
        return ('<p style="color:#27ae60;font-weight:600;font-size:1em">'
                '✓ 所有营养素均已达标！All nutrients meet targets!</p>')

    # Sort by time_window_days ascending, then pct ascending within group
    sorted_def = sorted(deficient, key=lambda s: (s["window"], s["pct"]))

    _GROUP_TITLES = {
        1:  "今日需补充 · Needed Today",
        7:  "本周建议补充 · Recommended This Week",
        14: "近两周建议补充 · Recommended This Fortnight",
        30: "本月建议补充 · Recommended This Month",
    }

    parts = []
    current_window = None
    for s in sorted_def:
        if s["window"] != current_window:
            current_window = s["window"]
            title = _GROUP_TITLES.get(current_window, f"近{current_window}天建议补充")
            parts.append(f"<div class='window-section-title'>{title}</div>")

        info, unit, pct = s["info"], s["unit"], s["pct"]
        deficit = s["target"] - s["actual"]
        card_cls = "card warn" if pct >= 70 else "card"

        # Food recommendations sorted ascending by grams_needed (fewest = most efficient = first)
        recs = []
        for src in info.get("sources", []):
            if src["per_100g"] > 0:
                recs.append((src["food"], src["per_100g"], deficit / src["per_100g"] * 100))
        recs.sort(key=lambda x: x[2])

        max_grams = max((r[2] for r in recs), default=1)
        frows = []
        for rank, (food_name, per_100g, grams_needed) in enumerate(recs, 1):
            eff_w = max(4, round((1 - grams_needed / max_grams) * 80 + 4))
            frows.append(
                f"<tr>"
                f"<td><strong>#{rank}</strong> {food_name}</td>"
                f"<td>{_fmt(per_100g, unit)}/100g</td>"
                f"<td><strong>~{grams_needed:.0f}g</strong>"
                f"<span class='eff' style='width:{eff_w}px'></span></td>"
                f"</tr>"
            )
        ftable = (
            "<table class='ftable'>"
            "<thead><tr><th>食物</th><th>每100g含量</th><th>需要摄入 ↑效率最高</th></tr></thead>"
            f"<tbody>{''.join(frows)}</tbody></table>"
            if frows else "<p style='color:#aaa;font-size:0.9em'>暂无推荐食物数据</p>"
        )
        parts.append(
            f"<div class='{card_cls}'>"
            f"<h3>{info['name']}</h3>"
            f"<div class='mrow'>"
            f"<span>窗口: {s['label']}</span>"
            f"<span>达标率: <strong>{pct:.0f}%</strong></span>"
            f"<span>还需摄入: <strong>{_fmt(deficit, unit)}</strong></span>"
            f"</div>"
            f"{ftable}"
            f"</div>"
        )
    return "\n".join(parts)


def _unit_conversion_html() -> str:
    rows = [
        ("质量单位 Weight", "1 g", "= 1,000 mg", "= 1,000,000 mcg (μg)"),
        ("", "1 mg", "= 0.001 g", "= 1,000 mcg (μg)"),
        ("", "1 mcg (μg)", "= 0.001 mg", "= 0.000001 g"),
        ("特殊单位 Special", "mcg RAE", "维生素A当量 Vitamin A Retinol Activity Equivalent", ""),
        ("", "mcg DFE", "叶酸当量 Dietary Folate Equivalent", ""),
        ("", "mg NE", "烟酸当量 Niacin Equivalent", ""),
    ]
    frows = "".join(
        f"<tr><td>{r[0]}</td><td><strong>{r[1]}</strong></td><td>{r[2]}</td><td>{r[3]}</td></tr>"
        for r in rows
    )
    head = "<tr><th>类别</th><th>单位</th><th>换算</th><th>备注</th></tr>"
    return (
        f"<div class='unit-box'>"
        f"<table><thead>{head}</thead><tbody>{frows}</tbody></table>"
        f"</div>"
    )


def _disease_risks_html(deficient: list[dict]) -> str:
    if not deficient:
        return ('<p style="color:#27ae60;font-weight:600">'
                '✓ 当前无缺乏营养素，继续保持！</p>')

    # Sort by time_window_days ascending
    sorted_def = sorted(deficient, key=lambda s: (s["window"], s["pct"]))
    rows = []
    for s in sorted_def:
        info, pct = s["info"], s["pct"]
        diseases = info.get("deficiency_diseases", [])
        tags = "".join(f"<span class='dis-tag'>{d}</span>" for d in diseases)
        urgency = "今日" if s["window"] == 1 else s["label"]
        rows.append(
            f"<tr>"
            f"<td><strong>{info['name']}</strong><br>"
            f"<span style='font-size:0.8em;color:#888'>{urgency}，达标率 {pct:.0f}%</span></td>"
            f"<td>{tags if tags else '<span style=\"color:#aaa\">—</span>'}</td>"
            f"</tr>"
        )
    head = "<tr><th style='width:30%'>缺乏营养素</th><th>可能引发的疾病 / Potential Deficiency Diseases</th></tr>"
    return (
        f"<table class='disease-table'>"
        f"<thead>{head}</thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        f"</table>"
        f"<p style='font-size:0.78em;color:#aaa;margin-top:4px'>"
        f"* 以上信息仅供参考，不构成医疗建议。如有健康疑虑请咨询医生。"
        f"</p>"
    )


# ── Previous period comparison ─────────────────────────────────────────────────

def _daily_totals(log: list[dict]) -> dict[str, dict[str, float]]:
    """Sum nutrient totals per calendar day (local time)."""
    by_date: dict[str, dict[str, float]] = {}
    for entry in log:
        ts = _parse_ts(entry.get("timestamp", ""))
        if not ts:
            continue
        date_str = ts.astimezone().strftime("%Y-%m-%d")
        t = entry.get("totals", {})
        if date_str not in by_date:
            by_date[date_str] = {k: 0.0 for k in ALL_NUTRIENT_KEYS}
        for k in ALL_NUTRIENT_KEYS:
            by_date[date_str][k] += float(t.get(k, 0.0))
    return by_date


def _find_prev_period(
    daily: dict[str, dict[str, float]], min_days_ago: int
) -> tuple[str, dict[str, float]] | None:
    """Return (date_str, totals) for the most recent date at least min_days_ago days before today."""
    today = datetime.now().date()
    cutoff = today - timedelta(days=min_days_ago)
    candidates = [d for d in daily if datetime.strptime(d, "%Y-%m-%d").date() <= cutoff]
    if not candidates:
        return None
    best = max(candidates)
    return best, daily[best]


def _day_deficiencies(day_totals: dict[str, float]) -> list[dict]:
    """Nutrients below daily RDA for a single day's totals."""
    result = []
    for key, info in NUTRIENTS.items():
        rda = _get_rda(key)
        if rda <= 0:
            continue
        actual = day_totals.get(key, 0.0)
        pct = actual / rda * 100
        if pct < 100:
            result.append({"key": key, "info": info, "actual": actual,
                           "rda": rda, "pct": pct, "unit": info["unit"]})
    return sorted(result, key=lambda x: x["pct"])


def _food_suggestions(deficiencies: list[dict]) -> list[str]:
    """Top food names ranked by how many deficient nutrients they cover."""
    coverage: dict[str, list[str]] = {}
    for d in deficiencies:
        for src in d["info"].get("sources", [])[:3]:
            coverage.setdefault(src["food"], []).append(d["info"]["name"])
    ranked = sorted(coverage.items(), key=lambda x: (-len(x[1]), x[0]))
    return [fn for fn, _ in ranked[:6]]


def _period_comparison_html(log: list[dict]) -> str:
    daily = _daily_totals(log)
    today_str = datetime.now().strftime("%Y-%m-%d")
    # Exclude today so "day" window always looks at a previous day
    daily_prev = {d: v for d, v in daily.items() if d != today_str}

    if not daily_prev:
        return '<p style="color:#aaa;font-size:0.9em">暂无历史数据，首次记录后此处将显示对比 / No prior history yet.</p>'

    PERIODS = [
        (1,  "上次 (天)",  "今天"),
        (7,  "上次 (周)",  "这周"),
        (30, "上次 (月)",  "本月"),
    ]

    parts = []
    for min_days, period_label, future_label in PERIODS:
        result = _find_prev_period(daily_prev, min_days)
        if result is None:
            parts.append(
                f"<div class='prev-card prev-empty'>"
                f"<span class='prev-label'>{period_label}</span>"
                f"&nbsp; <span style='color:#aaa'>暂无 {min_days} 天前的记录</span>"
                f"</div>"
            )
            continue

        date_str, day_totals = result
        days_ago = (datetime.now().date() - datetime.strptime(date_str, "%Y-%m-%d").date()).days
        deficiencies = _day_deficiencies(day_totals)

        if not deficiencies:
            parts.append(
                f"<div class='prev-card prev-ok'>"
                f"<div class='prev-header'>"
                f"<span class='prev-label'>{period_label}</span>"
                f"<span class='prev-date'>{date_str}（{days_ago}天前）</span>"
                f"</div>"
                f"<span style='color:#27ae60;font-weight:700'>✓ 当天全部营养素达标</span>"
                f"</div>"
            )
            continue

        shown = deficiencies[:8]
        def_badges = "".join(
            f"<span class='prev-ndef'>{d['info']['name']} <strong>{d['pct']:.0f}%</strong></span>"
            for d in shown
        )
        more_txt = (f" <span style='color:#aaa;font-size:0.82em'>…共{len(deficiencies)}项</span>"
                    if len(deficiencies) > 8 else "")

        suggestions = _food_suggestions(deficiencies)
        sug_html = ""
        if suggestions:
            chips = "".join(f"<span class='prev-food'>{fn}</span>" for fn in suggestions)
            sug_html = (f"<div class='prev-sug'>"
                        f"<span style='color:#555'>{future_label}可以主动吃：</span>{chips}"
                        f"</div>")

        parts.append(
            f"<div class='prev-card'>"
            f"<div class='prev-header'>"
            f"<span class='prev-label'>{period_label}</span>"
            f"<span class='prev-date'>{date_str}（{days_ago}天前）缺少：</span>"
            f"</div>"
            f"<div class='prev-defs'>{def_badges}{more_txt}</div>"
            f"{sug_html}"
            f"</div>"
        )

    return "\n".join(parts)


def generate_html_report(log: list[dict], new_entry: dict | None = None) -> Path:
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    date_dir = OUTPUTS_DIR / now.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    out_path = date_dir / f"report_{now.strftime('%H%M%S')}.html"

    # Compute stats for all nutrients (using personalized RDA)
    stats = []
    for key, info in NUTRIENTS.items():
        window = info["time_window_days"]
        target = _get_rda(key) * window
        actual = get_window_intake(log, key, window)
        pct    = (actual / target * 100) if target > 0 else 0.0
        stats.append({"key": key, "info": info, "window": window,
                       "target": target, "actual": actual, "pct": pct,
                       "unit": info["unit"], "label": _window_label(window)})

    deficient = sorted([s for s in stats if s["pct"] < 100.0], key=lambda s: s["pct"])
    recent    = _get_recent_foods(log, days=7)

    # Meal banner (only when a new meal was just logged)
    meal_banner = ""
    if new_entry:
        foods = new_entry.get("foods", [])
        t = new_entry.get("totals", {})
        p, fat, carb = t.get("protein", 0), t.get("fat", 0), t.get("carbohydrates", 0)
        food_parts = []
        for f in foods:
            disp = f.get("_amount_display") or f"{float(f.get('amount_g', 0)):.0f}g"
            food_parts.append(f"{f.get('name', '?')} {disp}")
        names = "、".join(food_parts)
        kcal = p * 4 + fat * 9 + carb * 4
        # Lookup notes (DB auto-fill / warnings)
        notes = new_entry.get("lookup_notes", [])
        notes_html = ""
        if notes:
            items = "".join(f"<li style='margin:1px 0'>{n}</li>" for n in notes)
            notes_html = f"<ul style='margin:6px 0 0 16px;padding:0;font-size:0.85em;color:#555'>{items}</ul>"
        meal_banner = (
            f"<div class='meal-banner'>"
            f"<strong>✓ 本次已记录 / Meal logged:</strong> {names}<br>"
            f"<span style='color:#555'>"
            f"蛋白质 {p:.1f}g &nbsp;·&nbsp; 脂肪 {fat:.1f}g &nbsp;·&nbsp; "
            f"碳水 {carb:.1f}g &nbsp;·&nbsp; 估算热量 ~{kcal:.0f} kcal"
            f"</span>"
            f"{notes_html}"
            f"</div>"
        )

    n_ok  = sum(1 for s in stats if s["pct"] >= 100)
    n_def = len(deficient)
    summary_color = "#27ae60" if n_def == 0 else ("#e67e22" if n_def <= 5 else "#e74c3c")
    summary_line = (
        f"<p style='font-size:0.9em;color:{summary_color}'>"
        f"<strong>{n_ok}/{len(stats)}</strong> 营养素达标 &nbsp;|&nbsp; "
        f"<strong>{n_def}</strong> 项不足</p>"
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>营养摄入报告 {now_str}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
  <h1>营养摄入报告 · Nutrient Intake Report</h1>
  <p class="meta">生成时间 / Generated: {now_str} &nbsp;|&nbsp; 日志: {INTAKE_LOG_FILE.name}</p>
  <p class="meta">档案 / Profile: {GENDER} &nbsp;·&nbsp; {AGE}岁 &nbsp;·&nbsp; {WEIGHT_KG}kg &nbsp;·&nbsp; {HEIGHT_CM}cm &nbsp;·&nbsp; BMR≈{_bmr():.0f} kcal &nbsp;·&nbsp; TDEE≈{_tdee():.0f} kcal</p>
  {meal_banner}
  {summary_line}

  <h2>上次摄入对比 · Previous Period Comparison</h2>
  {_period_comparison_html(log)}

  <h2>近期摄入食物 · Recent Intake（近7天）</h2>
  {_recent_foods_html(recent)}

  <h2>单位换算 · Unit Reference</h2>
  {_unit_conversion_html()}

  <h2>营养素达标状态 · Nutrient Status（共 {len(stats)} 项，按时间紧迫度排序）</h2>
  {_nutrients_table_html(stats)}

  <h2>缺乏营养素及补充建议 · Deficiencies & Recommendations（按时间紧迫度排序）</h2>
  {_deficiencies_html(deficient)}

  <h2>缺乏可能引发的疾病 · Potential Deficiency Diseases</h2>
  {_disease_risks_html(deficient)}
</div>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    return out_path


# ── History display (CLI only) ────────────────────────────────────────────────

def show_history(n: int = 10) -> None:
    log = load_log()
    if not log:
        print("  暂无记录 / No log entries found.")
        return
    entries = log[-n:]
    print(f"\n  最近 {n} 条记录 / Last {n} entries\n  " + "-" * 60)
    for i, entry in enumerate(entries, 1):
        ts = entry.get("timestamp", "unknown")
        names = ", ".join(f.get("name", "?") for f in entry.get("foods", []))
        t = entry.get("totals", {})
        p, fat, carb = t.get("protein", 0), t.get("fat", 0), t.get("carbohydrates", 0)
        print(f"  {i:>2}. [{ts[:19]}]  {names}")
        print(f"      蛋白质 {p:.1f}g · 脂肪 {fat:.1f}g · 碳水 {carb:.1f}g")
    print()


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="营养摄入计算器 / Nutrient Intake Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "用法 / Usage:\n"
            "  python nutrients_calculator.py              # 记录餐食并生成报告\n"
            "  python nutrients_calculator.py --status     # 仅生成报告（不读取输入）\n"
            "  python nutrients_calculator.py --history 5  # 显示最近5条记录\n"
        ),
    )
    parser.add_argument("--status",  action="store_true",
                        help="仅生成报告，不处理输入 / Generate report only")
    parser.add_argument("--history", nargs="?", const=10, type=int, metavar="N",
                        help="显示最近N条记录 / Show last N log entries (default 10)")
    args = parser.parse_args()

    if args.history is not None:
        show_history(args.history)
        return

    if args.status:
        log = load_log()
        path = generate_html_report(log)
        print(f"  报告已生成 / Report saved: {path}")
        return

    # Default: process meal input → log → report
    print("\n  营养摄入计算器 / Nutrient Intake Calculator\n  " + "-" * 60)
    success, entry = process_meal_input()

    if success and entry is not None:
        append_log(entry)
        names = "、".join(f.get("name", "?") for f in entry["foods"])
        print(f"  ✓ 已记录 {len(entry['foods'])} 种食物: {names}")
        print(f"  ✓ 已写入日志: {INTAKE_LOG_FILE}")
        log = load_log()
        path = generate_html_report(log, new_entry=entry)
    else:
        log = load_log()
        path = generate_html_report(log)

    print(f"  ✓ 报告已生成 / Report saved: {path}\n")


if __name__ == "__main__":
    main()
