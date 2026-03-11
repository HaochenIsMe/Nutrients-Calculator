#!/usr/bin/env python3
"""
dish_recommender.py – Gap-filling dish recommendation engine.

Algorithm:
  For each nutrient in SCORING_KEYS:
    gap_weight = max(0, gap / rda)   # how urgently this nutrient is needed
    contribution = min(dish_amount, gap) / rda  # how much this dish fills the gap

  score(dish) = sum(contribution × gap_weight for all scoring keys)

Higher score = dish best fills current nutritional gaps.
"""

from __future__ import annotations

from dish_database import list_dishes, DISH_NUTRIENT_KEYS

# User-visible scoring nutrients (no trace minerals)
SCORING_KEYS: list[str] = [
    "protein", "fat", "carbohydrates", "fiber",
    "vitamin_a", "vitamin_c", "vitamin_d",
    "calcium", "iron", "potassium",
]


def compute_gaps(today_totals: dict[str, float],
                 get_rda: callable) -> dict[str, float]:
    """
    Return {key: gap} for each SCORING_KEY where gap > 0.
    gap = rda - actual (clamped to ≥ 0).
    """
    gaps: dict[str, float] = {}
    for key in SCORING_KEYS:
        rda    = get_rda(key)
        actual = float(today_totals.get(key, 0.0))
        gap    = max(0.0, rda - actual)
        gaps[key] = gap
    return gaps


def score_dish(dish: dict, gaps: dict[str, float],
               get_rda: callable) -> float:
    """
    Score a dish against current nutritional gaps.
    Returns a float; higher = better.
    """
    nutrients = dish.get("nutrients", {})
    total = 0.0
    for key in SCORING_KEYS:
        rda = get_rda(key)
        if rda <= 0:
            continue
        gap        = gaps.get(key, 0.0)
        gap_weight = gap / rda                       # 0 → not needed, 1 → fully missing
        dish_amt   = float(nutrients.get(key, 0.0))
        contribution = min(dish_amt, gap) / rda      # fraction of RDA filled
        total += contribution * gap_weight
    return total


def recommend_dishes(today_totals: dict[str, float],
                     get_rda: callable,
                     top_n: int = 5) -> list[dict]:
    """
    Return up to `top_n` dishes ranked by score (descending).
    Each item: {"dish": ..., "score": float, "top_gaps_filled": [(key, pct), ...]}
    """
    gaps   = compute_gaps(today_totals, get_rda)
    dishes = list_dishes()

    scored: list[tuple[float, dict]] = []
    for dish in dishes:
        s = score_dish(dish, gaps, get_rda)
        scored.append((s, dish))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for s, dish in scored[:top_n]:
        nutrients = dish.get("nutrients", {})
        # Which gaps does this dish fill most (top 3)?
        filled = []
        for key in SCORING_KEYS:
            rda = get_rda(key)
            if rda <= 0:
                continue
            gap     = gaps.get(key, 0.0)
            dish_v  = float(nutrients.get(key, 0.0))
            pct     = min(dish_v, gap) / rda * 100 if rda > 0 else 0
            if pct > 1:
                filled.append((key, pct))
        filled.sort(key=lambda x: x[1], reverse=True)
        results.append({
            "dish":             dish,
            "score":            s,
            "top_gaps_filled":  filled[:3],
        })
    return results
