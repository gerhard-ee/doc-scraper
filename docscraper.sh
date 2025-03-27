#!/bin/bash

# Web Scraper with Menu Traversal
# This script scrapes web content while maintaining menu structure

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to display usage information
show_usage() {
    echo "Usage: ./docscraper.sh [URL] [OPTIONS]"
    echo
    echo "Options:"
    echo "  -d, --depth       Maximum depth to traverse menu (0 for single page, default: 0)"
    echo "  -o, --output-dir  Output directory for scraped content (default: output)"
    echo "  -t, --timeout     Request timeout in seconds (default: 60)"
    echo "  -f, --format      Output format: text, pdf, json, or both (default: text)"
    echo "  -v, --verbose     Enable verbose logging"
    echo "  -h, --help        Show this help message"
    echo
    echo "Examples:"
    echo "  ./docscraper.sh https://docs.databricks.com/aws/en/"
    echo "  ./docscraper.sh https://docs.databricks.com/aws/en/ -f pdf"
    echo "  ./docscraper.sh https://docs.databricks.com/aws/en/ -d 2"
    echo "  ./docscraper.sh https://docs.databricks.com/aws/en/ -o my_output -f both"
}

# Check if help is requested
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# Check if no arguments are provided
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the docscraper command
python -m doc_scraper.cli scrape "$@"

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
