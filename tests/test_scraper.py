import pytest
from unittest.mock import patch, MagicMock
from web_scraper.scraper import WebScraper

@pytest.fixture
def scraper():
    return WebScraper()

@pytest.fixture
def mock_response():
    mock = MagicMock()
    mock.text = """
    <html>
        <body>
            <div class="content">
                <h1>Test Title</h1>
                <p>Test paragraph 1</p>
                <p>Test paragraph 2</p>
            </div>
        </body>
    </html>
    """
    return mock

def test_scrape_page_success(scraper, mock_response):
    with patch('requests.get', return_value=mock_response):
        content = scraper.scrape_page("https://test.com")
        assert "Test Title" in content
        assert "Test paragraph 1" in content
        assert "Test paragraph 2" in content

def test_scrape_page_invalid_url(scraper):
    with pytest.raises(ValueError):
        scraper.scrape_page("invalid-url")

def test_save_as_text(scraper, tmp_path):
    content = "Test content"
    output_file = tmp_path / "test.txt"
    scraper.save_as_text(content, str(output_file))
    assert output_file.read_text() == content

def test_save_as_pdf(scraper, tmp_path):
    content = "Test content"
    output_file = tmp_path / "test.pdf"
    scraper.save_as_pdf(content, str(output_file))
    assert output_file.exists()
    assert output_file.stat().st_size > 0 