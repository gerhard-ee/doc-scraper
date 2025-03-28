import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from .scraper import WebScraper

logger = logging.getLogger(__name__)

class SnowflakeDocScraper(WebScraper):
    """Specialized scraper for Snowflake documentation."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.snowflake_domains = {"docs.snowflake.com"}
        
    def is_snowflake_url(self, url: str) -> bool:
        """Check if a URL belongs to Snowflake documentation."""
        parsed = urlparse(url)
        return parsed.netloc in self.snowflake_domains
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """
        Extract and clean text content from a Snowflake documentation page.
        This override ensures we capture all content, not just headings.
        """
        # First remove unwanted elements that might clutter the content
        for element in soup(['script', 'style', 'footer', 'iframe']):
            element.decompose()
            
        # Extract the main content area - snowflake docs typically have main content in specific containers
        main_content = None
        for selector in ['.documentationContent', 'main', '.main-content', 'article', '.content-container']:
            main_content = soup.select_one(selector)
            if main_content:
                break
                
        if not main_content:
            # Fall back to the whole body if specific containers aren't found
            main_content = soup.body
            
        # Extract all content sections including text, tables, code blocks, etc.
        content_parts = []
        
        # Process headings and create a structured content
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
            return super()._extract_text(soup)
            
        return "\n".join(content_parts)
    
    def _find_menu_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """
        Find menu links in Snowflake documentation pages.
        This override provides better handling of Snowflake's navigation structure.
        """
        # First use the standard menu link finder
        standard_links = super()._find_menu_links(soup, current_url)
        
        # For Snowflake specifically, look for their unique menu structures
        menu_links = set(standard_links)
        
        # Extract table of contents links which are common in Snowflake docs
        toc_containers = soup.select('.md-nav__list, .toc-container, .table-of-contents')
        for container in toc_containers:
            for link in container.find_all('a'):
                href = link.get('href')
                if href and isinstance(href, str):
                    absolute_url = urljoin(current_url, href)
                    # Filter out fragment-only links that point to the same page
                    if not href.startswith('#') and self._is_valid_url(absolute_url):
                        menu_links.add(absolute_url)
        
        # Look for "See Also" and related links sections
        related_sections = soup.select('.related-links, .see-also, .related-content')
        for section in related_sections:
            for link in section.find_all('a'):
                href = link.get('href')
                if href and isinstance(href, str):
                    absolute_url = urljoin(current_url, href)
                    if self._is_valid_url(absolute_url) and self.is_snowflake_url(absolute_url):
                        menu_links.add(absolute_url)
        
        return list(menu_links)
    
    def _filter_urls(self, urls: List[str]) -> List[str]:
        """Enhanced URL filtering for Snowflake documentation."""
        # Use the standard filtering first
        filtered = super()._filter_urls(urls)
        
        # Additional Snowflake-specific filtering
        snowflake_filtered = []
        for url in filtered:
            # Ensure we only get documentation pages
            if not self.is_snowflake_url(url):
                continue
                
            # Skip version history and archive pages which duplicate content
            if any(x in url.lower() for x in ['/archive/', '/release-notes/', '/previous-versions/']):
                continue
                
            snowflake_filtered.append(url)
            
        return snowflake_filtered
