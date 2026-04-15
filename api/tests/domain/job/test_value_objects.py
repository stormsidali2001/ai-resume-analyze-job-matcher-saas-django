"""
tests/domain/job/test_value_objects.py

Unit tests for domain/job/value_objects.py
"""

import pytest

from domain.job.value_objects import (
    CompanyName,
    EmploymentType,
    JobDescription,
    JobTitle,
    Location,
    SalaryRange,
)


# ============================================================
# JobTitle
# ============================================================


class TestJobTitle:
    @pytest.mark.parametrize("title", ["Software Engineer", "Senior Python Dev", "CTO"])
    def test_valid_title(self, title):
        jt = JobTitle(value=title)
        assert jt.value == title
        assert str(jt) == title

    @pytest.mark.parametrize("bad", ["", "   "])
    def test_rejects_empty(self, bad):
        with pytest.raises(Exception):
            JobTitle(value=bad)

    def test_equality(self):
        assert JobTitle(value="Engineer") == JobTitle(value="Engineer")

    def test_inequality(self):
        assert JobTitle(value="Engineer") != JobTitle(value="Manager")

    def test_immutability(self):
        jt = JobTitle(value="Dev")
        with pytest.raises(Exception):
            jt.value = "changed"  # type: ignore[misc]


# ============================================================
# CompanyName
# ============================================================


class TestCompanyName:
    def test_valid(self):
        cn = CompanyName(value="Acme Corp")
        assert cn.value == "Acme Corp"

    @pytest.mark.parametrize("bad", ["", "   "])
    def test_rejects_empty(self, bad):
        with pytest.raises(Exception):
            CompanyName(value=bad)

    def test_equality(self):
        assert CompanyName(value="A") == CompanyName(value="A")

    def test_str(self):
        assert str(CompanyName(value="TechCo")) == "TechCo"


# ============================================================
# Location
# ============================================================


class TestLocation:
    def test_valid_non_remote(self):
        loc = Location(city="London", country="UK", remote=False)
        assert loc.city == "London"
        assert not loc.remote

    def test_valid_remote(self):
        loc = Location(city="Berlin", country="Germany", remote=True)
        assert loc.remote
        assert "Remote" in loc.display

    def test_display_non_remote(self):
        loc = Location(city="Paris", country="France")
        assert loc.display == "Paris, France"

    def test_display_remote(self):
        loc = Location(city="Austin", country="USA", remote=True)
        assert loc.display == "Austin, USA (Remote)"

    @pytest.mark.parametrize("bad_city", ["", "   "])
    def test_rejects_empty_city(self, bad_city):
        with pytest.raises(Exception):
            Location(city=bad_city, country="USA")

    @pytest.mark.parametrize("bad_country", ["", "   "])
    def test_rejects_empty_country(self, bad_country):
        with pytest.raises(Exception):
            Location(city="NYC", country=bad_country)

    def test_equality(self):
        assert Location(city="A", country="B") == Location(city="A", country="B")

    def test_inequality_remote_flag(self):
        assert Location(city="A", country="B", remote=True) != Location(city="A", country="B", remote=False)


# ============================================================
# EmploymentType
# ============================================================


class TestEmploymentType:
    @pytest.mark.parametrize(
        "et,value",
        [
            (EmploymentType.FULL_TIME, "full_time"),
            (EmploymentType.PART_TIME, "part_time"),
            (EmploymentType.CONTRACT, "contract"),
            (EmploymentType.FREELANCE, "freelance"),
            (EmploymentType.INTERNSHIP, "internship"),
        ],
    )
    def test_all_variants(self, et, value):
        assert et.value == value

    def test_equality(self):
        assert EmploymentType.FULL_TIME == EmploymentType.FULL_TIME

    def test_inequality(self):
        assert EmploymentType.FULL_TIME != EmploymentType.PART_TIME


# ============================================================
# SalaryRange
# ============================================================


class TestSalaryRange:
    def test_valid_range(self):
        sr = SalaryRange(min_salary=50_000, max_salary=80_000, currency="USD")
        assert sr.min_salary == 50_000
        assert sr.max_salary == 80_000

    def test_equal_min_max_is_valid(self):
        sr = SalaryRange(min_salary=60_000, max_salary=60_000)
        assert sr.midpoint == 60_000

    def test_midpoint(self):
        sr = SalaryRange(min_salary=50_000, max_salary=90_000)
        assert sr.midpoint == 70_000

    def test_display(self):
        sr = SalaryRange(min_salary=50_000, max_salary=80_000, currency="GBP")
        assert "GBP" in sr.display
        assert "50,000" in sr.display

    def test_rejects_negative_min(self):
        with pytest.raises(Exception):
            SalaryRange(min_salary=-1, max_salary=50_000)

    def test_rejects_max_less_than_min(self):
        with pytest.raises(Exception):
            SalaryRange(min_salary=80_000, max_salary=50_000)

    def test_rejects_empty_currency(self):
        with pytest.raises(Exception):
            SalaryRange(min_salary=50_000, max_salary=80_000, currency="")

    @pytest.mark.parametrize(
        "min_s,max_s",
        [(0, 0), (0, 100_000), (1, 2), (100_000, 200_000)],
    )
    def test_valid_ranges(self, min_s, max_s):
        sr = SalaryRange(min_salary=min_s, max_salary=max_s)
        assert sr.min_salary == min_s

    def test_equality(self):
        assert SalaryRange(min_salary=50_000, max_salary=80_000) == SalaryRange(min_salary=50_000, max_salary=80_000)


# ============================================================
# JobDescription
# ============================================================


class TestJobDescription:
    def test_valid_description(self):
        text = "We are looking for a skilled Python developer. " * 5
        jd = JobDescription(text=text)
        assert jd.text == text

    def test_preview_truncates(self):
        jd = JobDescription(text="x" * 300)
        assert len(jd.preview) == 200

    @pytest.mark.parametrize("bad", ["", "   ", "too short"])
    def test_rejects_short_description(self, bad):
        with pytest.raises(Exception):
            JobDescription(text=bad)

    def test_exact_min_length_is_accepted(self):
        text = "x" * 100
        jd = JobDescription(text=text)
        assert jd.text == text

    def test_one_below_min_rejected(self):
        with pytest.raises(Exception):
            JobDescription(text="x" * 99)

    def test_equality(self):
        text = "y" * 100
        assert JobDescription(text=text) == JobDescription(text=text)
