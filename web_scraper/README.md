# Web Scraper with Menu Traversal

A robust web scraper that can extract content from websites while maintaining the menu structure. It supports traversing through menu items up to a specified depth and can output the content in multiple formats.

## Features

- Menu structure preservation
- Configurable traversal depth
- Multiple output formats (Text, PDF, JSON)
- Concurrent scraping with configurable workers
- Robust error handling and retries
- Detailed logging
- Graceful shutdown handling
- Scrapes documentation sites with menu-based navigation
- Supports multiple output formats (text, PDF)
- Configurable depth and concurrency
- Progress tracking with tqdm
- Connection pooling for better performance
- Docker support for containerized execution

## Installation

### From PyPI (when published)
```bash
pip install web-scraper
```

### From source
```bash
git clone https://github.com/yourusername/web-scraper.git
cd web-scraper
pip install -e .
```

## Usage

### Command Line Interface

Basic usage:
```bash
web-scraper https://example.com
```

With menu traversal:
```bash
web-scraper https://example.com -d 2
```

Full options:
```bash
web-scraper --help
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--depth` | `-d` | Maximum depth to traverse menu (0 for single page) | 0 |
| `--output-dir` | `-o` | Output directory for scraped content | "output" |
| `--timeout` | `-t` | Request timeout in seconds | 60 |
| `--retry-count` | `-r` | Number of retry attempts for failed requests | 3 |
| `--max-workers` | `-w` | Maximum number of concurrent workers | 5 |
| `--verbose` | `-v` | Enable verbose logging | False |
| `--output-format` | | Output format (text/pdf/both/json) | "both" |
| `--pool-connections` | | Number of connection pools to keep | 100 |
| `--pool-maxsize` | | Maximum number of connections per pool | 100 |
| `--no-pool-block` | | Do not block when connection pool is full | False |

### Examples

1. Basic scraping with menu traversal:
```bash
web-scraper https://docs.example.com -d 2
```

2. Scraping with custom timeout and retries:
```bash
web-scraper https://docs.example.com -t 120 -r 5
```

3. Scraping with concurrent workers and verbose logging:
```bash
web-scraper https://docs.example.com -w 10 -v
```

4. Scraping with specific output format:
```bash
web-scraper https://docs.example.com --output-format pdf
```

5. Scraping with custom output directory:
```bash
web-scraper https://docs.example.com -o my_output
```

6. Scraping with custom connection pool settings:
```bash
web-scraper https://docs.example.com --pool-connections 200 --pool-maxsize 200
```

7. Scraping with non-blocking connection pool:
```bash
web-scraper https://docs.example.com --no-pool-block
```

### Docker Usage

```bash
docker build -t web-scraper .
docker run -v $(pwd)/output:/app/output web-scraper scrape https://docs.example.com
```

## Configuration Options

- `timeout`: Request timeout in seconds (default: 60)
- `retry_count`: Number of retry attempts for failed requests (default: 3)
- `max_workers`: Maximum number of concurrent workers (default: 5)
- `output_dir`: Directory for output files (default: "output")
- `menu_selectors`: CSS selectors for menu items (configurable)

## Output Formats

### Text Output
- Hierarchical structure with indentation
- Level indicators
- URLs and titles preserved
- Clean text content

### PDF Output
- One page per menu item
- Hierarchical structure through page order
- Formatted headers and content
- Clean typography

### JSON Output
- Complete menu tree structure
- URLs, titles, and levels
- Parent-child relationships
- Easy to parse and process

## Error Handling

The scraper includes robust error handling for:
- Network timeouts
- HTTP errors
- Invalid URLs
- File system errors
- Graceful shutdown on interruption

## Logging

Logs are written to both:
- Console (with optional verbosity)
- File (`web_scraper.log`)

Log levels:
- INFO: Basic progress information
- DEBUG: Detailed information (enabled with -v)
- ERROR: Error messages and exceptions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- BeautifulSoup4 for HTML parsing
- FPDF for PDF generation
- Requests for HTTP handling

## Development

### Project Structure

```
web_scraper/
├── web_scraper/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   └── scraper.py
├── setup.py
├── requirements.txt
├── Dockerfile
└── README.md
```

### Generation Prompts

The web scraper package was generated using the following prompts:

1. Initial Package Structure:
```
Create a Python package for a web scraper that can extract content from documentation sites. The scraper should:
- Support menu-based navigation
- Handle multiple output formats (text, PDF)
- Include progress tracking
- Support concurrent scraping
- Have proper error handling
- Include Docker support
```

2. Core Scraper Implementation:
```
Implement the core web scraper functionality with:
- BeautifulSoup4 for HTML parsing
- Requests for HTTP requests
- FPDF2 for PDF generation
- Connection pooling for better performance
- Menu structure extraction
- Content extraction and formatting
```

3. CLI Implementation:
```
Create a Click-based CLI with:
- Command-line options for configuration
- Progress bars using tqdm
- Verbose logging support
- Output format selection
- Concurrent worker configuration
```

4. Docker Support:
```
Add Docker support with:
- Multi-stage build for smaller image size
- Volume mounting for output
- Environment variable configuration
- Health check
```

5. Documentation:
```
Create comprehensive documentation including:
- Installation instructions
- Usage examples
- Command-line options
- Docker usage
- Project structure
- Development setup
``` 