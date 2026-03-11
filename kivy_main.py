#!/usr/bin/env python3
"""
kivy_main.py – Mobile (Kivy) UI for the Nutrient Intake Calculator.

Desktop testing : python kivy_main.py
Android build   : buildozer android debug deploy run
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# ── Kivy must be configured before any kivy import ───────────────────────────
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.app            import App
from kivy.clock          import Clock
from kivy.metrics        import dp
from kivy.utils          import get_color_from_hex
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label      import Label
from kivy.uix.button     import Button
from kivy.uix.textinput  import TextInput
from kivy.uix.spinner    import Spinner
from kivy.uix.popup      import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.togglebutton  import ToggleButton
from kivy.graphics       import Color, Rectangle, RoundedRectangle

# ── Colours (match desktop palette) ──────────────────────────────────────────
_HEX = {
    "bg":     "#f0f2f5", "white":  "#ffffff", "dark":   "#2c3e50",
    "green":  "#27ae60", "blue":   "#3498db", "red":    "#e74c3c",
    "grey":   "#7f8c8d", "orange": "#e67e22", "purple": "#8e44ad",
    "ok":     "#d4edda", "warn":   "#fff3cd", "bad":    "#f8d7da",
    "row_alt":"#f8f9fa",
}
_C = {k: get_color_from_hex(v) for k, v in _HEX.items()}

# ── Scoring nutrient keys (user-visible) ─────────────────────────────────────
SCORING_KEYS = [
    "protein", "fat", "carbohydrates", "fiber",
    "vitamin_a", "vitamin_c", "vitamin_d",
    "calcium", "iron", "potassium",
]
_KEY_NAMES = {
    "protein": "蛋白质", "fat": "脂肪", "carbohydrates": "碳水",
    "fiber": "膳食纤维", "vitamin_a": "维A", "vitamin_c": "维C",
    "vitamin_d": "维D", "calcium": "钙", "iron": "铁", "potassium": "钾",
}
_UNITS = {
    "protein": "g", "fat": "g", "carbohydrates": "g", "fiber": "g",
    "vitamin_a": "mcg", "vitamin_c": "mg", "vitamin_d": "mcg",
    "calcium": "mg", "iron": "mg", "potassium": "mg",
}


# ── Path patching (Android private storage) ───────────────────────────────────
def _patch_paths(data_dir: str) -> None:
    """Redirect all file I/O to the app's private data directory."""
    import nutrients_calculator as nc
    import user_profiles as up
    p = Path(data_dir)
    p.mkdir(parents=True, exist_ok=True)
    nc.INTAKE_LOG_FILE = p / "intake_log.jsonl"
    nc.OUTPUTS_DIR     = p / "outputs"
    nc.MEAL_INPUT_FILE = p / "meal_input.json"
    up._PROFILES_FILE  = p / "profiles.json"
    up._load()


# ── Per-profile RDA (no tkinter dependency) ───────────────────────────────────
def _get_rda(key: str) -> float:
    from user_profiles import get_current_profile, compute_rda
    return compute_rda(key, get_current_profile())


def _apply_profile(profile: dict) -> None:
    import nutrients_calculator as nc
    nc.GENDER    = profile["gender"]
    nc.AGE       = int(profile["age"])
    nc.WEIGHT_KG = float(profile["weight_kg"])
    nc.HEIGHT_CM = float(profile["height_cm"])
    nc.ACTIVITY  = float(profile["activity"])


# ── Shared widget helpers ─────────────────────────────────────────────────────
def _btn(text: str, hex_color: str, cb, height=None, font_size=None) -> Button:
    b = Button(
        text=text,
        background_color=get_color_from_hex(hex_color),
        background_normal="", background_down="",
        color=(1, 1, 1, 1),
        font_size=font_size or dp(14),
    )
    if height:
        b.size_hint_y = None
        b.height = height
    b.bind(on_release=cb)
    return b


def _with_bg(widget, hex_color: str):
    """Draw a solid background behind *widget*."""
    color = get_color_from_hex(hex_color)
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, "pos",  widget.pos),
                size=lambda *_: setattr(rect, "size", widget.size))
    return widget


class _Row(BoxLayout):
    """One horizontal data row."""
    def __init__(self, values, widths, bg_hex=None, **kw):
        super().__init__(orientation="horizontal",
                         size_hint_y=None, height=dp(38), **kw)
        if bg_hex:
            _with_bg(self, bg_hex)
        for val, w in zip(values, widths):
            lbl = Label(text=str(val), size_hint_x=w,
                        font_size=dp(13), color=(0.1, 0.1, 0.1, 1),
                        halign="center", valign="middle")
            lbl.bind(size=lbl.setter("text_size"))
            self.add_widget(lbl)


