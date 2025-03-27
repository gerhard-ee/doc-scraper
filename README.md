# Doc Scraper

A Python-based web scraper that can extract text content from documentation websites and save it as text or PDF files. The scraper can traverse menu structures to extract content from multiple pages.

## Features

- Scrapes text content from documentation websites
- Supports saving output as text, PDF, or JSON files
- Built with Test-Driven Development (TDD) principles
- Handles nested documentation pages
- Configurable output formats
- Command-line interface (CLI)
- Menu traversal with configurable depth
- Automatic handling of relative and absolute URLs
- Smart menu detection using common selectors
- Concurrent scraping with configurable workers
- Progress tracking with tqdm

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install the package:
   ```bash
   pip install -e .
   ```

## Usage

### Command Line Interface

The scraper can be used from the command line:

```bash
# Basic usage (saves as text)
docscraper scrape https://docs.databricks.com/aws/en/

# Save as PDF
docscraper scrape https://docs.databricks.com/aws/en/ -f pdf

# Save as both text and PDF with custom output directory
docscraper scrape https://docs.databricks.com/aws/en/ -f both -o my_output

# Set custom timeout (in seconds)
docscraper scrape https://docs.databricks.com/aws/en/ -t 60

# Traverse menu up to 2 levels deep
docscraper scrape https://docs.databricks.com/aws/en/ -d 2

# Traverse menu 3 levels deep and save as PDF
docscraper scrape https://docs.databricks.com/aws/en/ -d 3 -f pdf

# Fix Unicode character issues in PDF output
docscraper scrape https://docs.databricks.com/aws/en/ -f pdf --ascii-only
```

You can also use the included shell script:

```bash
# Make the script executable
chmod +x docscraper.sh

# Run with basic options
./docscraper.sh https://docs.databricks.com/aws/en/

# Run with advanced options
./docscraper.sh https://docs.databricks.com/aws/en/ -d 2 -f pdf -o custom_output
```

Options:

- `-d, --depth`: Maximum depth to traverse menu (0 for single page, default: 0)
- `-o, --output-dir`: Output directory for scraped content (default: output)
- `-f, --format`: Output format: text, pdf, json, or both (default: text)
- `-t, --timeout`: Request timeout in seconds (default: 60)
- `-r, --retry-count`: Number of retries for failed requests (default: 3)
- `-w, --max-workers`: Maximum number of concurrent workers (default: 5)
- `-v, --verbose`: Enable verbose logging
- `--pool-connections`: Number of connection pools to keep (default: 100)
- `--pool-maxsize`: Maximum number of connections per pool (default: 100)
- `--no-pool-block`: Do not block when pool is full
- `--ascii-only`: Filter non-ASCII characters in PDF output (default: enabled)
- `--verbose-progress`: Show detailed progress including site names being scraped

### Python API

You can also use the scraper in your Python code:

```python
from docscraper import DocScraper, ScraperConfig

# Initialize the scraper with default configuration
scraper = DocScraper()

# Or with custom configuration
config = ScraperConfig(
    timeout=120,
    max_workers=10,
    output_dir="custom_output"
)
scraper = DocScraper(config)

# Scrape a single page
content = scraper.scrape_site("https://docs.databricks.com/aws/en/")

# Scrape multiple pages by traversing menu (up to 2 levels deep)
content = scraper.scrape_site("https://docs.databricks.com/aws/en/", max_depth=2)

# Save as text
scraper.save_as_text(content, "output.txt")

# Save as PDF
scraper.save_as_pdf(content, "output.pdf")

# Save menu structure as JSON
scraper.save_menu_tree("menu.json")
```

## Menu Traversal

The scraper can automatically traverse menu structures to extract content from multiple pages. It detects menu links using common selectors including:

- Navigation links (`nav a`)
- Menu classes (`.menu a`, `.navigation a`)
- Sidebar links (`.sidebar a`)
- Table of contents (`.toc a`)
- Documentation menus (`.docs-menu a`, `.doc-menu a`)
- Navigation menus (`.nav-menu a`, `.main-menu a`, `.site-menu a`)

The scraper will:

1. Start from the given URL
2. Find menu links using the above selectors
3. Follow those links up to the specified depth
4. Save all content with clear separation between pages
5. Include URLs as headers in both text and PDF output

## Testing

Run the tests with:

```bash
pytest tests/
```

For coverage report:

```bash
pytest --cov=docscraper tests/
```

## Concurrency & Performance

The scraper uses concurrent processing to speed up scraping of multiple pages:

- ThreadPoolExecutor for parallel requests
- Configurable number of workers
- Connection pooling for better performance
- Progress tracking with tqdm

## Error Handling

The scraper includes robust error handling for:

- Network timeouts
- HTTP errors
- Invalid URLs
- File system errors
- Graceful shutdown on interruption

## License

MIT License
