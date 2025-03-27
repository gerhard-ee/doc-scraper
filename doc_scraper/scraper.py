import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from fpdf import FPDF
import re
from typing import Set, List, Dict, Optional, Tuple
import time
from dataclasses import dataclass, field
from collections import defaultdict
import logging
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import signal
import sys
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Configuration for the web scraper."""

    timeout: int = 60
    retry_count: int = 3
    retry_delay: int = 2
    max_workers: int = 5
    output_dir: str = "output"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    menu_selectors: List[str] = field(
        default_factory=lambda: [
            'nav[role="navigation"] a',
            ".sidebar-menu a",
            ".docs-menu a",
            ".toc a",
            ".nav-links a",
            ".menu-item a",
            'a[href^="/"]',
            'a[href^="./"]',
            'a[href^="../"]',
        ]
    )
    pool_connections: int = 100  # Number of connection pools to keep
    pool_maxsize: int = 100  # Maximum number of connections per pool
    pool_block: bool = True  # Whether to block when pool is full
    verbose_progress: bool = (
        False  # Whether to show detailed progress including site names
    )

    def __post_init__(self):
        if self.menu_selectors is None:
            self.menu_selectors = [
                'nav[role="navigation"] a',
                ".sidebar-menu a",
                ".docs-menu a",
                ".toc a",
                ".nav-links a",
                ".menu-item a",
                'a[href^="/"]',
                'a[href^="./"]',
                'a[href^="../"]',
            ]


@dataclass
class MenuNode:
    url: str
    title: str
    children: List["MenuNode"]
    level: int
    parent_url: Optional[str] = None


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
        self.menu_tree: Optional[MenuNode] = None
        self.session = self._create_session()
        self._setup_signal_handlers()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy and connection pooling."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.retry_count,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # Configure connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.config.pool_connections,
            pool_maxsize=self.config.pool_maxsize,
            pool_block=self.config.pool_block,
        )

        # Mount the adapter for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)

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

    def scrape_page(
        self, 
        url: str, 
        max_depth: int = 0, 
        parent_node: Optional[MenuNode] = None,
        progress_bar: Optional[tqdm] = None
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

        if url in self.visited_urls:
            logger.debug(f"URL already visited: {url}")
            return {}, None

        self.visited_urls.add(url)
        result = {}

        try:
            # Only log the site being scraped if verbose progress is enabled
            if self.config.verbose_progress:
                logger.info(f"Scraping: {url}")
            elif progress_bar:
                # Show minimal info in progress bar to indicate activity
                progress_bar.set_description(f"Scraping page {len(self.visited_urls)}")
                progress_bar.update(0)  # Refresh without incrementing

            # Update progress bar to show activity during request
            if progress_bar:
                progress_bar.set_description(f"Fetching: {url.split('/')[-1]}")
                progress_bar.update(0)  # Refresh without incrementing

            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.config.timeout,
                allow_redirects=True,
            )
            response.raise_for_status()

            if self.base_url is None:
                self.base_url = url
                logger.info(f"Base URL set to: {self.base_url}")

            # Update progress to show parsing activity
            if progress_bar:
                progress_bar.set_description("Parsing content...")
                progress_bar.update(0)  # Refresh without incrementing

            soup = BeautifulSoup(response.text, "html.parser")

            text = self._extract_text(soup)
            title = self._extract_title(soup)
            result[url] = text

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

            # Update progress bar after getting content
            if progress_bar:
                progress_bar.update(1)

            if max_depth > 0:
                menu_links = self._find_menu_links(soup, url)
                if menu_links and self.config.verbose_progress:
                    logger.info(
                        f"Found {len(menu_links)} menu items at depth {max_depth}"
                    )
                elif menu_links and progress_bar:
                    progress_bar.set_description(f"Found {len(menu_links)} sub-pages to process")
                    progress_bar.update(0)  # Refresh without incrementing

                # If we have a lot of links, update the progress bar total
                if progress_bar and menu_links and len(menu_links) > 0:
                    # Estimate the new total (current + new links)
                    new_estimate = progress_bar.total + min(len(menu_links), 100)
                    progress_bar.total = new_estimate

                with ThreadPoolExecutor(
                    max_workers=self.config.max_workers
                ) as executor:
                    future_to_url = {
                        executor.submit(
                            self.scrape_page, link, max_depth - 1, current_node
                        ): link
                        for link in menu_links
                        if link not in self.visited_urls
                    }

                    # Only show detailed progress if verbose progress is enabled
                    if self.config.verbose_progress:
                        with tqdm(
                            total=len(future_to_url),
                            desc=f"Scraping pages at depth {max_depth}",
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
                                    pbar.update(1)  # Update progress even on error
                    else:
                        # Process without detailed progress but update main progress bar
                        completed = 0
                        for future in as_completed(future_to_url):
                            link = future_to_url[future]
                            try:
                                sub_result, _ = future.result()
                                result.update(sub_result)
                                completed += 1
                                # Update main progress bar periodically
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
            total=1, 
            desc="Initializing scraper", 
            unit="step", 
            position=0, 
            leave=True
        ) as init_pbar:
            # Update immediately to show activity
            init_pbar.update(1)
        
        # Create progress bar for overall scraping process
        with tqdm(
            total=100,  # Start with estimated total, will update later
            desc="Overall Progress", 
            unit="page", 
            position=0,
            leave=True
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
        return list(menu_links)

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

        # Option 2: Remove characters that are not printable ASCII
        # text = ''.join(c for c in text if c.isascii() and c.isprintable())

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