class _Header(_Row):
    def __init__(self, values, widths, **kw):
        super().__init__(values, widths, bg_hex=_HEX["dark"], **kw)
        for child in self.children:
            child.color = (1, 1, 1, 1)
            child.bold = True


def _scrollable_list():
    """Return (ScrollView, inner BoxLayout) pair."""
    sv = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation="vertical", size_hint_y=None, spacing=1)
    inner.bind(minimum_height=inner.setter("height"))
    sv.add_widget(inner)
    return sv, inner


def _confirm(title, msg, on_yes):
    content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
    content.add_widget(Label(text=msg, font_size=dp(15),
                             size_hint_y=None, height=dp(60)))
    row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
    popup = Popup(title=title, content=content,
                  size_hint=(0.88, None), height=dp(190))
    row.add_widget(_btn("确认", _HEX["red"],
                        lambda _: (popup.dismiss(), on_yes()), height=dp(44)))
    row.add_widget(_btn("取消", _HEX["grey"],
                        lambda _: popup.dismiss(), height=dp(44)))
    content.add_widget(row)
    popup.open()


# ══════════════════════════════════════════════════════════════════════════════
# Screen 1 — Record Meal
# ══════════════════════════════════════════════════════════════════════════════
class RecordMealScreen(Screen):
    def __init__(self, app_ref, **kw):
        super().__init__(name="record", **kw)
        self._app   = app_ref
        self._foods: list[dict] = []
        self._build()

    def _build(self):
        from food_database import FOOD_DB
        self._all_names = sorted(
            {n for e in FOOD_DB for n in e.get("names", [])})

        root = BoxLayout(orientation="vertical",
                         padding=dp(10), spacing=dp(6))
        _with_bg(root, _HEX["bg"])

        # Section: DB lookup
        root.add_widget(Label(text="从数据库添加食物", bold=True, font_size=dp(15),
                              size_hint_y=None, height=dp(28),
                              color=_C["dark"], halign="left"))

        row0 = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.food_input = TextInput(hint_text="食物名称", multiline=False,
                                    size_hint_x=0.42, font_size=dp(13))
        self.food_input.bind(text=self._filter_names)
        self.amt_input  = TextInput(hint_text="数量", text="100", multiline=False,
                                    input_filter="float", size_hint_x=0.2,
                                    font_size=dp(13))
        self.unit_sp = Spinner(values=["g", "ml", "l"], text="g",
                               size_hint_x=0.13, font_size=dp(12))
        row0.add_widget(self.food_input)
        row0.add_widget(self.amt_input)
        row0.add_widget(self.unit_sp)
        row0.add_widget(_btn("＋", _HEX["green"], self._add_from_db,
                             height=dp(44), font_size=dp(16)))
        root.add_widget(row0)

        # Autocomplete suggestions
        self.sugg = BoxLayout(orientation="vertical",
                              size_hint_y=None, height=0, spacing=1)
        root.add_widget(self.sugg)

        root.add_widget(_btn("✎ 手动填写营养素 (格式3 / 格式4)", _HEX["purple"],
                             self._open_manual, height=dp(44)))

        # Section: current meal
        root.add_widget(Label(text="本次餐食", bold=True, font_size=dp(15),
                              size_hint_y=None, height=dp(26),
                              color=_C["dark"], halign="left"))
        cols = ["食物", "量", "蛋白g", "脂肪g", "碳水g"]
        ws   = [0.33, 0.15, 0.17, 0.17, 0.18]
        root.add_widget(_Header(cols, ws))
        sv, self.meal_list = _scrollable_list()
        root.add_widget(sv)

        self.status_lbl = Label(text="", size_hint_y=None, height=dp(22),
                                font_size=dp(12), color=_C["green"])
        root.add_widget(self.status_lbl)

        btns = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        btns.add_widget(_btn("✓ 记录并保存", _HEX["green"],
                             self._submit, height=dp(52)))
        btns.add_widget(_btn("清空", _HEX["red"],
                             self._clear, height=dp(52)))
        root.add_widget(btns)
        self.add_widget(root)

    # ── Autocomplete ──────────────────────────────────────────────────────────
    def _filter_names(self, _inst, text):
        self.sugg.clear_widgets()
        if not text:
            self.sugg.height = 0
            return
        matches = [n for n in self._all_names if text.lower() in n.lower()][:5]
        self.sugg.height = dp(34) * len(matches)
        for name in matches:
            b = Button(text=name, size_hint_y=None, height=dp(34),
                       font_size=dp(13), background_color=_C["white"],
                       background_normal="", color=(0.1, 0.1, 0.1, 1))
            b.bind(on_release=lambda _b, n=name: (
                setattr(self.food_input, "text", n),
                self.sugg.clear_widgets(),
                setattr(self.sugg, "height", 0),
            ))
            self.sugg.add_widget(b)

    # ── Add from DB ───────────────────────────────────────────────────────────
    def _add_from_db(self, *_):
        from nutrients_calculator import _resolve_food
        name = self.food_input.text.strip()
        if not name:
            self.status_lbl.text = "请输入食物名称"
            return
        try:
            amount = float(self.amt_input.text or "100")
        except ValueError:
            self.status_lbl.text = "数量无效"
            return
        raw = {"name": name}
        u = self.unit_sp.text
        if u == "g":    raw["amount_g"]  = amount
        elif u == "ml": raw["amount_ml"] = amount
        else:           raw["amount_l"]  = amount
        resolved, note = _resolve_food(raw)
        self._foods.append(resolved)
        self._refresh_list()
        self.food_input.text = ""
        self.amt_input.text  = "100"
        self.status_lbl.text = f"✓ {note or name + ' 已添加'}"

    def _open_manual(self, *_):
        ManualEntryPopup(self._on_manual).open()

    def _on_manual(self, food_dict):
        from nutrients_calculator import _resolve_food
        resolved, _ = _resolve_food(food_dict)
        self._foods.append(resolved)
        self._refresh_list()
        self.status_lbl.text = f"✓ {food_dict.get('name', '?')} 已添加"

    def _refresh_list(self):
        from nutrients_calculator import compute_meal_totals
        self.meal_list.clear_widgets()
        ws = [0.33, 0.15, 0.17, 0.17, 0.18]
        for i, food in enumerate(self._foods):
            t   = compute_meal_totals([food])
            bg  = _HEX["white"] if i % 2 == 0 else _HEX["row_alt"]
            disp = food.get("_amount_display", "")
            self.meal_list.add_widget(_Row(
                [food.get("name", "?")[:12], disp,
                 f"{t['protein']:.1f}", f"{t['fat']:.1f}",
                 f"{t['carbohydrates']:.1f}"],
                ws, bg_hex=bg,
            ))

    def _submit(self, *_):
        if not self._foods:
            self.status_lbl.text = "请先添加食物"
            return
        from nutrients_calculator import compute_meal_totals, append_log
        totals = compute_meal_totals(self._foods)
        entry  = {
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "foods":        list(self._foods),
            "totals":       totals,
            "lookup_notes": [],
        }
        append_log(entry)
        self._app.show_info("已记录", f"餐食已保存！共 {len(self._foods)} 种食物。")
        self._clear()
        self._app.refresh_all()

    def _clear(self, *_):
        self._foods.clear()
        self.meal_list.clear_widgets()
        self.status_lbl.text = ""


# ══════════════════════════════════════════════════════════════════════════════
# Manual Entry Popup
# ══════════════════════════════════════════════════════════════════════════════
class ManualEntryPopup(Popup):
    _SHOW_KEYS = ["protein", "fat", "carbohydrates", "fiber",
                  "vitamin_a", "vitamin_c", "vitamin_d",
                  "calcium", "iron", "potassium", "sodium", "sugar"]

    def __init__(self, callback, **kw):
        self._callback = callback
        super().__init__(title="手动填写营养素",
                         size_hint=(0.96, 0.92), **kw)
        self._build()

    def _build(self):
        from nutrients_data import NUTRIENTS
        root = BoxLayout(orientation="vertical",
                         padding=dp(10), spacing=dp(8))

        # Name + format
        info_grid = GridLayout(cols=2, size_hint_y=None, height=dp(96), spacing=dp(6))
        info_grid.add_widget(Label(text="食物名称:", size_hint_x=0.3, font_size=dp(14)))
        self.v_name = TextInput(multiline=False, font_size=dp(14))
        info_grid.add_widget(self.v_name)
        info_grid.add_widget(Label(text="填写方式:", size_hint_x=0.3, font_size=dp(14)))
        self.fmt_sp = Spinner(
            values=["格式3 (每100g)", "格式4 (直接总量)"],
            text="格式3 (每100g)", font_size=dp(13))
        self.fmt_sp.bind(text=self._on_fmt)
        info_grid.add_widget(self.fmt_sp)
        root.add_widget(info_grid)

        # Amount row
        self.amt_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self.amt_row.add_widget(Label(text="摄入量:",
                                      size_hint_x=0.22, font_size=dp(13)))
        self.v_amt  = TextInput(text="100", multiline=False,
                                input_filter="float", size_hint_x=0.38,
                                font_size=dp(13))
        self.v_unit = Spinner(values=["g", "ml"], text="g",
                              size_hint_x=0.2, font_size=dp(12))
        self.amt_row.add_widget(self.v_amt)
        self.amt_row.add_widget(self.v_unit)
        self.amt_row.add_widget(Label(size_hint_x=0.2))
        root.add_widget(self.amt_row)

        # Nutrient grid
        sv   = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(4), padding=dp(4))
        grid.bind(minimum_height=grid.setter("height"))
        self._nutrient_inputs: dict[str, TextInput] = {}
        for key in self._SHOW_KEYS:
            if key not in NUTRIENTS:
                continue
            info = NUTRIENTS[key]
            grid.add_widget(Label(
                text=f"{info['name']} ({info['unit']}):",
                size_hint_y=None, height=dp(38), font_size=dp(12)))
            inp = TextInput(multiline=False, input_filter="float",
                            size_hint_y=None, height=dp(38), font_size=dp(13))
            grid.add_widget(inp)
            self._nutrient_inputs[key] = inp
        # Salt equivalent
        grid.add_widget(Label(text="食盐相当量 (g):",
                              size_hint_y=None, height=dp(38), font_size=dp(12)))
        self.v_salt = TextInput(multiline=False, input_filter="float",
                                size_hint_y=None, height=dp(38), font_size=dp(13))
        grid.add_widget(self.v_salt)
        sv.add_widget(grid)
        root.add_widget(sv)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        btns.add_widget(_btn("确认添加", _HEX["green"], self._ok, height=dp(50)))
        btns.add_widget(_btn("取消", _HEX["grey"],
                             lambda _: self.dismiss(), height=dp(50)))
        root.add_widget(btns)
        self.content = root

    def _on_fmt(self, _inst, val):
        self.amt_row.opacity = 0 if "格式4" in val else 1
        self.amt_row.disabled = "格式4" in val

    def _ok(self, *_):
        name = self.v_name.text.strip()
        if not name:
            return
        nutrients: dict[str, float] = {}
        for key, inp in self._nutrient_inputs.items():
            try:
                v = float(inp.text)
                if v:
                    nutrients[key] = v
            except (ValueError, TypeError):
                pass
        salt = self.v_salt.text.strip()
        if salt:
            try:
                nutrients["salt_equivalent"] = float(salt)
            except ValueError:
                pass
        food = {"name": name}
        if "格式4" in self.fmt_sp.text:
            food["nutrients_total"] = nutrients
        else:
            food["nutrients_per_100g"] = nutrients
            try:
                amt = float(self.v_amt.text)
            except ValueError:
                amt = 100.0
            if self.v_unit.text == "g":
                food["amount_g"] = amt
            else:
                food["amount_ml"] = amt
        self.dismiss()
        self._callback(food)


