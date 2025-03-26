import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from web_scraper.cli import main

def test_cli_basic_usage(tmp_path):
    """Test basic CLI usage with text output."""
    test_url = "https://docs.databricks.com/aws/en/"
    output_file = tmp_path / "output.txt"
    
    with patch('sys.argv', ['webscraper', test_url]), \
         patch('web_scraper.cli.WebScraper') as mock_scraper_class:
        
        # Setup mock
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape_page.return_value = "Test content"
        
        # Run CLI
        result = main()
        
        # Verify
        assert result == 0
        mock_scraper.scrape_page.assert_called_once_with(test_url)
        mock_scraper.save_as_text.assert_called_once_with("Test content", "output.txt")

def test_cli_pdf_output(tmp_path):
    """Test CLI with PDF output."""
    test_url = "https://docs.databricks.com/aws/en/"
    output_file = tmp_path / "output.pdf"
    
    with patch('sys.argv', ['webscraper', test_url, '-f', 'pdf']), \
         patch('web_scraper.cli.WebScraper') as mock_scraper_class:
        
        # Setup mock
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape_page.return_value = "Test content"
        
        # Run CLI
        result = main()
        
        # Verify
        assert result == 0
        mock_scraper.scrape_page.assert_called_once_with(test_url)
        mock_scraper.save_as_pdf.assert_called_once_with("Test content", "output.pdf")
        mock_scraper.save_as_text.assert_not_called()

def test_cli_both_formats(tmp_path):
    """Test CLI with both text and PDF output."""
    test_url = "https://docs.databricks.com/aws/en/"
    
    with patch('sys.argv', ['webscraper', test_url, '-f', 'both', '-o', 'test_output']), \
         patch('web_scraper.cli.WebScraper') as mock_scraper_class:
        
        # Setup mock
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape_page.return_value = "Test content"
        
        # Run CLI
        result = main()
        
        # Verify
        assert result == 0
        mock_scraper.scrape_page.assert_called_once_with(test_url)
        mock_scraper.save_as_text.assert_called_once_with("Test content", "test_output.txt")
        mock_scraper.save_as_pdf.assert_called_once_with("Test content", "test_output.pdf")

def test_cli_custom_timeout():
    """Test CLI with custom timeout."""
    test_url = "https://docs.databricks.com/aws/en/"
    
    with patch('sys.argv', ['webscraper', test_url, '-t', '60']), \
         patch('web_scraper.cli.WebScraper') as mock_scraper_class:
        
        # Setup mock
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape_page.return_value = "Test content"
        
        # Run CLI
        result = main()
        
        # Verify
        assert result == 0
        mock_scraper_class.assert_called_once_with(timeout=60)

def test_cli_invalid_url():
    """Test CLI with invalid URL."""
    with patch('sys.argv', ['webscraper', 'invalid-url']), \
         patch('web_scraper.cli.WebScraper') as mock_scraper_class:
        
        # Setup mock
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape_page.side_effect = ValueError("Invalid URL")
        
        # Run CLI
        result = main()
        
        # Verify
        assert result == 1 