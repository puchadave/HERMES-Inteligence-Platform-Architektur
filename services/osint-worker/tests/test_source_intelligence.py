from app.source_intelligence import parse_github_repository


def test_parses_repository_url() -> None:
    assert parse_github_repository("https://github.com/OpenOSINT/OpenOSINT") == ("OpenOSINT", "OpenOSINT")


def test_strips_git_suffix_and_ignores_trailing_path() -> None:
    assert parse_github_repository("Review https://github.com/github/github-mcp-server.git/tree/main/docs") == (
        "github",
        "github-mcp-server",
    )


def test_non_github_value_returns_none() -> None:
    assert parse_github_repository("https://example.org/repo") is None