# ══════════════════════════════════════════════════════════════════════════════
# Screen 2 — Today's Status
# ══════════════════════════════════════════════════════════════════════════════
class StatusScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="status", **kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=dp(10), spacing=dp(6))
        _with_bg(root, _HEX["bg"])
        root.add_widget(Label(text="今日营养素达标进度", bold=True, font_size=dp(16),
                              size_hint_y=None, height=dp(30), color=_C["dark"]))
        root.add_widget(_Header(["营养素", "摄入量", "目标", "达标率"],
                                [0.30, 0.23, 0.23, 0.24]))
        sv, self.list_box = _scrollable_list()
        root.add_widget(sv)
        self.add_widget(root)

    def refresh(self):
        from nutrients_calculator import load_log, _parse_ts
        from nutrients_data import NUTRIENTS
        self.list_box.clear_widgets()
        log = load_log()
        today_str = datetime.now().strftime("%Y-%m-%d")
        totals: dict[str, float] = {}
        for entry in log:
            ts = _parse_ts(entry.get("timestamp", ""))
            if ts and ts.astimezone().strftime("%Y-%m-%d") == today_str:
                for k, v in entry.get("totals", {}).items():
                    totals[k] = totals.get(k, 0.0) + float(v)

        ws = [0.30, 0.23, 0.23, 0.24]
        for i, key in enumerate(SCORING_KEYS):
            if key not in NUTRIENTS:
                continue
            info   = NUTRIENTS[key]
            rda    = _get_rda(key)
            actual = totals.get(key, 0.0)
            pct    = (actual / rda * 100) if rda > 0 else 0.0
            unit   = _UNITS.get(key, "")

            def _fv(v, u=unit):
                return f"{v:.0f}{u}" if "mc" in u or "mg" in u else f"{v:.1f}{u}"

            if info.get("upper_limit"):
                bg     = _HEX["ok"]  if pct < 70 else (_HEX["warn"] if pct < 100 else _HEX["bad"])
                status = f"{'正常' if pct<70 else ('偏高' if pct<100 else '超标')} {pct:.0f}%"
            else:
                bg     = _HEX["ok"]  if pct >= 100 else (_HEX["warn"] if pct >= 70 else _HEX["bad"])
                status = f"{'达标' if pct>=100 else ('接近' if pct>=70 else '不足')} {pct:.0f}%"

            self.list_box.add_widget(
                _Row([info["name"][:9], _fv(actual), _fv(rda), status], ws,
                     bg_hex=bg if i % 2 == 0 else bg))


