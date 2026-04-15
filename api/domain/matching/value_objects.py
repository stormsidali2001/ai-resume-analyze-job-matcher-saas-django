"""
domain/matching/value_objects.py

Re-exports shared value objects used by the Matching bounded context.
Gap, ImprovementSuggestion, and MatchScore all live in domain/common
because they are shared across contexts. This module provides a
convenient single import point for matching consumers.
"""

from domain.common.value_objects import (  # noqa: F401
    Gap,
    ImprovementSuggestion,
    MatchScore,
    Skill,
)
