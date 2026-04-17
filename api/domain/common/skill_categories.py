"""
domain/common/skill_categories.py

Canonical skill category taxonomy used across the application:
- AI parsing (constrains Gemini structured output)
- Scoring (category weights for match calculation)
- Frontend (via API response + shared constants)

Priority order: 1 = most important for technical role matching.
"""

from __future__ import annotations

from typing import Final

# Priority order (1 = highest, 10 = lowest)
CATEGORY_PRIORITY: Final[dict[str, int]] = {
    "language":     1,
    "framework":    2,
    "database":     3,
    "cloud":        4,
    "devops":       5,
    "architecture": 6,
    "data-science": 7,
    "tooling":      8,
    "testing":      9,
    "methodology":  10,
}

# Score weights used in skill matching (higher = missing this skill hurts more)
CATEGORY_SCORE_WEIGHT: Final[dict[str, float]] = {
    "language":     3.0,
    "framework":    2.5,
    "database":     2.0,
    "cloud":        1.5,
    "devops":       1.5,
    "architecture": 1.5,
    "data-science": 1.5,
    "tooling":      1.0,
    "testing":      1.0,
    "methodology":  0.5,
}

# Ordered tuple of all valid category values (priority order)
CANONICAL_CATEGORIES: Final[tuple[str, ...]] = tuple(CATEGORY_PRIORITY)

# Fallback weight for any skill whose category is not in the taxonomy
DEFAULT_WEIGHT: Final[float] = 1.0
