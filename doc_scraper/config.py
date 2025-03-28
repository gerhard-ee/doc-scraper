from dataclasses import dataclass, field
from typing import List


@dataclass
class ScraperConfig:
    """Configuration for the web scraper."""

    timeout: int = 60
    retry_count: int = 3
    retry_delay: int = 2
    max_workers: int = 5
    batch_size: int = 20  # Process URLs in batches to manage memory
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
            # Snowflake documentation selectors - enhanced for better coverage
            ".md-nav__item a",
            ".md-sidebar a",
            ".md-nav__link",
            ".snow-sidebar-nav a", 
            ".nav-tree a",
            ".documentationContent nav a",
            ".navigation-menu a",
            ".header-navigation-menu a",
            ".main-nav a",
            ".page-list a",
            ".article-nav a",
            # General selectors
            'a[href^="/"]',
            'a[href^="./"]',
            'a[href^="../"]',
        ]
    )
    # Added priority selectors - these are checked first and are more likely to be relevant navigation links
    priority_selectors: List[str] = field(
        default_factory=lambda: [
            'nav[role="navigation"] a',
            ".sidebar-menu a",
            ".docs-menu a",
            ".toc a",
            # Snowflake documentation priority selectors
            ".snow-sidebar-nav a",
            ".md-nav__item a",
            ".nav-tree a",
            ".documentationContent nav a",
            ".navigation-menu a",
        ]
    )
    excluded_paths: List[str] = field(
        default_factory=lambda: [
            "/search",
            "/login",
            "/signup",
            "/register",
            "/contact",
            "/download",
            "/print",
        ]
    )
    response_cache_size: int = 100  # Number of responses to cache
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
