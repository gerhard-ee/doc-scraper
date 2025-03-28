import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from fpdf import FPDF
import re
from typing import Set, List, Dict, Optional, Tuple
import time
from collections import OrderedDict
import logging
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import signal
import sys
from tqdm import tqdm
from functools import lru_cache

from .config import ScraperConfig
from .models import MenuNode
from .site_adapters import AdapterRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WebScraper:
    def __init__(self, config: Optional[ScraperConfig] = None):
        """
        Initialize the web scraper.

        Args:
            config (Optional[ScraperConfig]): Configuration for the scraper
        """
        self.config = config or ScraperConfig()
        self.headers = {"User-Agent": self.config.user_agent}
        self.visited_urls: Set[str] = set()
        self.base_url: Optional[str] = None
        self.base_domain: Optional[str] = None
        self.menu_tree: Optional[MenuNode] = None
        self.session = self._create_session()
        self._setup_signal_handlers()
        # Add caching for responses to avoid repeated requests for the same URL
        self.response_cache = OrderedDict()
        # Add domain pattern for better URL filtering
        self.domain_pattern = None

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy and connection pooling."""
        session = requests.Session()

        # Configure retry strategy with backoff for better handling of rate limits
        retry_strategy = Retry(
            total=self.config.retry_count,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )

        # Configure connection pooling with optimized settings
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.config.pool_connections,
            pool_maxsize=self.config.pool_maxsize,
            pool_block=self.config.pool_block,
        )

        # Mount the adapter for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Enable TCP keepalive for better connection reuse
        session.headers.update({"Connection": "keep-alive"})

        return session

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info("Received shutdown signal. Cleaning up...")
            self._cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _cleanup(self):
        """Cleanup resources before shutdown."""
        if hasattr(self, "session"):
            self.session.close()
        logger.info("Cleanup completed")

    @lru_cache(maxsize=1000)
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is from the same domain as the base URL (cached for performance)."""
        if not self.base_domain:
            return True
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain

    def _get_cached_or_request(self, url: str) -> requests.Response:
        """Get response from cache or make a new request."""
        if url in self.response_cache:
            return self.response_cache[url]

        response = self.session.get(
            url,
            headers=self.headers,
            timeout=self.config.timeout,
            allow_redirects=True,
        )
        response.raise_for_status()

        # Cache the response and maintain cache size
        self.response_cache[url] = response
        if len(self.response_cache) > self.config.response_cache_size:
            self.response_cache.popitem(last=False)

        return response

    def scrape_page(
        self,
        url: str,
        max_depth: int = 0,
        parent_node: Optional[MenuNode] = None,
        progress_bar: Optional[tqdm] = None,
    ) -> Tuple[Dict[str, str], Optional[MenuNode]]:
        """
        Scrape content from a given URL and optionally traverse its menu.

        Args:
            url (str): The URL to scrape
            max_depth (int): Maximum depth to traverse menu (0 for single page)
            parent_node (Optional[MenuNode]): Parent node in the menu tree
            progress_bar (Optional[tqdm]): Progress bar for updates

        Returns:
            Tuple[Dict[str, str], Optional[MenuNode]]: Dictionary mapping URLs to their content and the menu node
        """
        if not self._is_valid_url(url):
            logger.error(f"Invalid URL provided: {url}")
            raise ValueError("Invalid URL provided")

        # If we've already visited this URL, return immediately
        if url in self.visited_urls:
            logger.debug(f"URL already visited: {url}")
            return {}, None

        # Mark URL as visited immediately to prevent duplicate processing in concurrent requests
        self.visited_urls.add(url)
        result = {}

        try:
            # Initialize base domain for first request to improve filtering
            if self.base_url is None:
                self.base_url = url
                parsed_base = urlparse(url)
                self.base_domain = parsed_base.netloc
                logger.info(f"Base URL set to: {self.base_url}")
                logger.info(f"Base domain set to: {self.base_domain}")

            # Show progress updates if configured
            if self.config.verbose_progress:
                logger.info(f"Scraping: {url}")
            elif progress_bar:
                progress_bar.set_description(f"Scraping page {len(self.visited_urls)}")
                progress_bar.update(0)

            # Get response (either from cache or new request)
            response = self._get_cached_or_request(url)

            # Parse content with BeautifulSoup
            if progress_bar:
                progress_bar.set_description("Parsing content...")
                progress_bar.update(0)

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract content
            text = self._extract_text(soup)
            title = self._extract_title(soup)
            result[url] = text

            # Create or update menu node structure
            current_level = 0 if parent_node is None else parent_node.level + 1
            current_node = MenuNode(
                url=url,
                title=title,
                children=[],
                level=current_level,
                parent_url=parent_node.url if parent_node else None,
            )

            if self.menu_tree is None:
                self.menu_tree = current_node

            if parent_node is not None:
                parent_node.children.append(current_node)

            # Update progress
            if progress_bar:
                progress_bar.update(1)

            # Process nested pages if max_depth > 0
            if max_depth > 0:
                # Find all menu links, prioritizing more important navigation elements
                menu_links = self._find_menu_links(soup, url)

                # Apply early filtering to remove likely irrelevant URLs
                menu_links = self._filter_urls(menu_links)

                # Update progress info if links were found
                if menu_links and self.config.verbose_progress:
                    logger.info(
                        f"Found {len(menu_links)} menu items at depth {max_depth}"
                    )
                elif menu_links and progress_bar:
                    progress_bar.set_description(
                        f"Found {len(menu_links)} sub-pages to process"
                    )
                    progress_bar.update(0)

                # Update progress bar estimation
                if progress_bar and menu_links:
                    new_estimate = progress_bar.total + min(len(menu_links), 100)
                    progress_bar.total = new_estimate

                # Process URLs in batches for better memory management
                for i in range(0, len(menu_links), self.config.batch_size):
                    batch = menu_links[i : i + self.config.batch_size]
                    # Skip URLs that have already been visited (may have been added by other concurrent processes)
                    batch = [link for link in batch if link not in self.visited_urls]

                    # Process this batch concurrently
                    with ThreadPoolExecutor(
                        max_workers=self.config.max_workers
                    ) as executor:
                        future_to_url = {
                            executor.submit(
                                self.scrape_page,
                                link,
                                max_depth - 1,
                                current_node,
                                progress_bar,
                            ): link
                            for link in batch
                        }

                        if self.config.verbose_progress:
                            with tqdm(
                                total=len(future_to_url),
                                desc=f"Batch {i//self.config.batch_size+1}/{(len(menu_links)+self.config.batch_size-1)//self.config.batch_size}",
                                unit="page",
                                leave=False,
                            ) as pbar:
                                for future in as_completed(future_to_url):
                                    link = future_to_url[future]
                                    try:
                                        sub_result, _ = future.result()
                                        result.update(sub_result)
                                        pbar.update(1)
                                        pbar.set_postfix({"current": link})
                                    except Exception as e:
                                        logger.error(f"Error scraping {link}: {str(e)}")
                                        pbar.update(1)
                        else:
                            # Process without detailed progress
                            completed = 0
                            for future in as_completed(future_to_url):
                                link = future_to_url[future]
                                try:
                                    sub_result, _ = future.result()
                                    result.update(sub_result)
                                    completed += 1
                                    if progress_bar and completed % 5 == 0:
                                        progress_bar.update(5)
                                except Exception as e:
                                    if self.config.verbose_progress:
                                        logger.error(f"Error scraping {link}: {str(e)}")
                                    completed += 1

            return result, current_node

        except requests.Timeout:
            logger.error(f"Timeout while scraping {url}")
            raise Exception(f"Request timed out after {self.config.timeout} seconds")
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            if (
                hasattr(e, "response")
                and e.response is not None
                and hasattr(e.response, "status_code")
            ):
                raise Exception(f"Failed to fetch URL (HTTP {e.response.status_code})")
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while scraping {url}: {str(e)}")
            raise

    def scrape_site(self, url: str, max_depth: int = 0) -> Dict[str, str]:
        """
        Scrape content from a website starting from a given URL.

        Args:
            url (str): The starting URL to scrape
            max_depth (int): Maximum depth to traverse menu (0 for single page)

        Returns:
            Dict[str, str]: Dictionary mapping URLs to their content
        """
        logger.info(f"Starting to scrape site: {url}")
        logger.info(f"Maximum depth: {max_depth}")

        # Show immediate feedback with an initial progress bar
        with tqdm(
            total=1, desc="Initializing scraper", unit="step", position=0, leave=True
        ) as init_pbar:
            # Update immediately to show activity
            init_pbar.update(1)

        # Create progress bar for overall scraping process
        with tqdm(
            total=100,  # Start with estimated total, will update later
            desc="Overall Progress",
            unit="page",
            position=0,
            leave=True,
        ) as pbar:
            # Show immediate activity
            pbar.set_description("Preparing to fetch initial page...")
            pbar.update(1)

            try:
                # Show activity while making the initial request
                pbar.set_description("Fetching initial page...")
                pbar.update(1)

                result, _ = self.scrape_page(url, max_depth, progress_bar=pbar)

                # Update with actual count
                pbar.total = len(self.visited_urls)
                pbar.n = len(self.visited_urls)
                pbar.refresh()

                logger.info(f"Successfully scraped {len(self.visited_urls)} pages")
                return result
            except Exception as e:
                logger.error(f"Failed to scrape site: {str(e)}")
                raise

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title from the page."""
        # Try to find the title in various ways
        title = None

        # Try h1 tag first
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text().strip()

        # Try title tag if no h1
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text().strip()

        # If still no title, use the URL
        if not title:
            title = (
                urlparse(self.base_url or "")
                .path.split("/")[-1]
                .replace("-", " ")
                .title()
            )

        return title

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract and clean text content from a BeautifulSoup object."""
        # Use the appropriate site adapter for content extraction
        adapter = AdapterRegistry.get_adapter_for_url(self.base_url or "")
        return adapter.extract_content(soup)

    def _find_menu_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Find menu links in the page with priority ordering."""
        # Use the appropriate site adapter for menu link extraction
        adapter = AdapterRegistry.get_adapter_for_url(current_url)
        
        menu_links = set()

        # First check priority selectors which are more likely to be relevant navigation
        priority_links = adapter.find_menu_links(soup, current_url, self.config.priority_selectors)
        menu_links.update(priority_links)

        # Then check other selectors if we still need more links
        if len(menu_links) < 5:  # Only look for more if we don't have enough high-priority links
            # Use only selectors that aren't in priority_selectors
            additional_selectors = [s for s in self.config.menu_selectors if s not in self.config.priority_selectors]
            additional_links = adapter.find_menu_links(soup, current_url, additional_selectors)
            menu_links.update(additional_links)

        return list(menu_links)

    def _filter_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to remove likely irrelevant ones and improve performance."""
        # Start with basic filtering
        filtered = []

        for url in urls:
            # Skip URLs we've already visited
            if url in self.visited_urls:
                continue

            # Skip URLs that aren't from the same domain
            if not self._is_same_domain(url):
                continue

            # Skip URLs that contain excluded paths
            if any(excluded in url for excluded in self.config.excluded_paths):
                continue

            # Skip URLs with fragments or query strings (often duplicate content)
            parsed = urlparse(url)
            if parsed.fragment or parsed.query:
                continue

            # Skip URLs that don't start with the base URL (likely external links)
            if self.base_url and not url.startswith(self.base_url):
                continue

            # Skip URLs with common non-content indicators
            if any(x in url for x in ["javascript:", "mailto:", "tel:", "#", "?"]):
                continue

            filtered.append(url)

        # Apply site-specific filtering using the appropriate adapter
        adapter = AdapterRegistry.get_adapter_for_url(self.base_url or "")
        filtered = adapter.filter_urls(filtered, self.base_url or "")

        # Prioritize URLs that look like they contain content (those with more path segments)
        filtered.sort(key=lambda u: len(urlparse(u).path.split("/")), reverse=True)

        return filtered

    def save_as_text(self, content: Dict[str, str], output_file: str):
        """Save content to a text file."""
        output_path = Path(self.config.output_dir) / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                if self.menu_tree:
                    self._write_menu_tree_text(f, self.menu_tree, content)
                else:
                    for url, text in content.items():
                        f.write(f"\n{'='*80}\n")
                        f.write(f"URL: {url}\n")
                        f.write(f"{'='*80}\n\n")
                        f.write(text)
                        f.write("\n\n")
            logger.info(f"Content saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving text file: {str(e)}")
            raise

    def _write_menu_tree_text(self, f, node: MenuNode, content: Dict[str, str]):
        """Write the menu tree structure to the text file."""
        # Write current node
        indent = "  " * node.level
        f.write(f"\n{indent}{'='*80}\n")
        f.write(f"{indent}Level {node.level}: {node.title}\n")
        f.write(f"{indent}URL: {node.url}\n")
        f.write(f"{indent}{'='*80}\n\n")

        # Write content
        if node.url in content:
            text = content[node.url]
            for line in text.split("\n"):
                f.write(f"{indent}{line}\n")
            f.write("\n")

        # Write children
        for child in node.children:
            self._write_menu_tree_text(f, child, content)

    def _sanitize_text_for_pdf(self, text: str) -> str:
        """
        Sanitize text for PDF output to avoid font encoding issues.
        Replaces or removes characters that might not be supported by the PDF font.
        """
        # Option 1: Replace non-ASCII characters with their closest ASCII equivalent
        text = text.encode("ascii", "replace").decode("ascii")

        return text

    def save_as_pdf(self, content: Dict[str, str], output_file: str):
        """Save content to a PDF file."""
        output_path = Path(self.config.output_dir) / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            pdf = FPDF()

            if self.menu_tree:
                # Add title page
                self._add_title_page(pdf)

                # Add table of contents
                self._add_table_of_contents(pdf)

                # Add content pages
                self._write_menu_tree_pdf(pdf, self.menu_tree, content)
            else:
                # Add title page
                self._add_title_page(pdf)

                # Add content pages
                for url, text in content.items():
                    pdf.add_page()
                    # Sanitize text before writing to PDF
                    sanitized_text = self._sanitize_text_for_pdf(text)
                    self._format_page(pdf, url, sanitized_text)

            pdf.output(str(output_path))
            logger.info(f"Content saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving PDF file: {str(e)}")
            raise

    def _add_title_page(self, pdf: FPDF):
        """Add a title page to the PDF."""
        pdf.add_page()

        # Center the title
        pdf.set_xy(0, 40)
        pdf.set_font("Helvetica", "B", size=24)
        pdf.cell(210, 20, "Web Scraper Output", ln=True, align="C")

        # Add metadata
        pdf.set_xy(0, 80)
        pdf.set_font("Helvetica", size=12)
        pdf.cell(210, 10, f"Base URL: {self.base_url}", ln=True)
        pdf.cell(210, 10, f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(210, 10, f"Pages: {len(self.visited_urls)}", ln=True)

    def _add_table_of_contents(self, pdf: FPDF):
        """Add a table of contents to the PDF."""
        pdf.add_page()

        # TOC title
        pdf.set_font("Helvetica", "B", size=16)
        pdf.cell(210, 10, "Table of Contents", ln=True)
        pdf.ln(10)

        # Add TOC entries
        if self.menu_tree:
            self._write_toc_entries(pdf, self.menu_tree, 0)

    def _write_toc_entries(self, pdf: FPDF, node: MenuNode, level: int):
        """Write table of contents entries recursively."""
        pdf.set_font("Helvetica", size=12)

        # Add dots for TOC
        dots = "." * (50 - len(node.title) - level * 2)
        page_num = pdf.page_no() + 1  # +1 because TOC is on current page

        # Write entry with proper indentation
        pdf.cell(level * 10, 8, "", 0, 0)
        pdf.cell(0, 8, f"{node.title} {dots} {page_num}", ln=True)

        # Write children
        for child in node.children:
            self._write_toc_entries(pdf, child, level + 1)

    def _format_page(self, pdf: FPDF, url: str, text: str):
        """Format a single page with proper margins and styling."""
        # Set margins
        pdf.set_left_margin(20)
        pdf.set_right_margin(20)

        # Write URL as header
        pdf.set_font("Helvetica", "B", size=14)
        pdf.write(8, f"URL: {url}\n\n")

        # Write content
        pdf.set_font("Helvetica", size=12)
        lines = text.split("\n")
        for line in lines:
            if line.strip():
                pdf.write(8, line + "\n")

    def _write_menu_tree_pdf(self, pdf: FPDF, node: MenuNode, content: Dict[str, str]):
        """Write the menu tree structure to the PDF file."""
        pdf.add_page()

        # Set margins
        pdf.set_left_margin(20)
        pdf.set_right_margin(20)

        # Write level and title
        pdf.set_font("Helvetica", "B", size=16)
        sanitized_title = self._sanitize_text_for_pdf(node.title)
        pdf.write(8, f"Level {node.level}: {sanitized_title}\n\n")

        # Write URL
        pdf.set_font("Helvetica", "I", size=12)
        pdf.write(8, f"URL: {node.url}\n\n")

        # Write content
        if node.url in content:
            pdf.set_font("Helvetica", size=12)
            text = content[node.url]
            # Sanitize text before writing to PDF
            sanitized_text = self._sanitize_text_for_pdf(text)
            lines = sanitized_text.split("\n")
            for line in lines:
                if line.strip():
                    pdf.write(8, line + "\n")

        # Write children
        for child in node.children:
            self._write_menu_tree_pdf(pdf, child, content)

    def save_menu_tree(self, output_file: str):
        """Save the menu tree structure to a JSON file."""
        output_path = Path(self.config.output_dir) / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:

            def node_to_dict(node: MenuNode) -> dict:
                return {
                    "url": node.url,
                    "title": node.title,
                    "level": node.level,
                    "parent_url": node.parent_url,
                    "children": [node_to_dict(child) for child in node.children],
                }

            if self.menu_tree:
                tree_dict = node_to_dict(self.menu_tree)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(tree_dict, f, indent=2)
                logger.info(f"Menu tree saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving menu tree: {str(e)}")
            raise

    def _is_valid_url(self, url: str) -> bool:
        """
        Check if the URL is valid.

        Args:
            url (str): The URL to validate

        Returns:
            bool: True if the URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
