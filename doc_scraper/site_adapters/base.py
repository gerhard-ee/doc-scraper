import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class BaseSiteAdapter(ABC):
    """
    Base interface for site-specific adapters.
    
    Adapters provide customized behavior for different documentation sites
    while maintaining a common interface.
    """
    
    def __init__(self):
        """Initialize the adapter."""
        self.domains = set()  # Domains this adapter supports
    
    def can_handle(self, url: str) -> bool:
        """
        Check if this adapter can handle the given URL.
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if this adapter can handle the URL, False otherwise
        """
        if not url:
            return False
            
        try:
            parsed = urlparse(url)
            return parsed.netloc in self.domains
        except:
            return False
    
    def extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract and clean text content from a page.
        
        Args:
            soup (BeautifulSoup): The parsed page content
            
        Returns:
            str: The extracted text content
        """
        # Default implementation - can be overridden by specific adapters
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Extract main content
        main_content = None
        for selector in ['.main-content', 'main', 'article', '.content', '#content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
                
        if not main_content:
            main_content = soup.body
            
        # Get text content
        content_parts = []
        
        # Process headings for structure
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text().strip()
            if heading_text:
                content_parts.append(f"\n\n{heading_text}\n{'=' * len(heading_text)}\n")
                
                # Find content under this heading until the next heading
                sibling = heading.next_sibling
                while sibling and sibling.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if sibling.name == 'p':
                        content_parts.append(sibling.get_text().strip())
                    elif sibling.name == 'pre' or sibling.find('code'):
                        code_text = sibling.get_text().strip()
                        if code_text:
                            content_parts.append(f"\nCode Block:\n```\n{code_text}\n```\n")
                    elif sibling.name == 'table':
                        table_text = "Table:\n"
                        rows = sibling.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            row_text = " | ".join(cell.get_text().strip() for cell in cells)
                            table_text += f"{row_text}\n"
                        content_parts.append(f"\n{table_text}\n")
                    elif sibling.name in ['ul', 'ol']:
                        list_items = sibling.find_all('li')
                        list_text = "\n".join(f"- {item.get_text().strip()}" for item in list_items)
                        content_parts.append(f"\n{list_text}\n")
                    
                    sibling = sibling.next_sibling
        
        # If we didn't extract structured content, fall back to regular text extraction
        if not content_parts:
            text = main_content.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return "\n".join(chunk for chunk in chunks if chunk)
        
        return "\n".join(content_parts)
    
    def find_menu_links(self, soup: BeautifulSoup, current_url: str, menu_selectors: List[str]) -> List[str]:
        """
        Find menu links in the page.
        
        Args:
            soup (BeautifulSoup): The parsed page content
            current_url (str): The current URL
            menu_selectors (List[str]): Selectors to find menu links
            
        Returns:
            List[str]: A list of menu links
        """
        # Default implementation - can be overridden by specific adapters
        menu_links = set()
        
        for selector in menu_selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href and isinstance(href, str):
                    absolute_url = urljoin(current_url, href)
                    menu_links.add(absolute_url)
        
        return list(menu_links)
    
    def filter_urls(self, urls: List[str], base_url: str) -> List[str]:
        """
        Filter URLs to keep only relevant ones.
        
        Args:
            urls (List[str]): URLs to filter
            base_url (str): The base URL for comparison
            
        Returns:
            List[str]: Filtered URLs
        """
        # Default implementation - can be overridden by specific adapters
        return urls
