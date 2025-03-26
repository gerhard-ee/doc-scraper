#!/bin/bash

# Web Scraper with Menu Traversal
# This script scrapes web content while maintaining menu structure
# Usage: ./webscraper.sh [options] URL

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add the parent directory to PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR/..:$PYTHONPATH"

# Show help if no arguments provided
if [ $# -eq 0 ]; then
    python3 -m web_scraper --help
    exit 1
fi

# Run the Python script with all arguments passed through
python3 -m web_scraper "$@" 