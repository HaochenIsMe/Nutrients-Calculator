"""
Comprehensive food nutrition database.
Nutrient values are per 100g (or per 100ml for liquids), sourced from USDA FoodData Central.
"""

from __future__ import annotations
import re


# ---------------------------------------------------------------------------
# Helper: build a full 32-key nutrient dict (defaults all to 0.0)
# ---------------------------------------------------------------------------
_NUTRIENT_KEYS = [
    "protein", "fat", "carbohydrates", "fiber", "sugar",
    "vitamin_a", "vitamin_c", "vitamin_d", "vitamin_e",
    "vitamin_k", "vitamin_b1", "vitamin_b2", "vitamin_b3",
    "vitamin_b5", "vitamin_b6", "vitamin_b7", "vitamin_b9",
    "vitamin_b12", "calcium", "phosphorus", "magnesium",
    "potassium", "sodium", "iron", "zinc", "selenium",
    "iodine", "copper", "manganese", "chromium",
    "molybdenum", "fluoride", "omega3",
]

def _n(**kwargs) -> dict:
    """Return a nutrients dict with all 33 keys present; missing ones default to 0.0."""
    d = {k: 0.0 for k in _NUTRIENT_KEYS}
    for k, v in kwargs.items():
        if k not in d:
            raise KeyError(f"Unknown nutrient key: {k!r}")
        d[k] = float(v)
    return d