# ══════════════════════════════════════════════════════════════════════════════
# Screen 3 — Dish Recommendations
# ══════════════════════════════════════════════════════════════════════════════
class RecommendScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name="recommend", **kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=dp(10), spacing=dp(6))
        _with_bg(root, _HEX["bg"])
        root.add_widget(Label(text="今日推荐菜肴", bold=True, font_size=dp(16),
                              size_hint_y=None, height=dp(30), color=_C["dark"]))
        root.add_widget(Label(
            text="基于今日营养缺口推荐最优菜肴（双击可编辑数据）",
            font_size=dp(12), size_hint_y=None, height=dp(22),
            color=_C["grey"]))
        root.add_widget(_Header(["#", "菜名", "蛋白质", "热量kcal", "主要补充"],
                                [0.07, 0.22, 0.14, 0.14, 0.43]))
        sv, self.rec_list = _scrollable_list()
        root.add_widget(sv)

        # Gap summary section
        root.add_widget(Label(text="今日营养缺口", bold=True, font_size=dp(14),
                              size_hint_y=None, height=dp(26), color=_C["dark"]))
        root.add_widget(_Header(["营养素", "今日摄入", "目标", "缺口率%"],
                                [0.28, 0.24, 0.24, 0.24]))
        sv2, self.gap_list = _scrollable_list()
        sv2.size_hint_y = 0.4
        root.add_widget(sv2)
        self.add_widget(root)

    def refresh(self):
        from nutrients_calculator import load_log, _parse_ts
        from nutrients_data import ALL_NUTRIENT_KEYS
        from dish_recommender import recommend_dishes, compute_gaps
        self.rec_list.clear_widgets()
        self.gap_list.clear_widgets()

        log = load_log()
        today_str = datetime.now().strftime("%Y-%m-%d")
        today: dict[str, float] = {k: 0.0 for k in ALL_NUTRIENT_KEYS}
        for entry in log:
            ts = _parse_ts(entry.get("timestamp", ""))
            if ts and ts.astimezone().strftime("%Y-%m-%d") == today_str:
                for k in ALL_NUTRIENT_KEYS:
                    today[k] += float(entry.get("totals", {}).get(k, 0.0))

        recs = recommend_dishes(today, _get_rda, top_n=8)
        ws   = [0.07, 0.22, 0.14, 0.14, 0.43]
        for rank, r in enumerate(recs, 1):
            dish = r["dish"]
            n    = dish["nutrients"]
            top  = "、".join(
                f"{_KEY_NAMES.get(k,k)}+{p:.0f}%"
                for k, p in r["top_gaps_filled"])
            bg = _HEX["ok"] if rank == 1 else (
                 _HEX["warn"] if rank == 2 else _HEX["white"])
            self.rec_list.add_widget(_Row(
                [f"#{rank}", dish["name"][:8],
                 f"{n['protein']:.0f}g", f"~{n['kcal']:.0f}", top or "—"],
                ws, bg_hex=bg))

        # Gaps
        gaps = compute_gaps(today, _get_rda)
        gap_rows = [(k, gaps[k]) for k in SCORING_KEYS if gaps[k] > 0]
        gap_rows.sort(key=lambda x: x[1] / max(_get_rda(x[0]), 1), reverse=True)
        ws2 = [0.28, 0.24, 0.24, 0.24]
        for key, gap in gap_rows:
            rda    = _get_rda(key)
            actual = today.get(key, 0.0)
            pct    = gap / rda * 100 if rda > 0 else 0
            unit   = _UNITS.get(key, "")
            bg     = _HEX["bad"] if pct > 50 else (
                     _HEX["warn"] if pct > 20 else _HEX["ok"])
            self.gap_list.add_widget(_Row(
                [_KEY_NAMES.get(key, key),
                 f"{actual:.0f}{unit}", f"{rda:.0f}{unit}", f"{pct:.0f}%"],
                ws2, bg_hex=bg))


