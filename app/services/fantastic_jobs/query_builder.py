"""Convert a list of job titles into the appropriate title_filter or advanced_title_filter."""

import re


def build_title_filter(
    titles: list[str],
    title_filter_override: str | None = None,
    advanced_title_filter_override: str | None = None,
) -> tuple[str | None, str | None]:
    """Build the appropriate title filter from a list of titles.

    Returns:
        (title_filter, advanced_title_filter) — exactly one will be non-None.
        title_filter is used for simple single-title queries.
        advanced_title_filter is used for multi-title or complex queries.
    """
    # If user explicitly set a filter, respect it
    if advanced_title_filter_override:
        return (None, advanced_title_filter_override)
    if title_filter_override:
        return (title_filter_override, None)

    # Single simple title → use regular title_filter (Google-style)
    if len(titles) == 1 and _is_simple_title(titles[0]):
        return (f'"{titles[0]}"', None)

    # Single complex title → still use title_filter with quotes
    if len(titles) == 1:
        return (f'"{titles[0]}"', None)

    # Multiple titles → build advanced_title_filter with OR (|)
    expressions = []
    for title in titles:
        title = title.strip()
        if not title:
            continue

        words = title.split()
        if len(words) > 1:
            # Multi-word: use single quotes to make it a phrase
            expressions.append(f"'{title}'")
        else:
            expressions.append(title)

    advanced = " | ".join(expressions)
    return (None, advanced)


def _is_simple_title(title: str) -> bool:
    """A title is simple if it's 1-4 common words with no special chars."""
    words = title.strip().split()
    if not (1 <= len(words) <= 4):
        return False
    # Check for special characters that might need advanced operators
    return not bool(re.search(r"[&|!<>()/:*]", title))


def format_comma_list(values: list[str]) -> str:
    """Format a list as comma-delimited string with no spaces (API requirement)."""
    return ",".join(v.strip() for v in values if v.strip())


def format_taxonomy_list(taxonomies: list[str]) -> str:
    """Format taxonomies, double-quoting those containing '&'."""
    formatted = []
    for t in taxonomies:
        t = t.strip()
        if "&" in t:
            formatted.append(f'"{t}"')
        else:
            formatted.append(t)
    return ",".join(formatted)
