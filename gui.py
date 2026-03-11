#!/usr/bin/env python3
"""
gui.py – Graphical interface for the Nutrient Intake Calculator.

Usage:  python -X utf8 gui.py
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from nutrients_data import ALL_NUTRIENT_KEYS, NUTRIENTS
from food_database import FOOD_DB
from nutrients_calculator import (
    load_log, append_log, save_log, generate_html_report,
    compute_meal_totals, _resolve_food, _parse_ts,
    OUTPUTS_DIR,
)
import nutrients_calculator as _nc
from user_profiles import (
    list_profiles, get_profile, get_current_profile, get_current_profile_id,
    set_current_profile_id, create_profile, update_profile, delete_profile,
    compute_rda, _bmr_for, _tdee_for,
)
from dish_recommender import recommend_dishes, compute_gaps, SCORING_KEYS
from dish_database import list_dishes, save_dish_override, reset_dish_override, DISH_NUTRIENT_KEYS


def _apply_profile(profile: dict) -> None:
    """Patch nutrients_calculator globals so RDA / reports use the active profile."""
    _nc.GENDER     = profile["gender"]
    _nc.AGE        = int(profile["age"])
    _nc.WEIGHT_KG  = float(profile["weight_kg"])
    _nc.HEIGHT_CM  = float(profile["height_cm"])
    _nc.ACTIVITY   = float(profile["activity"])


def _get_rda(key: str) -> float:
    """RDA for the currently active profile."""
    return compute_rda(key, get_current_profile())

# ── All food name strings for the combobox autocomplete ───────────────────────
_ALL_FOOD_NAMES: list[str] = sorted(
    {name for entry in FOOD_DB for name in entry.get("names", [])}
)

# ── Colour palette ─────────────────────────────────────────────────────────────
_C = {
    "bg":     "#f0f2f5",
    "white":  "#ffffff",
    "dark":   "#2c3e50",
    "green":  "#27ae60",
    "blue":   "#3498db",
    "red":    "#e74c3c",
    "grey":   "#7f8c8d",
    "orange": "#e67e22",
    "purple": "#8e44ad",
}

# ── Column-sort helper for ttk.Treeview ───────────────────────────────────────
def _make_sortable(tree: ttk.Treeview) -> None:
    """
    Bind heading clicks to toggle-sort on every column of *tree*.
    Numeric values (after stripping leading # ~ and trailing units) sort as float;
    everything else sorts as a case-insensitive string.
    A ▲ / ▼ indicator is appended to the active column heading.
    """
    _state: dict[str, object] = {"col": None, "asc": True}
    # Store original heading texts so we can restore them
    _orig: dict[str, str] = {c: tree.heading(c, "text") for c in tree["columns"]}

    def _sort(col: str) -> None:
        asc = not _state["asc"] if _state["col"] == col else True
        _state["col"] = col
        _state["asc"] = asc

        col_idx = list(tree["columns"]).index(col)
        rows = [(tree.set(iid, col), iid) for iid in tree.get_children()]

        def _key(val: str) -> tuple:
            # Strip decorators: leading #, ~, trailing units like g/mg/mcg/%/kcal/RDA
            clean = val.strip().lstrip("#~").split()[0].rstrip("g%")
            try:
                return (0, float(clean))
            except ValueError:
                return (1, val.lower())

        rows.sort(key=lambda x: _key(x[0]), reverse=not asc)
        for idx, (_, iid) in enumerate(rows):
            tree.move(iid, "", idx)

        # Update headings: restore all, then mark sorted column
        for c, orig in _orig.items():
            tree.heading(c, text=orig)
        arrow = " ▲" if asc else " ▼"
        tree.heading(col, text=_orig[col] + arrow)

    for col in tree["columns"]:
        tree.heading(col, command=lambda c=col: _sort(c))


# ── Tiny helper: coloured flat button ─────────────────────────────────────────
def _btn(parent, text, color, cmd, **kw) -> tk.Button:
    font = kw.pop("font", ("Segoe UI", 10))
    return tk.Button(
        parent, text=text, bg=color, fg=_C["white"],
        font=font, relief="flat",
        padx=kw.pop("padx", 16), pady=kw.pop("pady", 8),
        cursor="hand2", activebackground=color, activeforeground=_C["white"],
        command=cmd, **kw,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Dialog: User profile editor
# ══════════════════════════════════════════════════════════════════════════════
class ProfileDialog(tk.Toplevel):
    """Create or edit a user profile."""

    _ACTIVITY_LABELS = [
        ("1.2  久坐（几乎不运动）",    1.2),
        ("1.375 轻度（每周1-3次）",    1.375),
        ("1.55  中度（每周3-5次）",    1.55),
        ("1.725 积极（每天运动）",      1.725),
    ]

    def __init__(self, parent, profile: dict | None = None):
        super().__init__(parent)
        self.title("编辑用户档案" if profile else "创建用户档案")
        self.geometry("420x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._profile = profile
        self.result: dict | None = None
        self._build(profile)
        self.wait_window()

    def _build(self, p: dict | None):
        self.configure(bg=_C["bg"])
        f = ttk.Frame(self, padding=(20, 16))
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        def row(label, r):
            ttk.Label(f, text=label).grid(row=r, column=0, sticky="w",
                                           padx=(0, 10), pady=6)

        row("姓名", 0);        self.v_name    = tk.StringVar(value=p["name"]        if p else "新用户")
        row("性别", 1);        self.v_gender  = tk.StringVar(value=p["gender"]      if p else "male")
        row("年龄", 2);        self.v_age     = tk.StringVar(value=str(p["age"])    if p else "26")
        row("体重 (kg)", 3);   self.v_weight  = tk.StringVar(value=str(p["weight_kg"])  if p else "65")
        row("身高 (cm)", 4);   self.v_height  = tk.StringVar(value=str(p["height_cm"])  if p else "175")
        row("活动量", 5)

        ttk.Entry(f, textvariable=self.v_name,   width=22).grid(row=0, column=1, sticky="ew")
        gf = ttk.Frame(f); gf.grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(gf, text="男", variable=self.v_gender, value="male").pack(side="left")
        ttk.Radiobutton(gf, text="女", variable=self.v_gender, value="female").pack(side="left", padx=(12,0))
        ttk.Entry(f, textvariable=self.v_age,    width=8).grid(row=2, column=1, sticky="w")
        ttk.Entry(f, textvariable=self.v_weight, width=8).grid(row=3, column=1, sticky="w")
        ttk.Entry(f, textvariable=self.v_height, width=8).grid(row=4, column=1, sticky="w")

        act_val = float(p["activity"]) if p else 1.375
        self.v_act = tk.DoubleVar(value=act_val)
        act_cb = ttk.Combobox(f, textvariable=self.v_act,
                              values=[lbl for lbl, _ in self._ACTIVITY_LABELS],
                              state="readonly", width=28)
        # Set display
        for lbl, val in self._ACTIVITY_LABELS:
            if abs(val - act_val) < 0.01:
                act_cb.set(lbl); break
        act_cb.grid(row=5, column=1, sticky="ew")
        self._act_cb = act_cb

        bf = ttk.Frame(f)
        bf.grid(row=6, column=0, columnspan=2, pady=(18, 0), sticky="w")
        _btn(bf, "保存", _C["green"], self._ok, padx=18, pady=7).pack(side="left")
        _btn(bf, "取消", _C["grey"],  self.destroy, padx=12, pady=7).pack(side="left", padx=(10,0))

    def _ok(self):
        name = self.v_name.get().strip()
        if not name:
            messagebox.showwarning("提示", "请填写姓名", parent=self); return
        try:
            age    = int(self.v_age.get())
            weight = float(self.v_weight.get())
            height = float(self.v_height.get())
        except ValueError:
            messagebox.showwarning("提示", "年龄/体重/身高必须是数字", parent=self); return

        sel = self._act_cb.get()
        act = 1.375
        for lbl, val in self._ACTIVITY_LABELS:
            if lbl == sel:
                act = val; break

        self.result = {
            "name": name, "gender": self.v_gender.get(),
            "age": age, "weight_kg": weight,
            "height_cm": height, "activity": act,
        }
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# Dialog: Dish nutrient editor
# ══════════════════════════════════════════════════════════════════════════════
class DishEditorDialog(tk.Toplevel):
    """Edit and save the nutrient override for a single dish."""

    _LABELS = {
        "protein": "蛋白质 (g)", "fat": "脂肪 (g)", "carbohydrates": "碳水 (g)",
        "fiber": "膳食纤维 (g)", "vitamin_a": "维生素A (mcg)",
        "vitamin_c": "维生素C (mg)", "vitamin_d": "维生素D (mcg)",
        "calcium": "钙 (mg)", "iron": "铁 (mg)", "potassium": "钾 (mg)",
        "kcal": "热量 (kcal)",
    }

    def __init__(self, parent, dish: dict):
        super().__init__(parent)
        self.title(f"编辑菜肴：{dish['name']}")
        self.geometry("360x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._dish = dish
        self.saved = False
        self._build()
        self.wait_window()

    def _build(self):
        self.configure(bg=_C["bg"])
        f = ttk.Frame(self, padding=(18, 14))
        f.pack(fill="both", expand=True)
        f.columnconfigure(1, weight=1)

        ttk.Label(f, text=f"份量：{self._dish['serving_desc']}",
                  foreground="#666", font=("Segoe UI", 8)).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._vars: dict[str, tk.StringVar] = {}
        nutrients = self._dish.get("nutrients", {})
        for i, key in enumerate(DISH_NUTRIENT_KEYS, 1):
            label = self._labels(key)
            ttk.Label(f, text=label).grid(row=i, column=0, sticky="w", pady=3, padx=(0,8))
            var = tk.StringVar(value=str(nutrients.get(key, 0.0)))
            ttk.Entry(f, textvariable=var, width=12).grid(row=i, column=1, sticky="w")
            self._vars[key] = var

        bf = ttk.Frame(f)
        bf.grid(row=len(DISH_NUTRIENT_KEYS)+2, column=0, columnspan=2, pady=(14, 0), sticky="w")
        _btn(bf, "保存修改", _C["green"],  self._save,  padx=16, pady=7).pack(side="left")
        _btn(bf, "恢复默认", _C["orange"], self._reset, padx=12, pady=7).pack(side="left", padx=(8,0))
        _btn(bf, "取消",     _C["grey"],   self.destroy,padx=12, pady=7).pack(side="left", padx=(8,0))

    def _labels(self, key: str) -> str:
        return self._LABELS.get(key, key)

    def _save(self):
        nutrients: dict[str, float] = {}
        for key, var in self._vars.items():
            try:
                nutrients[key] = float(var.get())
            except ValueError:
                messagebox.showwarning("提示", f"\"{self._labels(key)}\" 的值无效", parent=self)
                return
        save_dish_override(self._dish["name"], nutrients)
        self.saved = True
        messagebox.showinfo("已保存", f"菜肴 \"{self._dish['name']}\" 的营养数据已更新。", parent=self)
        self.destroy()

    def _reset(self):
        if messagebox.askyesno("确认", f"恢复 \"{self._dish['name']}\" 为内置默认值？", parent=self):
            reset_dish_override(self._dish["name"])
            self.saved = True
            self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# Dialog: Manual nutrient entry (Format 3 / Format 4)
# ══════════════════════════════════════════════════════════════════════════════
class ManualNutrientDialog(tk.Toplevel):
    """
    Let the user manually enter nutrient values for a food item.

    Format 3  – per-100g/ml label, user enters actual consumed amount.
                 Optionally specify serving_g / serving_ml if the label
                 reference is not 100g/ml.
    Format 4  – direct totals (product already gave total amounts).
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("手动填写营养素  Manual Entry")
        self.geometry("600x640")
        self.minsize(540, 480)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.result: dict | None = None
        self._build()
        self.wait_window()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build(self):
        self.configure(bg=_C["bg"])

        # ── Top: name + format ────────────────────────────────────────────────
        top = ttk.LabelFrame(self, text="基本信息", padding=(12, 8))
        top.pack(fill="x", padx=12, pady=(12, 6))
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="食物名称").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.v_name = tk.StringVar()
        ttk.Entry(top, textvariable=self.v_name, width=28).grid(
            row=0, column=1, columnspan=3, sticky="ew")

        ttk.Label(top, text="填写方式").grid(row=1, column=0, sticky="w",
                                             padx=(0, 8), pady=(10, 0))
        fmt_f = ttk.Frame(top)
        fmt_f.grid(row=1, column=1, columnspan=3, sticky="w", pady=(10, 0))
        self.v_fmt = tk.StringVar(value="3")
        ttk.Radiobutton(fmt_f, text="格式3：每100g/ml 成分表",
                        variable=self.v_fmt, value="3",
                        command=self._on_fmt_change).pack(side="left")
        ttk.Radiobutton(fmt_f, text="格式4：直接填总量",
                        variable=self.v_fmt, value="4",
                        command=self._on_fmt_change).pack(side="left", padx=(20, 0))

        # ── Amount row (hidden for format 4) ──────────────────────────────────
        self.amt_frame = ttk.Frame(top)
        self.amt_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        ttk.Label(self.amt_frame, text="实际摄入量").pack(side="left")
        self.v_amount = tk.StringVar(value="100")
        ttk.Entry(self.amt_frame, textvariable=self.v_amount, width=9).pack(
            side="left", padx=(6, 4))
        self.v_unit = tk.StringVar(value="g")
        ttk.Combobox(self.amt_frame, textvariable=self.v_unit,
                     values=["g", "ml"], width=5,
                     state="readonly").pack(side="left", padx=(0, 20))

        ttk.Label(self.amt_frame, text="标签参考量（留空=100）").pack(side="left")
        self.v_serving = tk.StringVar()
        ttk.Entry(self.amt_frame, textvariable=self.v_serving, width=7).pack(
            side="left", padx=(4, 0))
        ttk.Label(self.amt_frame, text="g/ml", foreground="#888").pack(side="left", padx=(2, 0))

        # ── Scrollable nutrient form ───────────────────────────────────────────
        nf_outer = ttk.LabelFrame(self, text="营养成分  Nutrients", padding=(8, 6))
        nf_outer.pack(fill="both", expand=True, padx=12, pady=4)

        canvas = tk.Canvas(nf_outer, bg=_C["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(nf_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._nf = ttk.Frame(canvas)
        _win = canvas.create_window((0, 0), window=self._nf, anchor="nw")

        def _on_frame_resize(_e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_resize(e):
            canvas.itemconfig(_win, width=e.width)

        self._nf.bind("<Configure>", _on_frame_resize)
        canvas.bind("<Configure>", _on_canvas_resize)
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1 * e.delta / 120), "units"))

        # Build two-column grid of nutrient fields
        self.nutrient_vars: dict[str, tk.StringVar] = {}
        entries = list(NUTRIENTS.items())
        for i, (key, info) in enumerate(entries):
            col = (i % 2) * 3
            row = i // 2
            label = f"{info['name']}  ({info['unit']})"
            ttk.Label(self._nf, text=label, font=("Segoe UI", 8)).grid(
                row=row, column=col, sticky="w", padx=(8 if col else 4, 4), pady=2)
            var = tk.StringVar(value="")
            ttk.Entry(self._nf, textvariable=var, width=10).grid(
                row=row, column=col + 1, padx=(0, 12), pady=2)
            self.nutrient_vars[key] = var

        # ── Salt equivalent special field ─────────────────────────────────────
        salt_f = ttk.LabelFrame(self, text="食盐相当量  Salt Equivalent (特殊换算字段)",
                                padding=(12, 6))
        salt_f.pack(fill="x", padx=12, pady=(0, 4))
        ttk.Label(salt_f,
                  text="食盐相当量 (g) × 400 = 钠 (mg)。填此字段后无需重复填钠。",
                  foreground="#555", font=("Segoe UI", 8)).pack(anchor="w")
        salt_row = ttk.Frame(salt_f)
        salt_row.pack(anchor="w", pady=(4, 0))
        ttk.Label(salt_row, text="食盐相当量 (g)").pack(side="left")
        self.v_salt = tk.StringVar()
        ttk.Entry(salt_row, textvariable=self.v_salt, width=10).pack(
            side="left", padx=(6, 0))

        # ── Buttons ────────────────────────────────────────────────────────────
        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=12, pady=(6, 12))
        _btn(bf, "确认添加", _C["green"], self._ok, padx=20, pady=8).pack(side="left")
        _btn(bf, "取消", _C["grey"], self.destroy, padx=14, pady=8).pack(
            side="left", padx=(10, 0))
        ttk.Label(bf, text="空白字段视为 0", foreground="#aaa",
                  font=("Segoe UI", 8)).pack(side="right")

    def _on_fmt_change(self):
        if self.v_fmt.get() == "4":
            self.amt_frame.grid_remove()
        else:
            self.amt_frame.grid()

    def _ok(self):
        name = self.v_name.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入食物名称", parent=self)
            return

        # Collect non-zero nutrient values
        nutrients: dict[str, float] = {}
        for key, var in self.nutrient_vars.items():
            raw = var.get().strip()
            if not raw:
                continue
            try:
                v = float(raw)
            except ValueError:
                messagebox.showwarning("提示", f"营养素 '{key}' 的值无效：{raw!r}", parent=self)
                return
            if v != 0.0:
                nutrients[key] = v

        # Optional salt_equivalent
        salt_raw = self.v_salt.get().strip()
        if salt_raw:
            try:
                salt_val = float(salt_raw)
                if salt_val != 0.0:
                    nutrients["salt_equivalent"] = salt_val
            except ValueError:
                messagebox.showwarning("提示", "食盐相当量格式不正确", parent=self)
                return

        food: dict = {"name": name}
        fmt = self.v_fmt.get()

        if fmt == "4":
            food["nutrients_total"] = nutrients
        else:
            food["nutrients_per_100g"] = nutrients
            # Amount consumed
            try:
                amt = float(self.v_amount.get())
            except ValueError:
                messagebox.showwarning("提示", "实际摄入量格式不正确", parent=self)
                return
            unit = self.v_unit.get()
            if unit == "g":
                food["amount_g"] = amt
            else:
                food["amount_ml"] = amt
            # Optional serving reference
            srv_raw = self.v_serving.get().strip()
            if srv_raw:
                try:
                    srv = float(srv_raw)
                    if unit == "ml":
                        food["serving_ml"] = srv
                    else:
                        food["serving_g"] = srv
                except ValueError:
                    messagebox.showwarning("提示", "标签参考量格式不正确", parent=self)
                    return

        self.result = food
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
class NutrientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("营养摄入计算器 · Nutrient Tracker")
        self.geometry("1020x760")
        self.minsize(860, 620)
        self.configure(bg=_C["bg"])
        self._setup_style()

        # Apply current profile to nutrients_calculator globals
        _apply_profile(get_current_profile())

        # State
        self.meal_foods: list[dict] = []   # resolved food dicts for current meal

        self._build_ui()

    # ── Styling ────────────────────────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame",          background=_C["bg"])
        s.configure("TLabel",          background=_C["bg"], font=("Segoe UI", 9))
        s.configure("TEntry",          font=("Segoe UI", 9))
        s.configure("TCombobox",       font=("Segoe UI", 9))
        s.configure("TLabelframe",     background=_C["bg"])
        s.configure("TLabelframe.Label",
                    background=_C["bg"], foreground=_C["dark"],
                    font=("Segoe UI", 9, "bold"))
        s.configure("TNotebook",       background=_C["bg"])
        s.configure("TNotebook.Tab",   padding=[14, 7], font=("Segoe UI", 10))
        s.map("TNotebook.Tab",         background=[("selected", _C["white"])])
        s.configure("Treeview",        rowheight=26, font=("Segoe UI", 9),
                    background=_C["white"], fieldbackground=_C["white"])
        s.configure("Treeview.Heading",
                    font=("Segoe UI", 9, "bold"),
                    background="#4a5568", foreground=_C["white"])
        s.map("Treeview.Heading", background=[("active", _C["dark"])])

    # ── Profile bar ────────────────────────────────────────────────────────────
    def _build_profile_bar(self):
        bar = tk.Frame(self, bg="#2c3e50", pady=6)
        bar.pack(fill="x")

        tk.Label(bar, text="当前用户：", bg="#2c3e50", fg="#bdc3c7",
                 font=("Segoe UI", 9)).pack(side="left", padx=(14, 0))

        self.v_profile_name = tk.StringVar()
        self._update_profile_label()
        tk.Label(bar, textvariable=self.v_profile_name, bg="#2c3e50", fg="#ecf0f1",
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 0))

        # Profile selector combobox
        self._profile_names_map: dict[str, str] = {}  # display → id
        self.v_profile_sel = tk.StringVar()
        self._profile_cb = ttk.Combobox(bar, textvariable=self.v_profile_sel,
                                        width=18, state="readonly")
        self._profile_cb.pack(side="left", padx=(16, 0))
        self._profile_cb.bind("<<ComboboxSelected>>", self._on_profile_selected)
        self._refresh_profile_combobox()

        _btn(bar, "+ 新建", _C["blue"],   self._create_profile, padx=10, pady=3,
             font=("Segoe UI", 8)).pack(side="left", padx=(8, 0))
        _btn(bar, "✎ 编辑", _C["grey"],   self._edit_profile,   padx=10, pady=3,
             font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))
        _btn(bar, "🗑 删除", _C["red"],    self._delete_profile, padx=10, pady=3,
             font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))

        # BMR/TDEE quick info
        self.v_profile_stats = tk.StringVar()
        self._update_profile_stats()
        tk.Label(bar, textvariable=self.v_profile_stats, bg="#2c3e50", fg="#95a5a6",
                 font=("Segoe UI", 8)).pack(side="right", padx=(0, 14))

    def _update_profile_label(self):
        p = get_current_profile()
        gender_zh = "男" if p["gender"].lower() in ("male", "m") else "女"
        self.v_profile_name.set(
            f"{p['name']}  ({gender_zh} · {p['age']}岁 · {p['weight_kg']}kg · {p['height_cm']}cm)"
        )

    def _update_profile_stats(self):
        from user_profiles import _bmr_for, _tdee_for
        p = get_current_profile()
        bmr  = _bmr_for(p)
        tdee = _tdee_for(p)
        self.v_profile_stats.set(f"BMR ≈ {bmr:.0f} kcal  ·  TDEE ≈ {tdee:.0f} kcal")

    def _refresh_profile_combobox(self):
        profiles = list_profiles()
        self._profile_names_map = {}
        names = []
        cur_id = get_current_profile_id()
        cur_name = ""
        for p in profiles:
            display = f"{p['name']} ({p['id'][:6]})"
            self._profile_names_map[display] = p["id"]
            names.append(display)
            if p["id"] == cur_id:
                cur_name = display
        self._profile_cb["values"] = names
        self.v_profile_sel.set(cur_name)

    def _on_profile_selected(self, _event=None):
        sel = self.v_profile_sel.get()
        pid = self._profile_names_map.get(sel)
        if pid:
            set_current_profile_id(pid)
            _apply_profile(get_current_profile())
            self._update_profile_label()
            self._update_profile_stats()
            self._refresh_status()
            self._refresh_recommend()

    def _create_profile(self):
        dlg = ProfileDialog(self)
        if dlg.result:
            r = dlg.result
            create_profile(r["name"], r["gender"], r["age"],
                           r["weight_kg"], r["height_cm"], r["activity"])
            self._refresh_profile_combobox()

    def _edit_profile(self):
        p = get_current_profile()
        dlg = ProfileDialog(self, profile=p)
        if dlg.result:
            r = dlg.result
            update_profile(p["id"], **r)
            _apply_profile(get_current_profile())
            self._update_profile_label()
            self._update_profile_stats()
            self._refresh_profile_combobox()
            self._refresh_status()
            self._refresh_recommend()

    def _delete_profile(self):
        p = get_current_profile()
        if p["id"] == "default":
            messagebox.showwarning("提示", "默认档案不能删除。", parent=self)
            return
        if not messagebox.askyesno("确认删除", f"删除档案 \"{p['name']}\"？", parent=self):
            return
        delete_profile(p["id"])
        _apply_profile(get_current_profile())
        self._update_profile_label()
        self._update_profile_stats()
        self._refresh_profile_combobox()
        self._refresh_status()
        self._refresh_recommend()

    # ── Main notebook ──────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_profile_bar()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        self.tab_log     = ttk.Frame(nb)
        self.tab_reports = ttk.Frame(nb)
        self.tab_history = ttk.Frame(nb)
        self.tab_status  = ttk.Frame(nb)
        self.tab_recommend = ttk.Frame(nb)

        nb.add(self.tab_log,       text="  📝 记录餐食  ")
        nb.add(self.tab_reports,   text="  📊 查看报告  ")
        nb.add(self.tab_history,   text="  📋 历史记录  ")
        nb.add(self.tab_status,    text="  📈 今日状态  ")
        nb.add(self.tab_recommend, text="  🍽 推荐菜肴  ")

        self._build_log_tab()
        self._build_reports_tab()
        self._build_history_tab()
        self._build_status_tab()
        self._build_recommend_tab()

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 1 — Record Meal
    # ══════════════════════════════════════════════════════════════════════════
    def _build_log_tab(self):
        f = self.tab_log

        # ── Food input panel ──────────────────────────────────────────────────
        inp = ttk.LabelFrame(f, text="添加食物  Add Food", padding=(14, 10))
        inp.pack(fill="x", padx=14, pady=(14, 4))

        grid = ttk.Frame(inp)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)

        # Row 0 — DB lookup: name + amount + unit + add button
        ttk.Label(grid, text="食物名称").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.v_name = tk.StringVar()
        self.cb_name = ttk.Combobox(grid, textvariable=self.v_name,
                                    values=_ALL_FOOD_NAMES, width=26)
        self.cb_name.grid(row=0, column=1, sticky="ew", padx=(0, 14))
        self.cb_name.bind("<KeyRelease>", self._filter_names)
        self.cb_name.bind("<Return>", lambda _e: self._add_food())

        ttk.Label(grid, text="数量").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.v_amount = tk.StringVar(value="100")
        e_amount = ttk.Entry(grid, textvariable=self.v_amount, width=9)
        e_amount.grid(row=0, column=3, padx=(0, 4))
        e_amount.bind("<Return>", lambda _e: self._add_food())

        self.v_unit = tk.StringVar(value="g")
        ttk.Combobox(grid, textvariable=self.v_unit,
                     values=["g", "ml", "l"], width=5,
                     state="readonly").grid(row=0, column=4, padx=(0, 12))

        _btn(grid, "＋ 从数据库添加", _C["green"], self._add_food,
             padx=14, pady=5).grid(row=0, column=5)

        # Row 1 — manual entry button + status
        row1 = ttk.Frame(inp)
        row1.pack(fill="x", pady=(8, 0))
        _btn(row1, "✎ 手动填写营养素  (格式3 / 格式4)", _C["purple"],
             self._add_food_manual, padx=14, pady=5).pack(side="left")
        self.v_add_status = tk.StringVar()
        ttk.Label(row1, textvariable=self.v_add_status,
                  foreground=_C["green"], font=("Segoe UI", 8)).pack(
            side="left", padx=(14, 0))

        # ── Meal food table ───────────────────────────────────────────────────
        tbl = ttk.LabelFrame(f, text="本次餐食  Current Meal", padding=(10, 6))
        tbl.pack(fill="both", expand=True, padx=14, pady=4)

        cols = ("食物 (摄入量)", "蛋白质 g", "脂肪 g", "碳水 g", "纤维 g", "热量 kcal")
        self.tree_meal = ttk.Treeview(tbl, columns=cols, show="headings", height=9,
                                       selectmode="browse")
        self.tree_meal.heading("食物 (摄入量)", text="食物 (摄入量)")
        self.tree_meal.column("食物 (摄入量)", width=230, anchor="w")
        for c in cols[1:]:
            self.tree_meal.heading(c, text=c)
            self.tree_meal.column(c, width=84, anchor="center")

        vsb = ttk.Scrollbar(tbl, orient="vertical", command=self.tree_meal.yview)
        self.tree_meal.configure(yscrollcommand=vsb.set)
        self.tree_meal.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        _make_sortable(self.tree_meal)

        # ── Totals + remove ───────────────────────────────────────────────────
        act = ttk.Frame(f)
        act.pack(fill="x", padx=14, pady=(2, 0))

        self.v_totals = tk.StringVar()
        ttk.Label(act, textvariable=self.v_totals,
                  font=("Segoe UI", 9), foreground="#555").pack(side="left")
        _btn(act, "🗑 移除选中", _C["grey"], self._remove_food,
             padx=10, pady=5).pack(side="right")

        # ── Submit row ────────────────────────────────────────────────────────
        sub = ttk.Frame(f)
        sub.pack(fill="x", padx=14, pady=(10, 14))

        _btn(sub, "✓  记录餐食并生成报告", _C["green"], self._submit_meal,
             padx=22, pady=11, font=("Segoe UI", 11, "bold")).pack(side="left")
        _btn(sub, "清空", _C["red"], self._clear_meal,
             padx=14, pady=11).pack(side="left", padx=(10, 0))
        _btn(sub, "仅生成报告（不记录餐食）", _C["blue"], self._report_only,
             padx=14, pady=11).pack(side="right")

    # ── Log tab helpers ────────────────────────────────────────────────────────
    def _filter_names(self, _event=None):
        typed = self.v_name.get().lower()
        self.cb_name["values"] = (
            [n for n in _ALL_FOOD_NAMES if typed in n.lower()] if typed
            else _ALL_FOOD_NAMES
        )

    def _add_food(self):
        name = self.v_name.get().strip()
        if not name:
            messagebox.showwarning("提示", "请输入食物名称", parent=self)
            return
        try:
            amount = float(self.v_amount.get())
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的数量（纯数字）", parent=self)
            return

        unit = self.v_unit.get()
        raw: dict = {"name": name}
        if unit == "g":    raw["amount_g"] = amount
        elif unit == "ml": raw["amount_ml"] = amount
        else:              raw["amount_l"] = amount

        self._commit_food(raw)
        self.v_name.set("")
        self.v_amount.set("100")

    def _add_food_manual(self):
        dlg = ManualNutrientDialog(self)
        if dlg.result:
            self._commit_food(dlg.result)

    def _commit_food(self, raw: dict):
        """Resolve raw food dict, add to meal list and update the table."""
        resolved, note = _resolve_food(raw)
        self.meal_foods.append(resolved)

        t  = compute_meal_totals([resolved])
        p, fat, carb, fib = t["protein"], t["fat"], t["carbohydrates"], t["fiber"]
        kcal = p * 4 + fat * 9 + carb * 4
        disp = resolved.get("_amount_display", "")
        label = f"{raw['name']}  {disp}".strip()

        self.tree_meal.insert("", "end", values=(
            label,
            f"{p:.1f}", f"{fat:.1f}", f"{carb:.1f}", f"{fib:.1f}", f"~{kcal:.0f}",
        ))
        self.v_add_status.set(f"✓  {note or (raw['name'] + ' 已添加')}")
        self._refresh_totals()

    def _remove_food(self):
        sel = self.tree_meal.selection()
        if not sel:
            return
        idx = self.tree_meal.index(sel[0])
        self.tree_meal.delete(sel[0])
        if 0 <= idx < len(self.meal_foods):
            self.meal_foods.pop(idx)
        self._refresh_totals()

    def _refresh_totals(self):
        if not self.meal_foods:
            self.v_totals.set("")
            return
        t = compute_meal_totals(self.meal_foods)
        p, fat, carb, fib = t["protein"], t["fat"], t["carbohydrates"], t["fiber"]
        kcal = p * 4 + fat * 9 + carb * 4
        self.v_totals.set(
            f"合计：蛋白质 {p:.1f}g  ·  脂肪 {fat:.1f}g  ·  碳水 {carb:.1f}g  ·  "
            f"纤维 {fib:.1f}g  ·  热量 ~{kcal:.0f} kcal"
        )

    def _submit_meal(self):
        if not self.meal_foods:
            messagebox.showwarning("提示", "请先添加食物", parent=self)
            return
        totals = compute_meal_totals(self.meal_foods)
        entry = {
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "foods":        list(self.meal_foods),
            "totals":       totals,
            "lookup_notes": [],
        }
        append_log(entry)
        log  = load_log()
        path = generate_html_report(log, new_entry=entry)
        webbrowser.open(path.as_uri())
        messagebox.showinfo("完成 ✓",
                            f"餐食已记录，报告已在浏览器中打开。\n\n{path}", parent=self)
        self._clear_meal()
        self._refresh_reports()
        self._refresh_history()
        self._refresh_status()

    def _clear_meal(self):
        self.meal_foods.clear()
        for item in self.tree_meal.get_children():
            self.tree_meal.delete(item)
        self.v_totals.set("")
        self.v_add_status.set("")

    def _report_only(self):
        log  = load_log()
        path = generate_html_report(log)
        webbrowser.open(path.as_uri())
        messagebox.showinfo("完成 ✓",
                            f"报告已在浏览器中打开。\n\n{path}", parent=self)
        self._refresh_reports()

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 2 — Saved Reports
    # ══════════════════════════════════════════════════════════════════════════
    def _build_reports_tab(self):
        f = self.tab_reports

        top = ttk.Frame(f)
        top.pack(fill="x", padx=14, pady=14)
        _btn(top, "生成新报告 并 打开", _C["blue"], self._report_only).pack(side="left")
        _btn(top, "🔄 刷新列表", _C["grey"], self._refresh_reports,
             padx=12).pack(side="left", padx=(10, 0))
        _btn(top, "🗑 删除选中", _C["orange"], self._delete_selected_report,
             padx=12).pack(side="left", padx=(10, 0))
        ttk.Label(top, text="双击打开 / 支持多选删除", foreground="#aaa",
                  font=("Segoe UI", 9)).pack(side="right")

        lf = ttk.LabelFrame(f, text="已保存的报告  Saved Reports", padding=(10, 6))
        lf.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        cols = ("日期", "时间", "文件路径")
        self.tree_reports = ttk.Treeview(lf, columns=cols, show="headings",
                                          selectmode="extended")
        self.tree_reports.heading("日期",    text="日期")
        self.tree_reports.heading("时间",    text="时间")
        self.tree_reports.heading("文件路径", text="文件路径")
        self.tree_reports.column("日期",    width=120, anchor="center")
        self.tree_reports.column("时间",    width=90,  anchor="center")
        self.tree_reports.column("文件路径", width=620, anchor="w")
        self.tree_reports.bind("<Double-1>", self._open_selected_report)
        self.tree_reports.bind("<Delete>", lambda _e: self._delete_selected_report())

        vsb = ttk.Scrollbar(lf, orient="vertical", command=self.tree_reports.yview)
        self.tree_reports.configure(yscrollcommand=vsb.set)
        self.tree_reports.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        _make_sortable(self.tree_reports)

        self._refresh_reports()

    def _refresh_reports(self):
        for item in self.tree_reports.get_children():
            self.tree_reports.delete(item)
        if not OUTPUTS_DIR.exists():
            return
        for r in sorted(OUTPUTS_DIR.glob("*/report_*.html"), reverse=True)[:60]:
            t = r.stem.replace("report_", "")
            ts = f"{t[:2]}:{t[2:4]}:{t[4:]}" if len(t) == 6 else t
            # Use file path as iid for reliable lookup
            self.tree_reports.insert("", "end", iid=str(r),
                                     values=(r.parent.name, ts, str(r)))

    def _open_selected_report(self, _event=None):
        sel = self.tree_reports.selection()
        if sel:
            webbrowser.open(Path(sel[0]).as_uri())

    def _delete_selected_report(self):
        sel = self.tree_reports.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择要删除的报告", parent=self)
            return
        n = len(sel)
        if not messagebox.askyesno(
            "确认删除",
            f"确定删除选中的 {n} 个报告文件？此操作不可撤销。",
            parent=self,
        ):
            return
        errors = []
        for path_str in sel:
            p = Path(path_str)
            try:
                p.unlink()
                # Remove parent date folder if now empty
                try:
                    p.parent.rmdir()
                except OSError:
                    pass  # not empty, that's fine
            except OSError as e:
                errors.append(f"{p.name}: {e}")
        if errors:
            messagebox.showwarning("部分失败",
                                   "以下文件删除失败：\n" + "\n".join(errors), parent=self)
        self._refresh_reports()

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 3 — History
    # ══════════════════════════════════════════════════════════════════════════
    def _build_history_tab(self):
        f = self.tab_history

        top = ttk.Frame(f)
        top.pack(fill="x", padx=14, pady=14)
        _btn(top, "🔄 刷新", _C["grey"], self._refresh_history, padx=12).pack(side="left")
        _btn(top, "🗑 删除选中", _C["orange"], self._delete_selected_log,
             padx=12).pack(side="left", padx=(10, 0))
        _btn(top, "⚠ 清空全部", _C["red"], self._clear_all_log,
             padx=12).pack(side="left", padx=(10, 0))
        self.v_hist_count = tk.StringVar()
        ttk.Label(top, textvariable=self.v_hist_count, foreground="#aaa",
                  font=("Segoe UI", 9)).pack(side="right")

        lf = ttk.LabelFrame(f, text="摄入记录  Intake Log", padding=(10, 6))
        lf.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        cols = ("时间", "食物", "蛋白质 g", "脂肪 g", "碳水 g", "热量 kcal")
        self.tree_hist = ttk.Treeview(lf, columns=cols, show="headings",
                                       selectmode="extended")
        self.tree_hist.heading("时间", text="时间")
        self.tree_hist.heading("食物", text="食物")
        self.tree_hist.column("时间", width=150, anchor="center")
        self.tree_hist.column("食物", width=330, anchor="w")
        for c in cols[2:]:
            self.tree_hist.heading(c, text=c)
            self.tree_hist.column(c, width=84, anchor="center")
        self.tree_hist.bind("<Delete>", lambda _e: self._delete_selected_log())

        vsb = ttk.Scrollbar(lf, orient="vertical", command=self.tree_hist.yview)
        self.tree_hist.configure(yscrollcommand=vsb.set)
        self.tree_hist.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        _make_sortable(self.tree_hist)

        self._refresh_history()

    def _refresh_history(self):
        for item in self.tree_hist.get_children():
            self.tree_hist.delete(item)
        log = load_log()
        self.v_hist_count.set(f"共 {len(log)} 条记录")
        for entry in reversed(log):
            ts_raw = entry.get("timestamp", "")
            ts     = _parse_ts(ts_raw)
            ts_str = ts.astimezone().strftime("%Y-%m-%d %H:%M:%S") if ts else ts_raw
            names  = "、".join(f.get("name", "?") for f in entry.get("foods", []))
            t      = entry.get("totals", {})
            p, fat, carb = t.get("protein", 0), t.get("fat", 0), t.get("carbohydrates", 0)
            kcal   = p * 4 + fat * 9 + carb * 4
            self.tree_hist.insert("", "end", iid=ts_raw, values=(
                ts_str, names,
                f"{p:.1f}", f"{fat:.1f}", f"{carb:.1f}", f"~{kcal:.0f}",
            ))

    def _delete_selected_log(self):
        sel = self.tree_hist.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择要删除的记录", parent=self)
            return
        if not messagebox.askyesno(
            "确认删除",
            f"确定删除选中的 {len(sel)} 条记录？此操作不可撤销。",
            parent=self,
        ):
            return
        to_remove = set(sel)
        save_log([e for e in load_log() if e.get("timestamp", "") not in to_remove])
        self._refresh_history()
        self._refresh_status()

    def _clear_all_log(self):
        count = len(load_log())
        if count == 0:
            messagebox.showinfo("提示", "记录已经是空的", parent=self)
            return
        if not messagebox.askyesno(
            "确认清空",
            f"确定清空全部 {count} 条摄入记录？此操作不可撤销。",
            icon="warning",
            parent=self,
        ):
            return
        save_log([])
        self._refresh_history()
        self._refresh_status()

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 4 — Today's Status
    # ══════════════════════════════════════════════════════════════════════════
    def _build_status_tab(self):
        f = self.tab_status

        top = ttk.Frame(f)
        top.pack(fill="x", padx=14, pady=14)
        _btn(top, "🔄 刷新", _C["grey"], self._refresh_status, padx=12).pack(side="left")
        ttk.Label(top, text="对比今日各营养素与每日RDA目标",
                  foreground="#555", font=("Segoe UI", 9)).pack(side="right")

        lf = ttk.LabelFrame(f, text="今日营养素达标进度  Today's Nutrient Progress",
                            padding=(10, 6))
        lf.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        cols = ("营养素", "今日摄入", "RDA目标", "达标率 %", "状态")
        self.tree_status = ttk.Treeview(lf, columns=cols, show="headings")
        self.tree_status.heading("营养素",  text="营养素")
        self.tree_status.column("营养素",   width=140, anchor="w")
        self.tree_status.heading("今日摄入", text="今日摄入")
        self.tree_status.column("今日摄入", width=110, anchor="center")
        self.tree_status.heading("RDA目标",  text="RDA目标")
        self.tree_status.column("RDA目标",  width=110, anchor="center")
        self.tree_status.heading("达标率 %", text="达标率 %")
        self.tree_status.column("达标率 %", width=80,  anchor="center")
        self.tree_status.heading("状态",    text="状态")
        self.tree_status.column("状态",     width=80,  anchor="center")

        self.tree_status.tag_configure("ok",   background="#d4edda", foreground="#155724")
        self.tree_status.tag_configure("warn", background="#fff3cd", foreground="#856404")
        self.tree_status.tag_configure("bad",  background="#f8d7da", foreground="#721c24")

        vsb = ttk.Scrollbar(lf, orient="vertical", command=self.tree_status.yview)
        self.tree_status.configure(yscrollcommand=vsb.set)
        self.tree_status.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        _make_sortable(self.tree_status)

        self._refresh_status()

    def _refresh_status(self):
        for item in self.tree_status.get_children():
            self.tree_status.delete(item)

        log = load_log()
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_totals: dict[str, float] = {k: 0.0 for k in ALL_NUTRIENT_KEYS}
        for entry in log:
            ts = _parse_ts(entry.get("timestamp", ""))
            if ts and ts.astimezone().strftime("%Y-%m-%d") == today_str:
                for k in ALL_NUTRIENT_KEYS:
                    today_totals[k] += float(entry.get("totals", {}).get(k, 0.0))

        for key, info in NUTRIENTS.items():
            if info["time_window_days"] != 1:
                continue
            rda    = _get_rda(key)
            actual = today_totals.get(key, 0.0)
            pct    = (actual / rda * 100) if rda > 0 else 0.0
            unit   = info["unit"]

            def _fmt(v: float, u: str = unit) -> str:
                if u in ("mcg", "mcg_rae", "mcg_dfe"):
                    return f"{v:.1f} mcg"
                if u in ("mg", "mg_ne"):
                    return f"{v:.1f} mg"
                return f"{v:.1f} g"

            if info.get("upper_limit"):
                # Lower is better: green < 70%, yellow 70-100%, red > 100%
                tag    = "ok"   if pct <  70 else ("warn" if pct < 100 else "bad")
                status = "✓ 正常" if pct < 70 else ("~ 偏高" if pct < 100 else "✗ 超标")
            else:
                tag    = "ok" if pct >= 100 else ("warn" if pct >= 70 else "bad")
                status = "✓ 达标" if pct >= 100 else ("~ 接近" if pct >= 70 else "✗ 不足")

            self.tree_status.insert("", "end", tags=(tag,), values=(
                info["name"], _fmt(actual), _fmt(rda), f"{pct:.0f}%", status,
            ))

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 5 — Dish Recommendations
    # ══════════════════════════════════════════════════════════════════════════
    def _build_recommend_tab(self):
        f = self.tab_recommend

        top = ttk.Frame(f)
        top.pack(fill="x", padx=14, pady=14)
        _btn(top, "🔄 重新推荐", _C["blue"],  self._refresh_recommend, padx=14).pack(side="left")
        _btn(top, "📋 所有菜肴", _C["grey"],  self._show_all_dishes,   padx=14).pack(side="left", padx=(10, 0))
        ttk.Label(top, text="基于今日营养缺口，推荐最能补充缺失营养素的菜肴",
                  foreground="#555", font=("Segoe UI", 9)).pack(side="right")

        # ── Recommendations list ───────────────────────────────────────────
        rec_lf = ttk.LabelFrame(f, text="推荐菜肴  Recommended Dishes", padding=(10, 6))
        rec_lf.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        rec_cols = ("排名", "菜名", "份量", "蛋白质g", "脂肪g", "碳水g",
                    "热量kcal", "主要补充营养素")
        self.tree_rec = ttk.Treeview(rec_lf, columns=rec_cols, show="headings",
                                      height=6, selectmode="browse")
        widths = [50, 130, 110, 70, 70, 70, 80, 260]
        anchors = ["center", "w", "w"] + ["center"] * 4 + ["w"]
        for col, w, a in zip(rec_cols, widths, anchors):
            self.tree_rec.heading(col, text=col)
            self.tree_rec.column(col, width=w, anchor=a)
        self.tree_rec.tag_configure("top1", background="#d4edda")
        self.tree_rec.tag_configure("top2", background="#fff3cd")
        self.tree_rec.bind("<Double-1>", self._edit_dish_from_rec)

        vsb_rec = ttk.Scrollbar(rec_lf, orient="vertical", command=self.tree_rec.yview)
        self.tree_rec.configure(yscrollcommand=vsb_rec.set)
        self.tree_rec.pack(side="left", fill="both", expand=True)
        vsb_rec.pack(side="right", fill="y")
        _make_sortable(self.tree_rec)

        # ── Nutrient gap summary ───────────────────────────────────────────
        gap_lf = ttk.LabelFrame(f, text="今日营养缺口  Today's Gaps", padding=(10, 6))
        gap_lf.pack(fill="x", padx=14, pady=(0, 14))

        gap_cols = ("营养素", "今日摄入", "RDA目标", "缺口", "缺口率%")
        self.tree_gaps = ttk.Treeview(gap_lf, columns=gap_cols, show="headings",
                                       height=5, selectmode="none")
        for col in gap_cols:
            self.tree_gaps.heading(col, text=col)
            self.tree_gaps.column(col, width=120, anchor="center")
        self.tree_gaps.column("营养素", width=150, anchor="w")
        self.tree_gaps.tag_configure("big",  background="#f8d7da", foreground="#721c24")
        self.tree_gaps.tag_configure("mid",  background="#fff3cd", foreground="#856404")
        self.tree_gaps.tag_configure("small",background="#d4edda", foreground="#155724")

        vsb_gap = ttk.Scrollbar(gap_lf, orient="vertical", command=self.tree_gaps.yview)
        self.tree_gaps.configure(yscrollcommand=vsb_gap.set)
        self.tree_gaps.pack(side="left", fill="both", expand=True)
        vsb_gap.pack(side="right", fill="y")
        _make_sortable(self.tree_gaps)

        self._refresh_recommend()

    def _today_totals(self) -> dict[str, float]:
        from nutrients_data import ALL_NUTRIENT_KEYS as _AK
        log = load_log()
        today_str = datetime.now().strftime("%Y-%m-%d")
        totals: dict[str, float] = {k: 0.0 for k in _AK}
        for entry in log:
            ts = _parse_ts(entry.get("timestamp", ""))
            if ts and ts.astimezone().strftime("%Y-%m-%d") == today_str:
                for k in _AK:
                    totals[k] += float(entry.get("totals", {}).get(k, 0.0))
        return totals

    def _refresh_recommend(self):
        # Clear both trees
        for item in self.tree_rec.get_children():
            self.tree_rec.delete(item)
        for item in self.tree_gaps.get_children():
            self.tree_gaps.delete(item)

        today = self._today_totals()
        recs  = recommend_dishes(today, _get_rda, top_n=8)

        _KEY_NAMES = {
            "protein": "蛋白质", "fat": "脂肪", "carbohydrates": "碳水",
            "fiber": "膳食纤维", "vitamin_a": "维A", "vitamin_c": "维C",
            "vitamin_d": "维D", "calcium": "钙", "iron": "铁", "potassium": "钾",
        }

        for rank, r in enumerate(recs, 1):
            dish = r["dish"]
            n    = dish["nutrients"]
            top  = "、".join(
                f"{_KEY_NAMES.get(k, k)} +{pct:.0f}%RDA"
                for k, pct in r["top_gaps_filled"]
            )
            tag = "top1" if rank == 1 else ("top2" if rank == 2 else "")
            self.tree_rec.insert("", "end", iid=dish["name"], tags=(tag,), values=(
                f"#{rank}", dish["name"], dish["serving_desc"],
                f"{n['protein']:.1f}", f"{n['fat']:.1f}", f"{n['carbohydrates']:.1f}",
                f"~{n['kcal']:.0f}", top or "—",
            ))

        # Gap summary
        gaps = compute_gaps(today, _get_rda)
        gap_rows = [(k, gaps[k]) for k in SCORING_KEYS if gaps[k] > 0]
        gap_rows.sort(key=lambda x: x[1] / max(_get_rda(x[0]), 1), reverse=True)

        _UNITS = {
            "protein": "g", "fat": "g", "carbohydrates": "g", "fiber": "g",
            "vitamin_a": "mcg", "vitamin_c": "mg", "vitamin_d": "mcg",
            "calcium": "mg", "iron": "mg", "potassium": "mg",
        }
        for key, gap in gap_rows:
            rda    = _get_rda(key)
            actual = float(today.get(key, 0.0))
            pct    = gap / rda * 100 if rda > 0 else 0
            unit   = _UNITS.get(key, "")
            tag    = "big" if pct > 50 else ("mid" if pct > 20 else "small")
            self.tree_gaps.insert("", "end", tags=(tag,), values=(
                _KEY_NAMES.get(key, key),
                f"{actual:.1f} {unit}",
                f"{rda:.1f} {unit}",
                f"{gap:.1f} {unit}",
                f"{pct:.0f}%",
            ))

    def _edit_dish_from_rec(self, _event=None):
        sel = self.tree_rec.selection()
        if not sel:
            return
        dish_name = sel[0]  # iid = dish name
        from dish_database import get_dish
        dish = get_dish(dish_name)
        if dish:
            dlg = DishEditorDialog(self, dish)
            if dlg.saved:
                self._refresh_recommend()

    def _show_all_dishes(self):
        """Open a window listing all dishes with an edit button."""
        win = tk.Toplevel(self)
        win.title("所有菜肴数据库")
        win.geometry("860x520")
        win.transient(self)

        top = ttk.Frame(win)
        top.pack(fill="x", padx=12, pady=10)
        ttk.Label(top, text="双击菜肴可编辑营养数据", foreground="#888",
                  font=("Segoe UI", 9)).pack(side="left")
        _btn(top, "关闭", _C["grey"], win.destroy, padx=12, pady=5).pack(side="right")

        lf = ttk.LabelFrame(win, text="菜肴列表", padding=(8, 6))
        lf.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols = ("菜名", "份量", "蛋白质g", "脂肪g", "碳水g", "热量kcal", "状态")
        tree = ttk.Treeview(lf, columns=cols, show="headings")
        widths = [140, 130, 80, 80, 80, 90, 80]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center" if col != "菜名" and col != "份量" else "w")
        tree.tag_configure("custom", foreground="#8e44ad")

        vsb = ttk.Scrollbar(lf, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        _make_sortable(tree)

        def _populate():
            for item in tree.get_children():
                tree.delete(item)
            for dish in list_dishes():
                n   = dish["nutrients"]
                tag = ("custom",) if dish.get("_overridden") else ()
                status = "已修改" if dish.get("_overridden") else "默认"
                tree.insert("", "end", iid=dish["name"], tags=tag, values=(
                    dish["name"], dish["serving_desc"],
                    f"{n['protein']:.1f}", f"{n['fat']:.1f}",
                    f"{n['carbohydrates']:.1f}", f"~{n['kcal']:.0f}", status,
                ))

        def _on_dbl(_e):
            sel = tree.selection()
            if not sel:
                return
            from dish_database import get_dish
            dish = get_dish(sel[0])
            if dish:
                dlg = DishEditorDialog(win, dish)
                if dlg.saved:
                    _populate()
                    self._refresh_recommend()

        tree.bind("<Double-1>", _on_dbl)
        _populate()


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    app = NutrientApp()
    app.mainloop()


if __name__ == "__main__":
    main()