# ══════════════════════════════════════════════════════════════════════════════
# Screen 4 — History
# ══════════════════════════════════════════════════════════════════════════════
class HistoryScreen(Screen):
    def __init__(self, app_ref, **kw):
        super().__init__(name="history", **kw)
        self._app = app_ref
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=dp(10), spacing=dp(6))
        _with_bg(root, _HEX["bg"])
        top = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.count_lbl = Label(text="", font_size=dp(13),
                               size_hint_x=0.55, color=_C["dark"])
        top.add_widget(self.count_lbl)
        top.add_widget(_btn("⚠ 清空全部", _HEX["red"],
                            self._clear_all, height=dp(44)))
        root.add_widget(top)
        root.add_widget(
            _Header(["时间", "食物", "蛋白g", "脂肪g", "碳水g"],
                    [0.26, 0.34, 0.13, 0.13, 0.14]))
        sv, self.hist_list = _scrollable_list()
        root.add_widget(sv)
        self.add_widget(root)

    def refresh(self):
        from nutrients_calculator import load_log, _parse_ts
        self.hist_list.clear_widgets()
        log = load_log()
        self.count_lbl.text = f"共 {len(log)} 条记录"
        ws = [0.26, 0.34, 0.13, 0.13, 0.14]
        for i, entry in enumerate(reversed(log)):
            ts = _parse_ts(entry.get("timestamp", ""))
            ts_str = ts.astimezone().strftime("%m-%d %H:%M") if ts else "?"
            names  = "、".join(
                f.get("name", "?") for f in entry.get("foods", []))[:14]
            t = entry.get("totals", {})
            p, fat, carb = (t.get("protein", 0),
                            t.get("fat", 0), t.get("carbohydrates", 0))
            bg = _HEX["white"] if i % 2 == 0 else _HEX["row_alt"]
            self.hist_list.add_widget(
                _Row([ts_str, names,
                      f"{p:.0f}g", f"{fat:.0f}g", f"{carb:.0f}g"],
                     ws, bg_hex=bg))

    def _clear_all(self, *_):
        from nutrients_calculator import load_log
        count = len(load_log())
        if not count:
            self._app.show_info("提示", "记录已经是空的"); return
        _confirm("确认清空", f"清空全部 {count} 条记录？此操作不可撤销。",
                 on_yes=self._do_clear)

    def _do_clear(self):
        from nutrients_calculator import save_log
        save_log([])
        self.refresh()
        self._app.refresh_all()