# ---------------------------------------------------------------------------
# Food database
# ---------------------------------------------------------------------------
FOOD_DB: list[dict] = [

    # ------------------------------------------------------------------ Meat & Fish
    {
        "names": ["鸡胸肉", "chicken breast", "鸡肉"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=31.0, fat=3.6,
            vitamin_a=9.0, vitamin_d=0.1, vitamin_e=0.27,
            vitamin_b1=0.07, vitamin_b2=0.11, vitamin_b3=13.4,
            vitamin_b5=0.9, vitamin_b6=0.9, vitamin_b7=3.0, vitamin_b9=4.0,
            vitamin_b12=0.3,
            calcium=11.0, phosphorus=220.0, magnesium=29.0,
            potassium=256.0, sodium=74.0,
            iron=0.9, zinc=1.0, selenium=27.6,
            copper=0.05, manganese=0.02, omega3=0.06,
        ),
    },
    {
        "names": ["牛肉", "beef", "lean beef"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=26.0, fat=3.6,
            vitamin_b2=0.20, vitamin_b3=6.2, vitamin_b5=0.5, vitamin_b6=0.4,
            vitamin_b12=2.6,
            calcium=18.0, phosphorus=200.0, magnesium=21.0,
            potassium=318.0, sodium=58.0,
            iron=2.6, zinc=7.0, selenium=14.2,
            copper=0.09, manganese=0.01, chromium=2.0, omega3=0.1,
        ),
    },
    {
        "names": ["猪肉", "pork", "pork loin"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=22.0, fat=4.0,
            vitamin_b1=0.87, vitamin_b2=0.22, vitamin_b3=6.3,
            vitamin_b5=0.8, vitamin_b6=0.5, vitamin_b12=0.7,
            calcium=6.0, phosphorus=210.0, magnesium=22.0,
            potassium=370.0, sodium=62.0,
            iron=0.9, zinc=2.4, selenium=33.0,
            copper=0.06, manganese=0.01, omega3=0.05,
        ),
    },
    {
        "names": ["三文鱼", "salmon"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=20.4, fat=13.4,
            vitamin_a=12.0, vitamin_c=3.9, vitamin_d=11.1, vitamin_e=3.55,
            vitamin_k=0.5,
            vitamin_b1=0.22, vitamin_b2=0.49, vitamin_b3=7.86,
            vitamin_b5=1.66, vitamin_b6=0.94, vitamin_b7=5.0, vitamin_b9=26.0,
            vitamin_b12=3.18,
            calcium=12.0, phosphorus=371.0, magnesium=29.0,
            potassium=628.0, sodium=59.0,
            iron=0.8, zinc=0.64, selenium=36.5, iodine=9.0,
            copper=0.25, manganese=0.02, omega3=2.26,
        ),
    },
    {
        "names": ["金枪鱼罐头", "canned tuna", "tuna"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=29.0, fat=0.5,
            vitamin_d=3.7,
            vitamin_b3=18.5, vitamin_b6=0.4, vitamin_b12=2.5,
            calcium=11.0, phosphorus=269.0, magnesium=34.0,
            potassium=237.0, sodium=344.0,
            iron=1.3, zinc=0.8, selenium=80.4,
            copper=0.1, omega3=0.3,
        ),
    },
    {
        "names": ["沙丁鱼罐头", "canned sardines", "sardines"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=25.0, fat=11.5,
            vitamin_d=4.8,
            vitamin_b2=0.18, vitamin_b3=5.2, vitamin_b5=0.6,
            vitamin_b6=0.2, vitamin_b12=8.9,
            calcium=382.0, phosphorus=490.0, magnesium=39.0,
            potassium=397.0, sodium=505.0,
            iron=2.9, zinc=1.3, selenium=52.7, iodine=35.0,
            copper=0.19, fluoride=0.88, omega3=1.48,
        ),
    },
    {
        "names": ["虾", "shrimp", "prawns"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=20.1, fat=0.9,
            vitamin_b2=0.03, vitamin_b3=2.6, vitamin_b12=1.4,
            calcium=70.0, phosphorus=237.0, magnesium=37.0,
            potassium=259.0, sodium=148.0,
            iron=2.4, zinc=1.1, selenium=39.6, iodine=40.0,
            copper=0.26, omega3=0.3,
        ),
    },
    {
        "names": ["牡蛎", "oysters", "oyster"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=9.0, fat=2.3, carbohydrates=4.9,
            vitamin_d=1.7,
            vitamin_b1=0.06, vitamin_b2=0.18, vitamin_b3=1.3,
            vitamin_b5=0.5, vitamin_b6=0.07, vitamin_b12=16.0,
            calcium=45.0, phosphorus=135.0, magnesium=22.0,
            potassium=168.0, sodium=417.0,
            iron=6.7, zinc=78.6, selenium=77.0,
            copper=7.6, manganese=0.4, omega3=0.6,
        ),
    },
    {
        "names": ["牛肝", "beef liver", "liver"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=20.4, fat=3.6, carbohydrates=3.9,
            vitamin_a=4968.0, vitamin_c=1.3, vitamin_d=1.2, vitamin_e=0.38,
            vitamin_k=3.1,
            vitamin_b1=0.18, vitamin_b2=3.08, vitamin_b3=14.9,
            vitamin_b5=7.0, vitamin_b6=1.08, vitamin_b7=36.8, vitamin_b9=290.0,
            vitamin_b12=59.3,
            calcium=5.0, phosphorus=387.0, magnesium=18.0,
            potassium=313.0, sodium=76.0,
            iron=6.5, zinc=5.2, selenium=28.1,
            copper=9.76, manganese=0.26, molybdenum=104.0, omega3=0.1,
        ),
    },
    {
        "names": ["鳕鱼", "cod"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=17.8, fat=0.9,
            vitamin_d=1.0,
            vitamin_b3=2.1, vitamin_b6=0.25, vitamin_b12=0.9,
            calcium=16.0, phosphorus=203.0, magnesium=42.0,
            potassium=413.0, sodium=54.0,
            iron=0.4, zinc=0.5, selenium=33.1, iodine=170.0,
            copper=0.03, omega3=0.2,
        ),
    },

    # ------------------------------------------------------------------ Eggs & Dairy
    {
        "names": ["鸡蛋", "egg", "cooked egg", "whole egg"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=13.0, fat=11.0, carbohydrates=1.1,
            vitamin_a=160.0, vitamin_d=2.0, vitamin_e=1.05, vitamin_k=0.3,
            vitamin_b1=0.05, vitamin_b2=0.46, vitamin_b3=0.1,
            vitamin_b5=1.4, vitamin_b6=0.17, vitamin_b7=20.0, vitamin_b9=44.0,
            vitamin_b12=1.1,
            calcium=50.0, phosphorus=198.0, magnesium=12.0,
            potassium=138.0, sodium=142.0,
            iron=1.8, zinc=1.3, selenium=30.8, iodine=53.0,
            copper=0.07, manganese=0.04, omega3=0.1,
        ),
    },
    {
        "names": ["蛋黄", "egg yolk", "yolk"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=15.9, fat=26.5, carbohydrates=3.6,
            vitamin_a=381.0, vitamin_d=5.4, vitamin_e=2.6, vitamin_k=0.7,
            vitamin_b1=0.18, vitamin_b2=0.53,
            vitamin_b5=2.99, vitamin_b6=0.35, vitamin_b7=50.0, vitamin_b9=144.0,
            vitamin_b12=1.95,
            calcium=129.0, phosphorus=390.0, magnesium=5.0,
            potassium=109.0, sodium=48.0,
            iron=2.7, zinc=2.3, selenium=56.0,
            copper=0.08, omega3=0.5,
        ),
    },
    {
        "names": ["牛奶", "milk", "whole milk"],
        "is_liquid": True,
        "density_g_per_ml": 1.03,
        "nutrients_per_100g": _n(
            protein=3.4, fat=3.7, carbohydrates=4.8, sugar=4.8,
            vitamin_a=46.0, vitamin_d=1.0, vitamin_e=0.06,
            vitamin_b1=0.04, vitamin_b2=0.18, vitamin_b3=0.09,
            vitamin_b5=0.35, vitamin_b6=0.04, vitamin_b7=3.5, vitamin_b9=5.0,
            vitamin_b12=0.45,
            calcium=120.0, phosphorus=93.0, magnesium=11.0,
            potassium=150.0, sodium=44.0,
            iron=0.03, zinc=0.38, selenium=3.7, iodine=56.0,
            copper=0.01, manganese=0.003, fluoride=0.02, omega3=0.08,
        ),
    },
    {
        "names": ["希腊酸奶", "greek yogurt", "Greek yogurt"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=10.0, fat=0.7, carbohydrates=3.6, sugar=4.0,
            vitamin_b2=0.27, vitamin_b5=0.33, vitamin_b12=0.75,
            calcium=110.0, phosphorus=135.0, magnesium=11.0,
            potassium=141.0, sodium=36.0,
            iron=0.07, zinc=0.52, selenium=9.7, iodine=37.0,
            omega3=0.04,
        ),
    },
    {
        "names": ["酸奶", "yogurt"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=3.5, fat=3.3, carbohydrates=4.7, sugar=4.7,
            vitamin_a=27.0,
            vitamin_b2=0.14, vitamin_b5=0.3, vitamin_b12=0.37,
            calcium=121.0, phosphorus=95.0, magnesium=12.0,
            potassium=155.0, sodium=46.0,
            iron=0.05, zinc=0.59, selenium=3.3, iodine=37.0,
            omega3=0.05,
        ),
    },
    {
        "names": ["硬奶酪", "hard cheese", "cheddar", "cheese"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=25.0, fat=33.0, carbohydrates=1.3,
            vitamin_a=330.0, vitamin_d=0.6, vitamin_e=0.4, vitamin_k=2.8,
            vitamin_b1=0.03, vitamin_b2=0.38, vitamin_b5=0.41,
            vitamin_b6=0.07, vitamin_b12=0.83,
            calcium=720.0, phosphorus=512.0, magnesium=28.0,
            potassium=98.0, sodium=620.0,
            iron=0.7, zinc=3.1, selenium=14.5, iodine=40.0,
            copper=0.03, omega3=0.3,
        ),
    },
    {
        "names": ["黄油", "butter"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.9, fat=81.1, carbohydrates=0.1,
            vitamin_a=684.0, vitamin_d=1.5, vitamin_e=2.32, vitamin_k=7.0,
            calcium=24.0, phosphorus=24.0, sodium=11.0,
            selenium=1.0, omega3=0.32,
        ),
    },

    # ------------------------------------------------------------------ Legumes & Tofu
    {
        "names": ["老豆腐", "firm tofu", "tofu"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=8.0, fat=4.8, carbohydrates=2.0, fiber=0.3,
            vitamin_b1=0.08, vitamin_b2=0.05, vitamin_b3=0.3,
            vitamin_b5=0.15, vitamin_b6=0.07, vitamin_b9=15.0,
            calcium=350.0, phosphorus=97.0, magnesium=58.0,
            potassium=150.0, sodium=7.0,
            iron=2.7, zinc=0.8, selenium=8.9,
            copper=0.19, manganese=0.6, omega3=0.3,
        ),
    },
    {
        "names": ["扁豆", "lentils", "cooked lentils"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=9.0, fat=0.4, carbohydrates=20.0, fiber=7.9,
            vitamin_b1=0.17, vitamin_b2=0.07, vitamin_b3=1.1,
            vitamin_b5=0.64, vitamin_b6=0.18, vitamin_b9=181.0,
            calcium=19.0, phosphorus=180.0, magnesium=36.0,
            potassium=369.0, sodium=2.0,
            iron=3.3, zinc=1.3, selenium=2.8,
            copper=0.25, manganese=0.49, molybdenum=155.0, omega3=0.04,
        ),
    },
    {
        "names": ["黑豆", "black beans", "cooked black beans"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=8.9, fat=0.5, carbohydrates=23.7, fiber=8.7,
            vitamin_b1=0.24, vitamin_b2=0.06, vitamin_b3=0.5,
            vitamin_b6=0.07, vitamin_b9=64.0,
            calcium=27.0, phosphorus=131.0, magnesium=60.0,
            potassium=355.0, sodium=1.0,
            iron=2.1, zinc=1.0, selenium=1.2,
            copper=0.21, manganese=0.44, molybdenum=130.0, omega3=0.17,
        ),
    },
    {
        "names": ["鹰嘴豆", "chickpeas", "cooked chickpeas", "garbanzo beans"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=8.9, fat=2.6, carbohydrates=27.4, fiber=7.6,
            vitamin_b1=0.12, vitamin_b2=0.06, vitamin_b3=0.5,
            vitamin_b5=0.29, vitamin_b6=0.14, vitamin_b9=172.0,
            calcium=49.0, phosphorus=168.0, magnesium=48.0,
            potassium=291.0, sodium=7.0,
            iron=2.9, zinc=1.5, selenium=3.0,
            copper=0.35, manganese=1.03, molybdenum=109.0, omega3=0.04,
        ),
    },
    {
        "names": ["白豆", "white beans", "cooked white beans", "cannellini beans"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=9.7, fat=0.4, carbohydrates=22.8, fiber=6.3,
            vitamin_b1=0.17, vitamin_b2=0.05, vitamin_b3=0.4,
            vitamin_b6=0.11, vitamin_b9=88.0,
            calcium=73.0, phosphorus=143.0, magnesium=63.0,
            potassium=561.0, sodium=2.0,
            iron=3.7, zinc=1.0, selenium=1.4,
            copper=0.23, manganese=0.52, omega3=0.09,
        ),
    },

    # ------------------------------------------------------------------ Grains
    {
        "names": ["面粉", "小麦粉", "all-purpose flour", "wheat flour"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=10.3, fat=1.0, carbohydrates=76.3, fiber=2.7,
            vitamin_b1=0.12, vitamin_b2=0.04, vitamin_b3=1.25,
            vitamin_b5=0.44, vitamin_b6=0.04, vitamin_b9=26.0,
            calcium=15.0, phosphorus=108.0, magnesium=22.0,
            potassium=107.0, sodium=2.0,
            iron=1.17, zinc=0.7, selenium=33.9,
            copper=0.14, manganese=0.68, omega3=0.04,
        ),
    },
    {
        "names": ["白米饭", "white rice", "cooked white rice", "米饭"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=2.7, fat=0.3, carbohydrates=28.0, fiber=0.4,
            vitamin_b1=0.02, vitamin_b2=0.01, vitamin_b3=0.4,
            vitamin_b5=0.3, vitamin_b6=0.09,
            calcium=10.0, phosphorus=68.0, magnesium=12.0,
            potassium=35.0, sodium=1.0,
            iron=0.2, zinc=0.5, selenium=7.5,
            copper=0.07, manganese=0.5, omega3=0.01,
        ),
    },
    {
        "names": ["糙米饭", "brown rice", "cooked brown rice"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=2.6, fat=0.9, carbohydrates=23.0, fiber=1.8,
            vitamin_b1=0.1, vitamin_b2=0.01, vitamin_b3=1.5,
            vitamin_b5=0.39, vitamin_b6=0.15,
            calcium=10.0, phosphorus=83.0, magnesium=44.0,
            potassium=79.0, sodium=1.0,
            iron=0.5, zinc=0.6, selenium=9.8,
            copper=0.08, manganese=0.97, omega3=0.02,
        ),
    },
    {
        "names": ["燕麦", "oats", "dry oats", "rolled oats"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=17.0, fat=7.0, carbohydrates=66.0, fiber=10.6,
            vitamin_b1=0.76, vitamin_b2=0.14, vitamin_b3=1.1,
            vitamin_b5=1.35, vitamin_b6=0.12, vitamin_b9=56.0,
            calcium=54.0, phosphorus=523.0, magnesium=177.0,
            potassium=429.0, sodium=2.0,
            iron=4.7, zinc=3.97, selenium=28.9,
            copper=0.63, manganese=3.63, molybdenum=85.0, omega3=0.11,
        ),
    },
    {
        "names": ["全麦面包", "whole wheat bread", "wholemeal bread"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=9.0, fat=4.2, carbohydrates=43.0, fiber=6.0, sugar=5.7,
            vitamin_b1=0.38, vitamin_b2=0.16, vitamin_b3=3.0,
            vitamin_b5=0.5, vitamin_b6=0.1, vitamin_b9=27.0,
            calcium=73.0, phosphorus=212.0, magnesium=76.0,
            potassium=248.0, sodium=491.0,
            iron=2.9, zinc=1.8, selenium=28.0,
            copper=0.22, manganese=1.87, chromium=4.5, omega3=0.2,
        ),
    },
    {
        "names": ["白面包", "white bread"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=8.0, fat=2.8, carbohydrates=49.0, fiber=2.3, sugar=5.1,
            vitamin_b1=0.5, vitamin_b2=0.25, vitamin_b3=4.5,
            vitamin_b5=0.4, vitamin_b6=0.04, vitamin_b9=27.0,
            calcium=150.0, phosphorus=109.0, magnesium=23.0,
            potassium=115.0, sodium=491.0,
            iron=2.2, zinc=0.8, selenium=20.0,
            copper=0.1, manganese=0.4, omega3=0.1,
        ),
    },
    {
        "names": ["红薯", "sweet potato", "cooked sweet potato"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=1.6, fat=0.1, carbohydrates=20.0, fiber=3.0, sugar=4.2,
            vitamin_a=961.0, vitamin_c=19.6, vitamin_e=0.26, vitamin_k=1.8,
            vitamin_b1=0.08, vitamin_b2=0.06, vitamin_b3=1.49,
            vitamin_b5=0.95, vitamin_b6=0.29, vitamin_b7=4.9, vitamin_b9=6.0,
            calcium=27.0, phosphorus=47.0, magnesium=27.0,
            potassium=475.0, sodium=27.0,
            iron=0.7, zinc=0.3, selenium=0.6,
            copper=0.15, manganese=0.26, chromium=1.0,
        ),
    },
    {
        "names": ["土豆", "potato", "boiled potato", "马铃薯"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=1.9, fat=0.1, carbohydrates=17.0, fiber=1.8, sugar=1.2,
            vitamin_c=13.0, vitamin_k=1.9,
            vitamin_b1=0.1, vitamin_b2=0.03, vitamin_b3=1.44,
            vitamin_b5=0.53, vitamin_b6=0.3, vitamin_b9=9.0,
            calcium=5.0, phosphorus=44.0, magnesium=22.0,
            potassium=379.0, sodium=4.0,
            iron=0.3, zinc=0.3, selenium=0.3,
            copper=0.09, manganese=0.14, chromium=0.3,
        ),
    },

    # ------------------------------------------------------------------ Vegetables
    {
        "names": ["菠菜", "spinach", "cooked spinach"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=2.97, fat=0.26, carbohydrates=3.75, fiber=2.4,
            vitamin_a=524.0, vitamin_c=9.8, vitamin_e=2.08, vitamin_k=483.0,
            vitamin_b1=0.09, vitamin_b2=0.24, vitamin_b3=0.49,
            vitamin_b5=0.15, vitamin_b6=0.24, vitamin_b7=0.4, vitamin_b9=146.0,
            calcium=99.0, phosphorus=56.0, magnesium=87.0,
            potassium=466.0, sodium=70.0,
            iron=3.6, zinc=0.76, selenium=1.5,
            copper=0.16, manganese=0.85, omega3=0.14,
        ),
    },
    {
        "names": ["西兰花", "broccoli"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=2.8, fat=0.4, carbohydrates=7.0, fiber=2.6,
            vitamin_a=31.0, vitamin_c=89.0, vitamin_e=0.78, vitamin_k=102.0,
            vitamin_b1=0.07, vitamin_b2=0.12, vitamin_b3=0.64,
            vitamin_b5=0.57, vitamin_b6=0.18, vitamin_b9=63.0,
            calcium=47.0, phosphorus=66.0, magnesium=21.0,
            potassium=316.0, sodium=33.0,
            iron=0.73, zinc=0.41, selenium=2.5,
            copper=0.04, manganese=0.21, chromium=11.0, omega3=0.05,
        ),
    },
    {
        "names": ["胡萝卜", "carrot"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.9, fat=0.2, carbohydrates=10.0, fiber=2.8, sugar=4.7,
            vitamin_a=835.0, vitamin_c=5.9, vitamin_k=13.2,
            vitamin_b1=0.07, vitamin_b2=0.06, vitamin_b3=0.98,
            vitamin_b5=0.27, vitamin_b6=0.14, vitamin_b9=19.0,
            calcium=33.0, phosphorus=35.0, magnesium=12.0,
            potassium=320.0, sodium=69.0,
            iron=0.3, zinc=0.24, selenium=0.1,
            copper=0.05, manganese=0.14,
        ),
    },
    {
        "names": ["红甜椒", "red bell pepper", "red pepper", "甜椒"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.99, fat=0.3, carbohydrates=6.0, fiber=2.1, sugar=4.2,
            vitamin_a=157.0, vitamin_c=128.0, vitamin_e=1.58, vitamin_k=4.9,
            vitamin_b1=0.05, vitamin_b2=0.09, vitamin_b3=0.98,
            vitamin_b5=0.32, vitamin_b6=0.29, vitamin_b9=46.0,
            calcium=7.0, phosphorus=26.0, magnesium=12.0,
            potassium=211.0, sodium=4.0,
            iron=0.43, zinc=0.25, selenium=0.1,
            copper=0.07, manganese=0.1, omega3=0.04,
        ),
    },
    {
        "names": ["番茄", "tomato", "西红柿"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.9, fat=0.2, carbohydrates=3.9, fiber=1.2, sugar=2.6,
            vitamin_a=42.0, vitamin_c=14.0, vitamin_e=0.54, vitamin_k=7.9,
            vitamin_b1=0.04, vitamin_b2=0.02, vitamin_b3=0.59,
            vitamin_b5=0.09, vitamin_b6=0.08, vitamin_b9=15.0,
            calcium=10.0, phosphorus=24.0, magnesium=11.0,
            potassium=237.0, sodium=5.0,
            iron=0.27, zinc=0.17, selenium=0.4,
            copper=0.06, manganese=0.11,
        ),
    },
    {
        "names": ["南瓜", "pumpkin", "cooked pumpkin"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.7, fat=0.1, carbohydrates=6.5, fiber=0.5, sugar=2.8,
            vitamin_a=426.0, vitamin_c=9.0, vitamin_e=1.06,
            vitamin_b1=0.05, vitamin_b2=0.11, vitamin_b3=0.6,
            vitamin_b5=0.3, vitamin_b6=0.06, vitamin_b9=16.0,
            calcium=21.0, phosphorus=44.0, magnesium=12.0,
            potassium=340.0, sodium=1.0,
            iron=0.8, zinc=0.32, selenium=0.3,
            copper=0.13, manganese=0.1, omega3=0.02,
        ),
    },
    {
        "names": ["白菜", "大白菜", "napa cabbage", "chinese cabbage"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=1.5, fat=0.1, carbohydrates=3.2, fiber=1.2, sugar=1.4,
            vitamin_a=20.0, vitamin_c=31.0, vitamin_e=0.08, vitamin_k=59.0,
            vitamin_b1=0.04, vitamin_b2=0.05, vitamin_b3=0.4,
            vitamin_b5=0.13, vitamin_b6=0.23, vitamin_b9=79.0,
            calcium=105.0, phosphorus=37.0, magnesium=13.0,
            potassium=230.0, sodium=65.0,
            iron=0.31, zinc=0.23, selenium=0.5,
            copper=0.04, manganese=0.19, omega3=0.03,
        ),
    },
    {
        "names": ["卷心菜", "cabbage"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=1.3, fat=0.1, carbohydrates=5.8, fiber=2.5, sugar=3.2,
            vitamin_a=5.0, vitamin_c=36.6, vitamin_e=0.15, vitamin_k=76.0,
            vitamin_b1=0.06, vitamin_b2=0.04, vitamin_b3=0.23,
            vitamin_b5=0.21, vitamin_b6=0.12, vitamin_b9=43.0,
            calcium=40.0, phosphorus=26.0, magnesium=12.0,
            potassium=170.0, sodium=18.0,
            iron=0.47, zinc=0.18, selenium=0.3,
            copper=0.02, manganese=0.16, omega3=0.1,
        ),
    },
    {
        "names": ["羽衣甘蓝", "kale"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=4.3, fat=0.9, carbohydrates=8.8, fiber=3.6,
            vitamin_a=241.0, vitamin_c=93.4, vitamin_e=1.54, vitamin_k=817.0,
            vitamin_b1=0.11, vitamin_b2=0.13, vitamin_b3=1.0,
            vitamin_b5=0.09, vitamin_b6=0.27, vitamin_b9=141.0,
            calcium=135.0, phosphorus=56.0, magnesium=34.0,
            potassium=447.0, sodium=38.0,
            iron=1.5, zinc=0.44, selenium=0.9,
            copper=0.2, manganese=0.77, omega3=0.2,
        ),
    },
    {
        "names": ["芦笋", "asparagus", "cooked asparagus"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=2.4, fat=0.2, carbohydrates=3.4, fiber=2.1,
            vitamin_a=75.0, vitamin_c=7.7, vitamin_e=1.1, vitamin_k=41.6,
            vitamin_b1=0.14, vitamin_b2=0.16, vitamin_b3=1.1,
            vitamin_b5=0.28, vitamin_b6=0.07, vitamin_b9=149.0,
            calcium=24.0, phosphorus=52.0, magnesium=14.0,
            potassium=202.0, sodium=2.0,
            iron=0.91, zinc=0.54, selenium=3.0,
            copper=0.16, manganese=0.16, chromium=1.0, omega3=0.05,
        ),
    },
    {
        "names": ["蘑菇", "mushroom", "mushrooms"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=3.1, fat=0.3, carbohydrates=3.3, fiber=1.0,
            vitamin_d=0.2,
            vitamin_b1=0.08, vitamin_b2=0.3, vitamin_b3=3.6,
            vitamin_b5=1.5, vitamin_b6=0.1, vitamin_b9=17.0,
            calcium=3.0, phosphorus=86.0, magnesium=9.0,
            potassium=318.0, sodium=5.0,
            iron=0.5, zinc=0.5, selenium=9.3,
            copper=0.32, manganese=0.05,
        ),
    },

    # ------------------------------------------------------------------ Fruits
    {
        "names": ["香蕉", "banana"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=1.1, fat=0.3, carbohydrates=23.0, fiber=2.6, sugar=12.2,
            vitamin_a=3.0, vitamin_c=8.7, vitamin_e=0.1, vitamin_k=0.5,
            vitamin_b1=0.03, vitamin_b2=0.07, vitamin_b3=0.67,
            vitamin_b5=0.33, vitamin_b6=0.37, vitamin_b7=3.1, vitamin_b9=20.0,
            calcium=5.0, phosphorus=22.0, magnesium=27.0,
            potassium=358.0, sodium=1.0,
            iron=0.26, zinc=0.15, selenium=1.0,
            copper=0.08, manganese=0.27, omega3=0.03,
        ),
    },
    {
        "names": ["橙子", "orange"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.9, fat=0.1, carbohydrates=12.0, fiber=2.4, sugar=9.4,
            vitamin_a=11.0, vitamin_c=53.2, vitamin_e=0.18,
            vitamin_b1=0.09, vitamin_b2=0.04, vitamin_b3=0.28,
            vitamin_b5=0.25, vitamin_b6=0.06, vitamin_b9=30.0,
            calcium=40.0, phosphorus=14.0, magnesium=10.0,
            potassium=181.0,
            iron=0.1, zinc=0.07, selenium=0.5,
            copper=0.05, manganese=0.02, omega3=0.01,
        ),
    },
    {
        "names": ["苹果", "apple"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.3, fat=0.2, carbohydrates=14.0, fiber=2.4, sugar=10.4,
            vitamin_a=3.0, vitamin_c=4.6, vitamin_e=0.18, vitamin_k=2.2,
            vitamin_b1=0.02, vitamin_b2=0.03, vitamin_b3=0.09,
            vitamin_b5=0.06, vitamin_b6=0.04, vitamin_b9=3.0,
            calcium=6.0, phosphorus=11.0, magnesium=5.0,
            potassium=107.0, sodium=1.0,
            iron=0.12, zinc=0.04,
            copper=0.03, manganese=0.04, omega3=0.01,
        ),
    },
    {
        "names": ["猕猴桃", "kiwifruit", "kiwi"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=1.1, fat=0.5, carbohydrates=15.0, fiber=3.0, sugar=8.7,
            vitamin_a=4.0, vitamin_c=93.0, vitamin_e=1.46, vitamin_k=40.3,
            vitamin_b1=0.03, vitamin_b2=0.02, vitamin_b3=0.34,
            vitamin_b5=0.18, vitamin_b6=0.06, vitamin_b7=0.6, vitamin_b9=25.0,
            calcium=34.0, phosphorus=34.0, magnesium=17.0,
            potassium=312.0, sodium=3.0,
            iron=0.31, zinc=0.14, selenium=0.2,
            copper=0.13, manganese=0.1, omega3=0.04,
        ),
    },
    {
        "names": ["草莓", "strawberry", "strawberries"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.7, fat=0.3, carbohydrates=7.7, fiber=2.0, sugar=4.9,
            vitamin_a=1.0, vitamin_c=58.8, vitamin_e=0.29, vitamin_k=2.2,
            vitamin_b1=0.02, vitamin_b2=0.02, vitamin_b3=0.39,
            vitamin_b5=0.13, vitamin_b6=0.05, vitamin_b9=24.0,
            calcium=16.0, phosphorus=24.0, magnesium=13.0,
            potassium=153.0, sodium=1.0,
            iron=0.41, zinc=0.14, selenium=0.4,
            copper=0.05, manganese=0.39, omega3=0.07,
        ),
    },
    {
        "names": ["牛油果", "avocado"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=2.0, fat=15.0, carbohydrates=9.0, fiber=6.7,
            vitamin_a=7.0, vitamin_c=10.0, vitamin_e=2.07, vitamin_k=21.0,
            vitamin_b1=0.07, vitamin_b2=0.13, vitamin_b3=1.74,
            vitamin_b5=1.39, vitamin_b6=0.26, vitamin_b7=3.1, vitamin_b9=81.0,
            calcium=12.0, phosphorus=52.0, magnesium=29.0,
            potassium=485.0, sodium=7.0,
            iron=0.55, zinc=0.64, selenium=0.4,
            copper=0.19, manganese=0.14, omega3=0.11,
        ),
    },
    {
        "names": ["梨", "pear"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=0.4, fat=0.1, carbohydrates=15.5, fiber=3.1, sugar=9.8,
            vitamin_a=1.0, vitamin_c=4.3, vitamin_k=4.4,
            vitamin_b1=0.01, vitamin_b2=0.03, vitamin_b3=0.16,
            vitamin_b5=0.05, vitamin_b6=0.03, vitamin_b9=7.0,
            calcium=9.0, phosphorus=12.0, magnesium=7.0,
            potassium=116.0, sodium=1.0,
            iron=0.18, zinc=0.1, selenium=0.1,
            copper=0.08, manganese=0.05, omega3=0.01,
        ),
    },

    # ------------------------------------------------------------------ Nuts & Seeds
    {
        "names": ["杏仁", "almonds", "almond"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=21.2, fat=50.0, carbohydrates=21.7, fiber=12.5,
            vitamin_e=25.6,
            vitamin_b1=0.21, vitamin_b2=1.01, vitamin_b3=3.62,
            vitamin_b5=0.47, vitamin_b6=0.14, vitamin_b7=64.0, vitamin_b9=44.0,
            calcium=264.0, phosphorus=484.0, magnesium=270.0,
            potassium=733.0, sodium=1.0,
            iron=3.7, zinc=3.1, selenium=4.1,
            copper=1.03, manganese=2.18,
        ),
    },
    {
        "names": ["核桃", "walnuts", "walnut"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=15.0, fat=65.0, carbohydrates=14.0, fiber=6.7,
            vitamin_a=1.0, vitamin_e=0.7,
            vitamin_b1=0.34, vitamin_b2=0.15, vitamin_b3=1.13,
            vitamin_b5=0.57, vitamin_b6=0.54, vitamin_b9=98.0,
            calcium=98.0, phosphorus=346.0, magnesium=158.0,
            potassium=441.0, sodium=2.0,
            iron=2.9, zinc=3.1, selenium=4.9,
            copper=1.59, manganese=3.41, omega3=9.08,
        ),
    },
    {
        "names": ["奇亚籽", "chia seeds", "chia"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=16.5, fat=30.7, carbohydrates=42.1, fiber=34.4,
            vitamin_a=54.0, vitamin_e=0.5,
            vitamin_b1=0.62, vitamin_b2=0.17, vitamin_b3=8.83,
            vitamin_b5=0.94, vitamin_b9=49.0,
            calcium=631.0, phosphorus=860.0, magnesium=335.0,
            potassium=407.0, sodium=16.0,
            iron=7.7, zinc=4.6, selenium=55.2,
            copper=0.92, manganese=2.72, omega3=17.8,
        ),
    },
    {
        "names": ["亚麻籽", "flaxseeds", "flax seeds", "linseed"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=18.3, fat=42.2, carbohydrates=28.9, fiber=27.3,
            vitamin_e=0.31,
            vitamin_b1=1.64, vitamin_b2=0.16, vitamin_b3=3.08,
            vitamin_b5=0.99, vitamin_b6=0.47, vitamin_b9=87.0,
            calcium=255.0, phosphorus=642.0, magnesium=392.0,
            potassium=813.0, sodium=30.0,
            iron=5.7, zinc=4.34, selenium=25.4,
            copper=1.22, manganese=2.48, omega3=22.8,
        ),
    },
    {
        "names": ["南瓜籽", "pumpkin seeds", "pepitas"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=19.4, fat=45.8, carbohydrates=17.8, fiber=6.0,
            vitamin_e=2.18, vitamin_k=7.3,
            vitamin_b1=0.23, vitamin_b2=0.32, vitamin_b3=4.99,
            vitamin_b5=0.75, vitamin_b6=0.14, vitamin_b9=57.0,
            calcium=46.0, phosphorus=1233.0, magnesium=592.0,
            potassium=919.0, sodium=7.0,
            iron=8.8, zinc=7.81, selenium=9.4,
            copper=1.39, manganese=4.54, omega3=0.1,
        ),
    },
    {
        "names": ["葵花籽", "sunflower seeds", "sunflower seed"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=20.8, fat=51.5, carbohydrates=20.0, fiber=8.6,
            vitamin_e=35.2,
            vitamin_b1=1.48, vitamin_b2=0.36, vitamin_b3=8.34,
            vitamin_b5=7.07, vitamin_b6=1.35, vitamin_b7=66.0, vitamin_b9=227.0,
            calcium=78.0, phosphorus=660.0, magnesium=325.0,
            potassium=645.0, sodium=9.0,
            iron=5.25, zinc=5.0, selenium=53.0,
            copper=1.83, manganese=1.95, omega3=0.07,
        ),
    },
    {
        "names": ["腰果", "cashews", "cashew"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=18.2, fat=43.9, carbohydrates=30.2, fiber=3.3, sugar=5.9,
            vitamin_e=0.9,
            vitamin_b1=0.42, vitamin_b2=0.06, vitamin_b3=1.4,
            vitamin_b5=0.86, vitamin_b6=0.42, vitamin_b9=25.0,
            calcium=37.0, phosphorus=593.0, magnesium=292.0,
            potassium=660.0, sodium=12.0,
            iron=6.7, zinc=5.6, selenium=19.9,
            copper=2.19, manganese=1.66, omega3=0.16,
        ),
    },
    {
        "names": ["花生", "peanuts", "peanut", "groundnuts"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=25.8, fat=49.2, carbohydrates=16.1, fiber=8.5, sugar=4.7,
            vitamin_e=8.33,
            vitamin_b1=0.64, vitamin_b2=0.13, vitamin_b3=13.8,
            vitamin_b5=1.77, vitamin_b6=0.35, vitamin_b7=34.0, vitamin_b9=240.0,
            calcium=92.0, phosphorus=376.0, magnesium=168.0,
            potassium=705.0, sodium=18.0,
            iron=4.6, zinc=3.3, selenium=7.2,
            copper=1.14, manganese=1.93,
        ),
    },
    {
        "names": ["巴西坚果", "brazil nut", "brazil nuts"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=14.3, fat=66.4, carbohydrates=11.7, fiber=7.5,
            vitamin_e=5.73,
            vitamin_b1=0.62, vitamin_b2=0.04, vitamin_b3=0.3,
            vitamin_b5=0.18, vitamin_b6=0.1, vitamin_b9=22.0,
            calcium=160.0, phosphorus=725.0, magnesium=376.0,
            potassium=659.0, sodium=3.0,
            iron=2.4, zinc=4.1, selenium=1917.0,
            copper=1.74, manganese=1.22, omega3=0.05,
        ),
    },

    # ------------------------------------------------------------------ Oils, Condiments & Special
    {
        "names": ["橄榄油", "olive oil"],
        "is_liquid": True,
        "density_g_per_ml": 0.91,
        "nutrients_per_100g": _n(
            fat=100.0,
            vitamin_e=14.4, vitamin_k=60.2,
            omega3=0.76,
        ),
    },
    {
        "names": ["葵花籽油", "sunflower oil"],
        "is_liquid": True,
        "density_g_per_ml": 0.92,
        "nutrients_per_100g": _n(
            fat=100.0,
            vitamin_e=41.1, vitamin_k=5.4,
            omega3=0.06,
        ),
    },
    {
        "names": ["食盐", "table salt", "salt"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            sodium=38000.0,
        ),
    },
    {
        "names": ["碘盐", "iodized salt"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            sodium=38000.0,
            iodine=4500.0,
        ),
    },
    {
        "names": ["酱油", "soy sauce"],
        "is_liquid": True,
        "density_g_per_ml": 1.18,
        "nutrients_per_100g": _n(
            protein=8.1, carbohydrates=8.1,
            sodium=5700.0,
            iron=2.4, manganese=0.4,
        ),
    },
    {
        "names": ["黑巧克力", "dark chocolate", "dark chocolate 70%"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=7.8, fat=43.1, carbohydrates=46.0, fiber=10.9, sugar=21.7,
            vitamin_e=0.59,
            vitamin_b1=0.06, vitamin_b2=0.08, vitamin_b3=0.43,
            vitamin_b5=0.4, vitamin_b9=8.0,
            calcium=73.0, phosphorus=308.0, magnesium=228.0,
            potassium=715.0, sodium=20.0,
            iron=11.9, zinc=3.3, selenium=6.8,
            copper=1.77, manganese=1.95, omega3=0.04,
        ),
    },
    {
        "names": ["海带", "kelp", "seaweed"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=1.7, fat=0.6, carbohydrates=9.6, fiber=1.3,
            vitamin_a=6.0, vitamin_c=3.0, vitamin_k=66.0,
            vitamin_b1=0.05, vitamin_b2=0.15, vitamin_b5=0.64, vitamin_b9=180.0,
            calcium=168.0, phosphorus=42.0, magnesium=121.0,
            potassium=89.0, sodium=233.0,
            iron=2.8, iodine=2984.0,
            copper=0.13, manganese=0.2,
        ),
    },

    # ------------------------------------------------------------------ Liquids
    {
        "names": ["橙汁", "orange juice"],
        "is_liquid": True,
        "density_g_per_ml": 1.04,
        "nutrients_per_100g": _n(
            protein=0.7, fat=0.2, carbohydrates=10.4, sugar=8.4,
            vitamin_a=10.0, vitamin_c=40.0,
            vitamin_b1=0.09, vitamin_b2=0.03, vitamin_b3=0.4,
            vitamin_b6=0.04, vitamin_b9=30.0,
            calcium=11.0, phosphorus=17.0, magnesium=11.0,
            potassium=200.0, sodium=1.0,
            iron=0.2, copper=0.04, chromium=2.2,
        ),
    },
    {
        "names": ["豆浆", "soy milk", "soymilk"],
        "is_liquid": True,
        "density_g_per_ml": 1.03,
        "nutrients_per_100g": _n(
            protein=3.3, fat=1.8, carbohydrates=3.0, fiber=0.3, sugar=1.5,
            vitamin_b1=0.04, vitamin_b2=0.02, vitamin_b3=0.3,
            vitamin_b5=0.12, vitamin_b6=0.06, vitamin_b9=18.0,
            calcium=25.0, phosphorus=49.0, magnesium=18.0,
            potassium=118.0, sodium=51.0,
            iron=0.6, zinc=0.3, selenium=3.0,
            copper=0.15, manganese=0.3, omega3=0.3,
        ),
    },
    {
        "names": ["绿茶", "green tea"],
        "is_liquid": True,
        "density_g_per_ml": 1.0,
        "nutrients_per_100g": _n(
            potassium=20.0, sodium=1.0,
            iron=0.02, manganese=0.3, fluoride=0.2,
        ),
    },
    {
        "names": ["红茶", "black tea"],
        "is_liquid": True,
        "density_g_per_ml": 1.0,
        "nutrients_per_100g": _n(
            potassium=37.0, sodium=3.0,
            iron=0.02, manganese=0.52, fluoride=0.37,
        ),
    },
    {
        "names": ["咖啡", "coffee"],
        "is_liquid": True,
        "density_g_per_ml": 1.0,
        "nutrients_per_100g": _n(
            vitamin_b2=0.19, vitamin_b3=0.43, vitamin_b5=0.27,
            potassium=115.0, sodium=2.0,
            iron=0.01, manganese=0.05,
        ),
    },
    {
        "names": ["燕麦粥", "oatmeal", "cooked oatmeal", "porridge"],
        "is_liquid": False,
        "nutrients_per_100g": _n(
            protein=2.4, fat=1.0, carbohydrates=12.0, fiber=1.7,
            vitamin_b1=0.1, vitamin_b5=0.2,
            calcium=9.0, phosphorus=77.0, magnesium=27.0,
            potassium=61.0, sodium=49.0,
            iron=0.8, zinc=0.6, selenium=4.6,
            copper=0.09, manganese=0.56, omega3=0.02,
        ),
    },
]


# ---------------------------------------------------------------------------
# Lookup index and function
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r'\(.*?\)', '', s)   # remove ASCII parentheses content
    s = re.sub(r'（.*?）', '', s)    # remove CJK parentheses content
    return s.strip()


# Build index once at module load
_INDEX: dict[str, dict] = {}
for _entry in FOOD_DB:
    for _name in _entry["names"]:
        _INDEX[_normalize(_name)] = _entry


def lookup_food(name: str) -> dict | None:
    """Look up a food entry by name.

    Performs normalization (lowercase, strip, remove parentheses content),
    then tries exact match, prefix/starts-with match, and finally substring match.

    Returns the matching food entry dict, or None if not found.
    """
    key = _normalize(name)
    if not key:
        return None

    # 1. Exact match
    if key in _INDEX:
        return _INDEX[key]

    # 2. Prefix match: one string starts with the other
    for k, entry in _INDEX.items():
        if k and (k.startswith(key) or key.startswith(k)):
            return entry

    # 3. Substring match: one string contained within the other
    for k, entry in _INDEX.items():
        if k and (key in k or k in key):
            return entry

    return None
