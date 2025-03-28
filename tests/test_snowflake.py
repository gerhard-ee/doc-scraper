import pytest
from unittest.mock import patch, MagicMock
from doc_scraper.snowflake_handler import SnowflakeDocScraper
from doc_scraper.config import ScraperConfig

@pytest.fixture
def snowflake_scraper():
    config = ScraperConfig(
        verbose_progress=True,
        max_workers=2,  # Reduce workers for testing
        timeout=10      # Lower timeout for testing
    )
    return SnowflakeDocScraper(config)

@pytest.mark.parametrize("url", [
    "https://docs.snowflake.com/en/reference",
    "https://docs.snowflake.com/en/sql-reference",
])
def test_is_snowflake_url(snowflake_scraper, url):
    """Test URL identification for Snowflake domains."""
    assert snowflake_scraper.is_snowflake_url(url) is True
    assert snowflake_scraper.is_snowflake_url("https://example.com") is False

def test_snowflake_filter_urls(snowflake_scraper):
    """Test URL filtering for Snowflake documentation."""
    test_urls = [
        "https://docs.snowflake.com/en/reference/intro",
        "https://docs.snowflake.com/en/archive/old-page",  # Should be filtered out
        "https://docs.snowflake.com/en/reference/sql/create-table",
        "https://example.com/page",  # Should be filtered out
        "https://docs.snowflake.com/en/release-notes/2023"  # Should be filtered out
    ]
    
    # Add these URLs to visited to test filtering
    for url in test_urls:
        snowflake_scraper.visited_urls.add(url)
        
    # Mock _is_valid_url to return True for all URLs in this test
    with patch.object(snowflake_scraper, '_is_valid_url', return_value=True):
        # Mock _is_same_domain to pass the domain check
        with patch.object(snowflake_scraper, '_is_same_domain', return_value=True):
            filtered = snowflake_scraper._filter_urls(test_urls)
            
            # Should keep reference pages but filter out archive and release notes
            assert "https://docs.snowflake.com/en/reference/intro" in filtered
            assert "https://docs.snowflake.com/en/reference/sql/create-table" in filtered
            assert "https://docs.snowflake.com/en/archive/old-page" not in filtered
            assert "https://example.com/page" not in filtered
            assert "https://docs.snowflake.com/en/release-notes/2023" not in filtered