# ══════════════════════════════════════════════════════════════════════════════
# Screen 5 — Profile
# ══════════════════════════════════════════════════════════════════════════════
class ProfileScreen(Screen):
    def __init__(self, app_ref, **kw):
        super().__init__(name="profile", **kw)
        self._app = app_ref
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=dp(14), spacing=dp(10))
        _with_bg(root, _HEX["bg"])
        root.add_widget(Label(text="用户档案管理", bold=True, font_size=dp(16),
                              size_hint_y=None, height=dp(30), color=_C["dark"]))

        # Info card
        card = BoxLayout(orientation="vertical", size_hint_y=None,
                         padding=dp(10), spacing=dp(3))
        _with_bg(card, _HEX["white"])
        self._lbl: dict[str, Label] = {}
        for field in ["姓名", "性别", "年龄", "体重", "身高", "活动量", "BMR", "TDEE"]:
            lbl = Label(text=f"{field}: —", font_size=dp(14),
                        size_hint_y=None, height=dp(24),
                        halign="left", color=(0.1, 0.1, 0.1, 1))
            lbl.bind(size=lbl.setter("text_size"))
            card.add_widget(lbl)
            self._lbl[field] = lbl
        card.height = dp(24) * 8 + dp(30)
        root.add_widget(card)

        # Switch profile
        sp_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        sp_row.add_widget(Label(text="切换用户:", size_hint_x=0.28,
                                font_size=dp(13)))
        self.sw_sp = Spinner(text="—", values=[], font_size=dp(13))
        self.sw_sp.bind(text=self._switch)
        sp_row.add_widget(self.sw_sp)
        root.add_widget(sp_row)

        btns = GridLayout(cols=2, size_hint_y=None, height=dp(100),
                          spacing=dp(8))
        btns.add_widget(_btn("✎ 编辑当前", _HEX["blue"],
                             self._edit, height=dp(46)))
        btns.add_widget(_btn("＋ 新建档案", _HEX["green"],
                             self._create, height=dp(46)))
        btns.add_widget(_btn("🗑 删除当前", _HEX["red"],
                             self._delete, height=dp(46)))
        btns.add_widget(Label())
        root.add_widget(btns)
        root.add_widget(Label())   # spacer
        self.add_widget(root)

    def refresh(self):
        from user_profiles import (get_current_profile, list_profiles,
                                   _bmr_for, _tdee_for)
        p  = get_current_profile()
        g  = "男" if p["gender"].lower() in ("male", "m") else "女"
        am = {1.2: "久坐", 1.375: "轻度活动", 1.55: "中度活动", 1.725: "积极"}
        vals = {
            "姓名": p["name"], "性别": g, "年龄": f"{p['age']} 岁",
            "体重": f"{p['weight_kg']} kg", "身高": f"{p['height_cm']} cm",
            "活动量": am.get(float(p["activity"]), str(p["activity"])),
            "BMR": f"≈{_bmr_for(p):.0f} kcal/天",
            "TDEE": f"≈{_tdee_for(p):.0f} kcal/天",
        }
        for field, lbl in self._lbl.items():
            lbl.text = f"{field}：{vals.get(field, '—')}"
        profiles = list_profiles()
        self.sw_sp.values = [p2["name"] for p2 in profiles]
        self.sw_sp.text   = p["name"]

    def _switch(self, _inst, name):
        from user_profiles import (list_profiles, set_current_profile_id,
                                   get_current_profile)
        for p in list_profiles():
            if p["name"] == name:
                try:
                    set_current_profile_id(p["id"])
                    _apply_profile(get_current_profile())
                    self.refresh()
                    self._app.refresh_all()
                except Exception:
                    pass
                break

    def _create(self, *_):
        ProfileEditPopup(None, self._saved).open()

    def _edit(self, *_):
        from user_profiles import get_current_profile
        ProfileEditPopup(get_current_profile(), self._saved).open()

    def _saved(self):
        self.refresh()
        self._app.refresh_all()

    def _delete(self, *_):
        from user_profiles import get_current_profile, delete_profile
        p = get_current_profile()
        if p["id"] == "default":
            self._app.show_info("提示", "默认档案不能删除。"); return
        _confirm("确认删除", f"删除档案 \"{p['name']}\"？",
                 on_yes=lambda: (delete_profile(p["id"]),
                                 self.refresh(), self._app.refresh_all()))


class ProfileEditPopup(Popup):
    _ACT_MAP = {"久坐": 1.2, "轻度": 1.375, "中度": 1.55, "积极": 1.725}
    _ACT_REV = {v: k for k, v in _ACT_MAP.items()}

    def __init__(self, profile, callback, **kw):
        self._profile  = profile
        self._callback = callback
        super().__init__(
            title="编辑档案" if profile else "新建档案",
            size_hint=(0.94, 0.82), **kw)
        self._build()

    def _build(self):
        p = self._profile
        root = BoxLayout(orientation="vertical",
                         padding=dp(12), spacing=dp(8))
        grid = GridLayout(cols=2, size_hint_y=None, spacing=dp(6))
        grid.bind(minimum_height=grid.setter("height"))

        def row(label, widget):
            grid.add_widget(Label(text=label, size_hint_y=None, height=dp(42),
                                  font_size=dp(14)))
            widget.size_hint_y = None
            widget.height = dp(42)
            grid.add_widget(widget)

        self.v_name   = TextInput(text=p["name"] if p else "",
                                  multiline=False, font_size=dp(14))
        self.v_age    = TextInput(text=str(p["age"]) if p else "26",
                                  multiline=False, input_filter="int",
                                  font_size=dp(14))
        self.v_weight = TextInput(text=str(p["weight_kg"]) if p else "65",
                                  multiline=False, input_filter="float",
                                  font_size=dp(14))
        self.v_height = TextInput(text=str(p["height_cm"]) if p else "175",
                                  multiline=False, input_filter="float",
                                  font_size=dp(14))
        self.v_gender = Spinner(
            text=("男" if p and p["gender"] in ("male","m") else "女") if p else "男",
            values=["男", "女"], font_size=dp(13))
        act_val = float(p["activity"]) if p else 1.375
        self.v_act = Spinner(
            text=self._ACT_REV.get(act_val, "轻度"),
            values=["久坐", "轻度", "中度", "积极"], font_size=dp(13))

        row("姓名",    self.v_name)
        row("性别",    self.v_gender)
        row("年龄",    self.v_age)
        row("体重 kg", self.v_weight)
        row("身高 cm", self.v_height)
        row("活动量",  self.v_act)

        sv = ScrollView(size_hint=(1, 1))
        sv.add_widget(grid)
        root.add_widget(sv)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        btns.add_widget(_btn("保存", _HEX["green"], self._save, height=dp(50)))
        btns.add_widget(_btn("取消", _HEX["grey"],
                             lambda _: self.dismiss(), height=dp(50)))
        root.add_widget(btns)
        self.content = root

    def _save(self, *_):
        from user_profiles import (create_profile, update_profile,
                                   get_current_profile, set_current_profile_id)
        gender = "male" if self.v_gender.text == "男" else "female"
        try:
            age    = int(self.v_age.text)
            weight = float(self.v_weight.text)
            height = float(self.v_height.text)
        except ValueError:
            return
        act = self._ACT_MAP.get(self.v_act.text, 1.375)
        if self._profile:
            update_profile(self._profile["id"], name=self.v_name.text,
                           gender=gender, age=age,
                           weight_kg=weight, height_cm=height, activity=act)
        else:
            p = create_profile(self.v_name.text, gender, age, weight, height, act)
            set_current_profile_id(p["id"])
        _apply_profile(get_current_profile())
        self.dismiss()
        self._callback()


