"""Tests for HTML parsing."""

from scraper.parser import parse_page


def test_parse_page_extracts_metadata_and_links() -> None:
    html = """
    <html>
      <head>
        <title>Example title</title>
        <meta name="description" content="A useful summary" />
        <link rel="canonical" href="/canonical-page" />
        <meta property="article:published_time" content="2024-01-15" />
      </head>
      <body>
        <nav><a href="/about">About</a></nav>
        <main>
          <h1>Headline</h1>
          <a href="/blog/post">Read more</a>
        </main>
      </body>
    </html>
    """

    parsed = parse_page(html, "https://example.com/start", "https://example.com/start")

    assert parsed.title == "Example title"
    assert parsed.meta_description == "A useful summary"
    assert parsed.publication_date == "2024-01-15"
    assert parsed.canonical_url == "https://example.com/canonical-page"
    assert {link.url for link in parsed.links} == {
        "https://example.com/about",
        "https://example.com/blog/post",
    }

