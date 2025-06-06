from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="doc-scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.12.3",
        "requests>=2.31.0",
        "fpdf2>=2.7.8",
        "tqdm>=4.65.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "docscraper=doc_scraper.cli:cli",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A web scraper for documentation sites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/doc-scraper",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
)
