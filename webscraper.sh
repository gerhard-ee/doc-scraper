#!/bin/bash

# Function to display usage information
show_usage() {
    echo "Usage: ./webscraper.sh [URL] [OPTIONS]"
    echo
    echo "Options:"
    echo "  -o, --output     Output file path (default: output.[txt|pdf])"
    echo "  -f, --format     Output format: text, pdf, or both (default: text)"
    echo "  -t, --timeout    Request timeout in seconds (default: 30)"
    echo "  -d, --depth      Maximum depth to traverse menu (0 for single page, default: 0)"
    echo "  -h, --help       Show this help message"
    echo
    echo "Examples:"
    echo "  ./webscraper.sh https://docs.databricks.com/aws/en/"
    echo "  ./webscraper.sh https://docs.databricks.com/aws/en/ -f pdf"
    echo "  ./webscraper.sh https://docs.databricks.com/aws/en/ -f both -o databricks_docs"
    echo "  ./webscraper.sh https://docs.databricks.com/aws/en/ -t 60"
    echo "  ./webscraper.sh https://docs.databricks.com/aws/en/ -d 2"
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

# Run the webscraper module directly
python3 -m web_scraper "$@"

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi 