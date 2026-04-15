"""
tests/domain/matching/test_aggregate.py

Unit tests for MatchResult aggregate and common matching VOs.
"""

import pytest

from domain.common.value_objects import Gap, ImprovementSuggestion, MatchScore
from domain.matching.aggregate import MatchResult


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def gap():
    return Gap(gap_type="missing_skill", description="Python is missing.")


@pytest.fixture
def suggestion():
    return ImprovementSuggestion(
        text="Learn Python.", priority="high", category="skills"
    )


@pytest.fixture
def match_result(gap, suggestion):
    return MatchResult.create(
        match_id="match-001",
        resume_id="resume-001",
        job_id="job-001",
        score=MatchScore(value=72),
        gaps=[gap],
        suggestions=[suggestion],
    )


# ============================================================
# MatchResult.create factory
# ============================================================


class TestMatchResultCreate:
    def test_creates_successfully(self, match_result):
        assert match_result.match_id == "match-001"
        assert match_result.resume_id == "resume-001"
        assert match_result.job_id == "job-001"
        assert match_result.score.value == 72

    def test_gaps_are_stored(self, match_result, gap):
        assert gap in match_result.gaps

    def test_suggestions_are_stored(self, match_result, suggestion):
        assert suggestion in match_result.suggestions

    @pytest.mark.parametrize("bad_id", ["", "   "])
    def test_rejects_empty_match_id(self, bad_id):
        with pytest.raises(ValueError):
            MatchResult.create(
                match_id=bad_id,
                resume_id="r1",
                job_id="j1",
                score=MatchScore(value=50),
                gaps=[],
                suggestions=[],
            )

    @pytest.mark.parametrize("bad_id", ["", "   "])
    def test_rejects_empty_resume_id(self, bad_id):
        with pytest.raises(ValueError):
            MatchResult.create(
                match_id="m1",
                resume_id=bad_id,
                job_id="j1",
                score=MatchScore(value=50),
                gaps=[],
                suggestions=[],
            )

    @pytest.mark.parametrize("bad_id", ["", "   "])
    def test_rejects_empty_job_id(self, bad_id):
        with pytest.raises(ValueError):
            MatchResult.create(
                match_id="m1",
                resume_id="r1",
                job_id=bad_id,
                score=MatchScore(value=50),
                gaps=[],
                suggestions=[],
            )


# ============================================================
# Properties
# ============================================================


class TestMatchResultProperties:
    def test_has_gaps_true(self, match_result):
        assert match_result.has_gaps is True

    def test_has_gaps_false_when_empty(self):
        mr = MatchResult.create(
            match_id="m1", resume_id="r1", job_id="j1",
            score=MatchScore(value=90), gaps=[], suggestions=[]
        )
        assert mr.has_gaps is False

    def test_high_priority_suggestions(self, suggestion):
        low = ImprovementSuggestion(text="Do something.", priority="low", category="general")
        mr = MatchResult.create(
            match_id="m1", resume_id="r1", job_id="j1",
            score=MatchScore(value=60), gaps=[],
            suggestions=[suggestion, low],
        )
        high_only = mr.high_priority_suggestions
        assert len(high_only) == 1
        assert high_only[0].priority == "high"

    def test_gaps_returns_defensive_copy(self, match_result, gap):
        copy = match_result.gaps
        copy.clear()
        assert len(match_result.gaps) == 1

    def test_suggestions_returns_defensive_copy(self, match_result):
        copy = match_result.suggestions
        copy.clear()
        assert len(match_result.suggestions) == 1

    def test_calculated_at_is_set(self, match_result):
        assert match_result.calculated_at is not None

    def test_repr(self, match_result):
        r = repr(match_result)
        assert "match-001" in r
        assert "72" in r


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
        from domain.common.value_objects import InvalidMatchScoreError
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
