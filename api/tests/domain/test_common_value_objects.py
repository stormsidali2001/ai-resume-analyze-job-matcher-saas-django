"""
tests/domain/test_common_value_objects.py

Unit tests for domain/common/value_objects.py — Skill, MatchScore, Gap,
ImprovementSuggestion.
"""

import pytest

from domain.common.value_objects import (
    Gap,
    ImprovementSuggestion,
    InvalidMatchScoreError,
    MatchScore,
    Skill,
    VALID_PROFICIENCY_LEVELS,
)


# ============================================================
# Skill
# ============================================================


class TestSkill:
    @pytest.mark.parametrize("level", sorted(VALID_PROFICIENCY_LEVELS))
    def test_valid_skill_all_levels(self, level):
        s = Skill(name="Python", category="programming", proficiency_level=level)
        assert s.proficiency_level == level

    def test_normalised_name_is_lowercase(self):
        s = Skill(name="Python", category="programming", proficiency_level="expert")
        assert s.normalised_name == "python"

    def test_normalised_category_is_lowercase(self):
        s = Skill(name="Python", category="Programming", proficiency_level="expert")
        assert s.normalised_category == "programming"

    def test_matches_case_insensitive(self):
        a = Skill(name="Python", category="programming", proficiency_level="expert")
        b = Skill(name="PYTHON", category="PROGRAMMING", proficiency_level="beginner")
        assert a.matches(b)

    def test_does_not_match_different_name(self):
        a = Skill(name="Python", category="programming", proficiency_level="expert")
        b = Skill(name="Django", category="programming", proficiency_level="expert")
        assert not a.matches(b)

    def test_does_not_match_different_category(self):
        a = Skill(name="Python", category="backend", proficiency_level="expert")
        b = Skill(name="Python", category="frontend", proficiency_level="expert")
        assert not a.matches(b)

    @pytest.mark.parametrize("bad_name", ["", "   "])
    def test_rejects_empty_name(self, bad_name):
        with pytest.raises(Exception):
            Skill(name=bad_name, category="programming", proficiency_level="expert")

    @pytest.mark.parametrize("bad_cat", ["", "   "])
    def test_rejects_empty_category(self, bad_cat):
        with pytest.raises(Exception):
            Skill(name="Python", category=bad_cat, proficiency_level="expert")

    @pytest.mark.parametrize("bad_level", ["guru", "pro", "", "EXPERT"])
    def test_rejects_invalid_proficiency_level(self, bad_level):
        with pytest.raises(Exception):
            Skill(name="Python", category="programming", proficiency_level=bad_level)

    def test_equality_by_value(self):
        a = Skill(name="Python", category="programming", proficiency_level="expert")
        b = Skill(name="Python", category="programming", proficiency_level="expert")
        assert a == b

    def test_inequality_on_different_level(self):
        a = Skill(name="Python", category="programming", proficiency_level="expert")
        b = Skill(name="Python", category="programming", proficiency_level="beginner")
        assert a != b

    def test_immutability(self):
        s = Skill(name="Python", category="programming", proficiency_level="expert")
        with pytest.raises(Exception):
            s.name = "Go"  # type: ignore[misc]

    def test_hashable(self):
        s = Skill(name="Python", category="programming", proficiency_level="expert")
        assert hash(s) is not None
        skill_set = {s}
        assert s in skill_set


# ============================================================
# MatchScore
# ============================================================


class TestMatchScore:
    @pytest.mark.parametrize("value", [0, 1, 50, 99, 100])
    def test_valid_scores(self, value):
        ms = MatchScore(value=value)
        assert ms.value == value

    @pytest.mark.parametrize("bad", [-1, 101, 200, -100])
    def test_rejects_out_of_range(self, bad):
        with pytest.raises(InvalidMatchScoreError):
            MatchScore(value=bad)

    @pytest.mark.parametrize(
        "value,label",
        [(80, "strong"), (60, "acceptable"), (30, "weak"), (10, "poor")],
    )
    def test_label(self, value, label):
        assert MatchScore(value=value).label == label

    def test_is_strong(self):
        assert MatchScore(value=75).is_strong
        assert not MatchScore(value=74).is_strong

    def test_is_acceptable(self):
        assert MatchScore(value=50).is_acceptable
        assert not MatchScore(value=49).is_acceptable

    def test_equality(self):
        assert MatchScore(value=80) == MatchScore(value=80)

    def test_immutability(self):
        ms = MatchScore(value=80)
        with pytest.raises(Exception):
            ms.value = 90  # type: ignore[misc]


# ============================================================
# Gap
# ============================================================


class TestGap:
    def test_valid(self):
        g = Gap(gap_type="missing_skill", description="Python not found.")
        assert g.gap_type == "missing_skill"

    @pytest.mark.parametrize("bad", ["", "   "])
    def test_rejects_empty_type(self, bad):
        with pytest.raises(Exception):
            Gap(gap_type=bad, description="desc")

    @pytest.mark.parametrize("bad", ["", "   "])
    def test_rejects_empty_description(self, bad):
        with pytest.raises(Exception):
            Gap(gap_type="type", description=bad)

    def test_equality(self):
        assert Gap(gap_type="t", description="d") == Gap(gap_type="t", description="d")


# ============================================================
# ImprovementSuggestion
# ============================================================


class TestImprovementSuggestion:
    def test_valid(self):
        s = ImprovementSuggestion(text="Learn Python.", priority="high", category="skills")
        assert s.priority == "high"

    @pytest.mark.parametrize("bad_priority", ["urgent", "critical", "", "MEDIUM"])
    def test_rejects_invalid_priority(self, bad_priority):
        with pytest.raises(Exception):
            ImprovementSuggestion(text="text", priority=bad_priority, category="skills")

    @pytest.mark.parametrize("bad_text", ["", "   "])
    def test_rejects_empty_text(self, bad_text):
        with pytest.raises(Exception):
            ImprovementSuggestion(text=bad_text, priority="high", category="skills")

    @pytest.mark.parametrize("bad_cat", ["", "   "])
    def test_rejects_empty_category(self, bad_cat):
        with pytest.raises(Exception):
            ImprovementSuggestion(text="text", priority="high", category=bad_cat)

    def test_equality(self):
        assert (
            ImprovementSuggestion(text="t", priority="low", category="c")
            == ImprovementSuggestion(text="t", priority="low", category="c")
        )
