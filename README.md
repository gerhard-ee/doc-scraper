# Web Scraper

A Python-based web scraper that can extract text content from documentation websites and save it as text or PDF files. The scraper can traverse menu structures to extract content from multiple pages.

## Features

- Scrapes text content from documentation websites
- Supports saving output as text or PDF files
- Built with Test-Driven Development (TDD) principles
- Handles nested documentation pages
- Configurable output formats
- Command-line interface (CLI)
- Menu traversal with configurable depth
- Automatic handling of relative and absolute URLs
- Smart menu detection using common selectors

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
webscraper https://docs.databricks.com/aws/en/

# Save as PDF
webscraper https://docs.databricks.com/aws/en/ -f pdf

# Save as both text and PDF with custom output name
webscraper https://docs.databricks.com/aws/en/ -f both -o databricks_docs

# Set custom timeout (in seconds)
webscraper https://docs.databricks.com/aws/en/ -t 60

# Traverse menu up to 2 levels deep
webscraper https://docs.databricks.com/aws/en/ -d 2

# Traverse menu 3 levels deep and save as PDF
webscraper https://docs.databricks.com/aws/en/ -d 3 -f pdf
```

Options:
- `-o, --output`: Output file path (default: output.[txt|pdf])
- `-f, --format`: Output format: text, pdf, or both (default: text)
- `-t, --timeout`: Request timeout in seconds (default: 30)
- `-d, --depth`: Maximum depth to traverse menu (0 for single page, default: 0)

### Python API

You can also use the scraper in your Python code:

```python
from web_scraper import WebScraper

# Initialize the scraper
scraper = WebScraper()

# Scrape a single page
content = scraper.scrape_page("https://docs.databricks.com/aws/en/")

# Scrape multiple pages by traversing menu (up to 2 levels deep)
content = scraper.scrape_page("https://docs.databricks.com/aws/en/", max_depth=2)

# Save as text
scraper.save_as_text(content, "output.txt")

# Save as PDF
scraper.save_as_pdf(content, "output.pdf")
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
pytest --cov=src tests/
```

## License

MIT License 