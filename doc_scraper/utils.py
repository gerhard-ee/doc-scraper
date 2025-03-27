import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def clean_text(text: str) -> str:
    """Clean up extracted text by removing excess whitespace and formatting."""
    # Clean up text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def is_valid_url(url: str) -> bool:
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


def extract_text_from_html(soup: BeautifulSoup) -> str:
    """Extract and clean text content from a BeautifulSoup object."""
    # Remove unwanted elements
    for element in soup(["script", "style", "nav", "footer", "iframe"]):
        element.decompose()

    # Get text content
    text = soup.get_text()

    return clean_text(text)
