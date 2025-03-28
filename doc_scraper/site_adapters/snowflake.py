import logging
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urljoin, urlparse

from .base import BaseSiteAdapter

logger = logging.getLogger(__name__)

class SnowflakeAdapter(BaseSiteAdapter):
    """Adapter for Snowflake documentation."""
    
    def __init__(self):
        super().__init__()
        self.domains = {"docs.snowflake.com"}
        
    def extract_content(self, soup: BeautifulSoup) -> str:
        """Extract content from Snowflake documentation."""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'footer', 'iframe']):
            element.decompose()
            
        # Find main content container - try specific Snowflake selectors first
        main_content = None
        for selector in ['.documentationContent', '.main-content', 'main', 'article', '.content-container']:
            main_content = soup.select_one(selector)
            if main_content:
                break
                
        if not main_content:
            main_content = soup.body
            
        # Extract all content sections
        content_parts = []
        
        # Process headings and create structured content
        for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text().strip()
            if heading_text:
                # Add spacing around headings for better readability
                content_parts.append(f"\n\n{heading_text}\n{'=' * len(heading_text)}\n")
                
                # Collect all content until the next heading
                sibling = heading.next_sibling
                while sibling and sibling.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if sibling.name == 'p':
                        content_parts.append(sibling.get_text().strip())
                    elif sibling.name == 'pre' or sibling.find('code'):
                        # Handle code blocks
                        code_text = sibling.get_text().strip()
                        if code_text:
                            content_parts.append(f"\nCode Block:\n```\n{code_text}\n```\n")
                    elif sibling.name == 'table':
                        # Handle tables
                        table_text = "Table:\n"
                        rows = sibling.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            row_text = " | ".join(cell.get_text().strip() for cell in cells)
                            table_text += f"{row_text}\n"
                        content_parts.append(f"\n{table_text}\n")
                    elif sibling.name == 'ul' or sibling.name == 'ol':
                        # Handle lists
                        list_items = sibling.find_all('li')
                        list_text = "\n".join(f"- {item.get_text().strip()}" for item in list_items)
                        content_parts.append(f"\n{list_text}\n")
                    
                    sibling = sibling.next_sibling
        
        # If we didn't get any structured content, fall back to regular text extraction
        if not content_parts:
            # Fall back to default implementation
            return super().extract_content(soup)
            
        return "\n".join(content_parts)
    
    def find_menu_links(self, soup: BeautifulSoup, current_url: str, menu_selectors: List[str]) -> List[str]:
        """Find menu links in Snowflake documentation."""
        # Get links using the default implementation
        standard_links = super().find_menu_links(soup, current_url, menu_selectors)
        
        # Add Snowflake-specific link extraction
        menu_links = set(standard_links)
        
        # Extract table of contents links
        toc_containers = soup.select('.md-nav__list, .toc-container, .table-of-contents')
        for container in toc_containers:
            for link in container.find_all('a'):
                href = link.get('href')
                if href and isinstance(href, str):
                    absolute_url = urljoin(current_url, href)
                    # Filter out fragment-only links that point to the same page
                    parsed_href = urlparse(href)
                    if not (parsed_href.scheme == '' and parsed_href.netloc == '' and parsed_href.path == '' and parsed_href.fragment != ''):
                        menu_links.add(absolute_url)
        
        # Look for "See Also" and related links sections
        related_sections = soup.select('.related-links, .see-also, .related-content')
        for section in related_sections:
            for link in section.find_all('a'):
                href = link.get('href')
                if href and isinstance(href, str):
                    absolute_url = urljoin(current_url, href)
                    menu_links.add(absolute_url)
        
        return list(menu_links)
    
    def filter_urls(self, urls: List[str], base_url: str) -> List[str]:
        """Filter URLs for Snowflake documentation."""
        filtered = []
        
        for url in urls:
            parsed = urlparse(url)
            
            # Only include Snowflake documentation URLs
            if parsed.netloc != "docs.snowflake.com":
                continue
                
            # Skip version history and archive pages
            if any(x in url.lower() for x in ['/archive/', '/release-notes/', '/previous-versions/']):
                continue
                
            filtered.append(url)
            
        return filtered