# ══════════════════════════════════════════════════════════════════════════════
# Main App
# ══════════════════════════════════════════════════════════════════════════════
class NutrientKivyApp(App):
    def build(self):
        self.title = "营养摄入计算器"
        root = BoxLayout(orientation="vertical")
        _with_bg(root, _HEX["bg"])

        # Screen manager
        self.sm = ScreenManager(transition=FadeTransition(duration=0.1),
                                size_hint_y=1)
        self.s_record  = RecordMealScreen(self)
        self.s_status  = StatusScreen()
        self.s_reco    = RecommendScreen()
        self.s_history = HistoryScreen(self)
        self.s_profile = ProfileScreen(self)
        for s in [self.s_record, self.s_status, self.s_reco,
                  self.s_history, self.s_profile]:
            self.sm.add_widget(s)
        root.add_widget(self.sm)

        # Bottom tab bar
        tab_bar = BoxLayout(size_hint_y=None, height=dp(60))
        _with_bg(tab_bar, "#2c3e50")
        tabs = [
            ("📝\n记录", "record"),
            ("📈\n状态", "status"),
            ("🍽\n推荐", "recommend"),
            ("📋\n历史", "history"),
            ("👤\n档案", "profile"),
        ]
        self._tab_btns: list[ToggleButton] = []
        for label, sname in tabs:
            tb = ToggleButton(
                text=label, group="tabs", font_size=dp(11),
                background_color=get_color_from_hex("#34495e"),
                background_down="",
                background_normal="",
                color=(1, 1, 1, 1), halign="center",
            )
            tb.bind(on_release=lambda b, sn=sname: self._go(sn))
            tab_bar.add_widget(tb)
            self._tab_btns.append(tb)
        self._tab_btns[0].state = "down"
        root.add_widget(tab_bar)
        return root

    def on_start(self):
        _patch_paths(self.user_data_dir)
        from user_profiles import get_current_profile
        _apply_profile(get_current_profile())
        Clock.schedule_once(lambda _dt: self.refresh_all(), 0.3)

    def _go(self, screen_name: str):
        self.sm.current = screen_name
        s = self.sm.get_screen(screen_name)
        if hasattr(s, "refresh"):
            s.refresh()

    def refresh_all(self):
        for s in [self.s_status, self.s_reco, self.s_history, self.s_profile]:
            if hasattr(s, "refresh"):
                s.refresh()

    def show_info(self, title: str, msg: str):
        content = BoxLayout(orientation="vertical",
                            padding=dp(16), spacing=dp(10))
        content.add_widget(Label(text=msg, font_size=dp(15),
                                 size_hint_y=None, height=dp(60)))
        popup = Popup(title=title, content=content,
                      size_hint=(0.82, None), height=dp(190))
        content.add_widget(_btn("确定", _HEX["blue"],
                                lambda _: popup.dismiss(), height=dp(46)))
        popup.open()


def main():
    NutrientKivyApp().run()


if __name__ == "__main__":
    main()
