import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from fpdf import FPDF
import re

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_page(self, url):
        """Scrape content from a given URL."""
        if not self._is_valid_url(url):
            raise ValueError("Invalid URL provided")

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")

    def save_as_text(self, content, output_file):
        """Save content to a text file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def save_as_pdf(self, content, output_file):
        """Save content to a PDF file."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Split content into lines and add to PDF
        for line in content.split('\n'):
            if line.strip():
                pdf.multi_cell(0, 10, txt=line)
        
        pdf.output(output_file)

    def _is_valid_url(self, url):
        """Check if the URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False 