#!/usr/bin/env python3
import click
import logging
import sys
from pathlib import Path
from typing import Optional
from .scraper import WebScraper, ScraperConfig


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


@click.group()
def cli():
    """Web Scraper CLI - A tool for scraping websites and preserving menu structure."""
    pass


@cli.command()
@click.argument("url")
@click.option(
    "-d",
    "--depth",
    default=0,
    help="Maximum depth to traverse menu (0 for single page)",
)
@click.option(
    "-o", "--output-dir", default="output", help="Output directory for scraped content"
)
@click.option("-t", "--timeout", default=60, help="Timeout for requests in seconds")
@click.option(
    "-r", "--retry-count", default=3, help="Number of retries for failed requests"
)
@click.option(
    "-w", "--max-workers", default=5, help="Maximum number of concurrent workers"
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["text", "pdf", "json", "both"]),
    default="text",
    help="Output format",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.option(
    "--pool-connections", default=100, help="Number of connection pools to keep"
)
@click.option(
    "--pool-maxsize", default=100, help="Maximum number of connections per pool"
)
@click.option("--no-pool-block", is_flag=True, help="Do not block when pool is full")
@click.option(
    "--ascii-only",
    is_flag=True,
    default=True,
    help="Filter non-ASCII characters in PDF output (prevents encoding errors)",
)
@click.option(
    "--no-ascii-only",
    is_flag=True,
    help="Disable ASCII-only filtering in PDF output (may cause font errors)",
)
@click.option(
    "--verbose-progress",
    is_flag=True,
    help="Show detailed progress including individual URLs being scraped",
)
def scrape(
    url: str,
    depth: int,
    output_dir: str,
    timeout: int,
    retry_count: int,
    max_workers: int,
    format: str,
    verbose: bool,
    pool_connections: int,
    pool_maxsize: int,
    no_pool_block: bool,
    ascii_only: bool,
    no_ascii_only: bool,
    verbose_progress: bool,
):
    """Scrape content from a website starting from the given URL."""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    # Handle conflicting options
    if no_ascii_only:
        ascii_only = False

    try:
        # Show immediate feedback
        print(f"Doc Scraper starting... URL: {url}")
        print(f"Depth: {depth}, Output format: {format}, Workers: {max_workers}")

        # Create configuration
        config = ScraperConfig(
            timeout=timeout,
            retry_count=retry_count,
            max_workers=max_workers,
            output_dir=output_dir,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            pool_block=not no_pool_block,
            verbose_progress=verbose_progress,
        )

        # Create and run scraper
        scraper = WebScraper(config)
        content = scraper.scrape_site(url, depth)

        # Save results based on format
        if format in ["text", "both"]:
            print(f"Saving content as text...")
            scraper.save_as_text(content, "scraped_content.txt")

        if format in ["pdf", "both"]:
            print(f"Saving content as PDF...")
            scraper.save_as_pdf(content, "scraped_content.pdf")

        if format in ["json", "both"]:
            print(f"Saving menu tree as JSON...")
            scraper.save_menu_tree("menu_tree.json")

        print(f"Successfully scraped {len(content)} pages")
        return 0

    except Exception as e:
        logger.error(f"Failed to scrape site: {str(e)}")
        return 1


def main():
    return cli(standalone_mode=False) or 0


if __name__ == "__main__":
    sys.exit(main())
