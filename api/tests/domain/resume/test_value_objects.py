"""
tests/domain/resume/test_value_objects.py

Full unit tests for domain/resume/value_objects.py
"""

import pytest

from domain.resume.value_objects import (
    ContactInfo,
    Education,
    Experience,
    RawResumeContent,
)


# ============================================================
# RawResumeContent
# ============================================================


class TestRawResumeContent:
    def test_valid_content_is_created(self):
        text = "A" * 50
        rc = RawResumeContent(text=text)
        assert rc.text == text

    def test_long_text_is_accepted(self):
        text = "Python developer with 5 years of experience in backend systems." * 5
        rc = RawResumeContent(text=text)
        assert rc.word_count > 0

    @pytest.mark.parametrize(
        "bad_text",
        [
            "",
            "   ",
            "too short",
            "x" * 49,
        ],
    )
    def test_rejects_invalid_text(self, bad_text):
        with pytest.raises(Exception):
            RawResumeContent(text=bad_text)

    def test_word_count(self):
        rc = RawResumeContent(text="hello world " * 10)
        assert rc.word_count == 20

    def test_preview_truncates_at_120_chars(self):
        rc = RawResumeContent(text="x" * 200)
        assert len(rc.preview) == 120

    def test_preview_of_short_content(self):
        text = "Senior engineer with Python skills and 8 years of experience building APIs."
        rc = RawResumeContent(text=text)
        assert rc.preview == text.strip()

    def test_immutability(self):
        rc = RawResumeContent(text="A" * 50)
        with pytest.raises(Exception):
            rc.text = "changed"  # type: ignore[misc]

    def test_equality_by_value(self):
        text = "A" * 50
        assert RawResumeContent(text=text) == RawResumeContent(text=text)

    def test_inequality_on_different_text(self):
        assert RawResumeContent(text="A" * 50) != RawResumeContent(text="B" * 50)


# ============================================================
# ContactInfo
# ============================================================


class TestContactInfo:
    def _valid(self, **overrides):
        defaults = {
            "email": "alice@example.com",
            "phone": "+1-555-0100",
            "location": "New York, USA",
        }
        defaults.update(overrides)
        return ContactInfo(**defaults)

    def test_valid_contact_info(self):
        ci = self._valid()
        assert ci.email == "alice@example.com"
        assert ci.phone == "+1-555-0100"
        assert ci.location == "New York, USA"

    @pytest.mark.parametrize("bad_email", ["", "   ", "not-an-email", "nodomain"])
    def test_rejects_invalid_email(self, bad_email):
        with pytest.raises(Exception):
            self._valid(email=bad_email)

    @pytest.mark.parametrize("bad_phone", ["", "   "])
    def test_rejects_empty_phone(self, bad_phone):
        with pytest.raises(Exception):
            self._valid(phone=bad_phone)

    @pytest.mark.parametrize("bad_location", ["", "   "])
    def test_rejects_empty_location(self, bad_location):
        with pytest.raises(Exception):
            self._valid(location=bad_location)

    def test_equality_by_value(self):
        assert self._valid() == self._valid()

    def test_inequality(self):
        assert self._valid(email="a@b.com") != self._valid(email="c@d.com")

    def test_immutability(self):
        ci = self._valid()
        with pytest.raises(Exception):
            ci.email = "x@y.com"  # type: ignore[misc]


# ============================================================
# Experience
# ============================================================


class TestExperience:
    def _valid(self, **overrides):
        defaults = {
            "role": "Software Engineer",
            "company": "Acme Corp",
            "duration_months": 24,
            "responsibilities": ["Built REST APIs", "Led code reviews"],
        }
        defaults.update(overrides)
        return Experience(**defaults)

    def test_valid_experience(self):
        exp = self._valid()
        assert exp.role == "Software Engineer"
        assert exp.duration_months == 24
        assert isinstance(exp.responsibilities, tuple)

    def test_list_converted_to_tuple(self):
        exp = self._valid(responsibilities=["a", "b"])
        assert isinstance(exp.responsibilities, tuple)
        assert exp.responsibilities == ("a", "b")

    def test_tuple_input_accepted(self):
        exp = self._valid(responsibilities=("a",))
        assert exp.responsibilities == ("a",)

    def test_zero_duration_is_valid(self):
        exp = self._valid(duration_months=0)
        assert exp.duration_months == 0

    def test_duration_years_calculation(self):
        exp = self._valid(duration_months=18)
        assert exp.duration_years == 1.5

    @pytest.mark.parametrize("bad_role", ["", "   "])
    def test_rejects_empty_role(self, bad_role):
        with pytest.raises(Exception):
            self._valid(role=bad_role)

    @pytest.mark.parametrize("bad_company", ["", "   "])
    def test_rejects_empty_company(self, bad_company):
        with pytest.raises(Exception):
            self._valid(company=bad_company)

    def test_rejects_negative_duration(self):
        with pytest.raises(Exception):
            self._valid(duration_months=-1)

    def test_equality_by_value(self):
        assert self._valid() == self._valid()

    def test_inequality_on_different_role(self):
        assert self._valid(role="A") != self._valid(role="B")

    def test_immutability(self):
        exp = self._valid()
        with pytest.raises(Exception):
            exp.role = "changed"  # type: ignore[misc]

    @pytest.mark.parametrize(
        "months,expected_years",
        [(12, 1.0), (6, 0.5), (36, 3.0), (1, 0.1)],
    )
    def test_duration_years_parametrize(self, months, expected_years):
        exp = self._valid(duration_months=months)
        assert exp.duration_years == expected_years


# ============================================================
# Education
# ============================================================


class TestEducation:
    def _valid(self, **overrides):
        defaults = {
            "degree": "B.Sc. Computer Science",
            "institution": "MIT",
            "graduation_year": 2020,
        }
        defaults.update(overrides)
        return Education(**defaults)

    def test_valid_education(self):
        edu = self._valid()
        assert edu.degree == "B.Sc. Computer Science"
        assert edu.graduation_year == 2020

    @pytest.mark.parametrize("bad_degree", ["", "   "])
    def test_rejects_empty_degree(self, bad_degree):
        with pytest.raises(Exception):
            self._valid(degree=bad_degree)

    @pytest.mark.parametrize("bad_institution", ["", "   "])
    def test_rejects_empty_institution(self, bad_institution):
        with pytest.raises(Exception):
            self._valid(institution=bad_institution)

    @pytest.mark.parametrize("bad_year", [1899, 2101, 0, -1])
    def test_rejects_out_of_range_year(self, bad_year):
        with pytest.raises(Exception):
            self._valid(graduation_year=bad_year)

    @pytest.mark.parametrize("good_year", [1900, 2024, 2100])
    def test_accepts_boundary_years(self, good_year):
        edu = self._valid(graduation_year=good_year)
        assert edu.graduation_year == good_year

    def test_equality_by_value(self):
        assert self._valid() == self._valid()

    def test_inequality(self):
        assert self._valid(graduation_year=2019) != self._valid(graduation_year=2020)

    def test_immutability(self):
        edu = self._valid()
        with pytest.raises(Exception):
            edu.degree = "PhD"  # type: ignore[misc]
