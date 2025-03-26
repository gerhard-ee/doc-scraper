import pytest
import os
from web_scraper.scraper import WebScraper

@pytest.fixture
def scraper():
    return WebScraper()

@pytest.fixture
def output_dir(tmp_path):
    return tmp_path

def test_scrape_databricks_docs(scraper, output_dir):
    """Test scraping Databricks AWS documentation."""
    url = "https://docs.databricks.com/aws/en/"
    content = scraper.scrape_page(url)
    
    # Test content extraction
    assert len(content) > 0
    assert "Databricks" in content
    # The page might be dynamic, so we check for common terms
    assert any(term in content for term in ["documentation", "Data", "Platform"])
    
    # Test saving as text
    text_file = output_dir / "databricks.txt"
    scraper.save_as_text(content, str(text_file))
    assert text_file.exists()
    assert text_file.stat().st_size > 0
    
    # Test saving as PDF
    pdf_file = output_dir / "databricks.pdf"
    scraper.save_as_pdf(content, str(pdf_file))
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 0

def test_scrape_with_redirect(scraper):
    """Test scraping a URL that might redirect."""
    url = "http://docs.databricks.com"  # Should redirect to https
    content = scraper.scrape_page(url)
    assert len(content) > 0
    assert "Databricks" in content

def test_scrape_large_documentation(scraper, output_dir):
    """Test scraping a larger documentation page."""
    url = "https://docs.databricks.com/en/workspace/index.html"
    content = scraper.scrape_page(url)
    
    # Test content extraction
    assert len(content) > 0
    assert any(term in content.lower() for term in ["workspace", "databricks"])
    
    # Clean content for PDF
    clean_content = ''.join(char for char in content if ord(char) < 128)
    
    # Test saving large content
    pdf_file = output_dir / "large_doc.pdf"
    scraper.save_as_pdf(clean_content, str(pdf_file))
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 1024  # Should be at least 1KB

@pytest.mark.parametrize("url", [
    "https://docs.databricks.com/aws/en/",
    "https://docs.databricks.com/en/workspace/index.html",
    "https://docs.databricks.com/en/getting-started/index.html"
])
def test_multiple_documentation_pages(scraper, url):
    """Test scraping multiple documentation pages."""
    content = scraper.scrape_page(url)
    assert len(content) > 0
    assert "Databricks" in content

def test_error_handling(scraper):
    """Test error handling for various scenarios."""
    # Test invalid URL
    with pytest.raises(ValueError):
        scraper.scrape_page("not-a-url")
    
    # Test non-existent page
    with pytest.raises(Exception) as exc_info:
        scraper.scrape_page("https://docs.databricks.com/nonexistent")
    assert "404" in str(exc_info.value) or "Failed to fetch URL" in str(exc_info.value) 