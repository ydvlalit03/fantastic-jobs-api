"""Tests for the query builder service."""

from app.services.fantastic_jobs.query_builder import (
    build_title_filter,
    format_comma_list,
    format_taxonomy_list,
)


class TestBuildTitleFilter:
    def test_single_simple_title(self):
        tf, atf = build_title_filter(["Software Engineer"])
        assert tf == '"Software Engineer"'
        assert atf is None

    def test_single_complex_title_with_special_chars(self):
        tf, atf = build_title_filter(["Engineer/Developer"])
        assert tf == '"Engineer/Developer"'
        assert atf is None

    def test_multiple_titles_builds_advanced_filter(self):
        tf, atf = build_title_filter(["Software Engineer", "Backend Developer"])
        assert tf is None
        assert atf == "'Software Engineer' | 'Backend Developer'"

    def test_multiple_titles_single_word(self):
        tf, atf = build_title_filter(["Engineer", "Developer"])
        assert tf is None
        assert atf == "Engineer | Developer"

    def test_multiple_titles_mixed(self):
        tf, atf = build_title_filter(["Engineer", "Backend Developer"])
        assert tf is None
        assert atf == "Engineer | 'Backend Developer'"

    def test_title_filter_override(self):
        tf, atf = build_title_filter(
            ["ignored"], title_filter_override="my custom filter"
        )
        assert tf == "my custom filter"
        assert atf is None

    def test_advanced_title_filter_override(self):
        tf, atf = build_title_filter(
            ["ignored"], advanced_title_filter_override="foo | bar & baz"
        )
        assert tf is None
        assert atf == "foo | bar & baz"

    def test_advanced_override_takes_precedence(self):
        tf, atf = build_title_filter(
            ["ignored"],
            title_filter_override="simple",
            advanced_title_filter_override="complex",
        )
        assert tf is None
        assert atf == "complex"

    def test_empty_titles_in_list_are_skipped(self):
        tf, atf = build_title_filter(["Engineer", "", "Developer"])
        assert tf is None
        assert "Engineer" in atf
        assert "Developer" in atf


class TestFormatCommaList:
    def test_basic(self):
        assert format_comma_list(["a", "b", "c"]) == "a,b,c"

    def test_strips_whitespace(self):
        assert format_comma_list([" a ", " b "]) == "a,b"

    def test_skips_empty(self):
        assert format_comma_list(["a", "", "b"]) == "a,b"


class TestFormatTaxonomyList:
    def test_basic(self):
        assert format_taxonomy_list(["Tech", "Finance"]) == "Tech,Finance"

    def test_quotes_ampersand(self):
        result = format_taxonomy_list(["Science & Tech", "Finance"])
        assert result == '"Science & Tech",Finance'
