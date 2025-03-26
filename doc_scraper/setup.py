from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="web-scraper",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A web scraper with menu traversal capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/web-scraper",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "beautifulsoup4>=4.12.3",
        "requests>=2.31.0",
        "fpdf2>=2.7.8",
        "tqdm>=4.65.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "webscraper=web_scraper.cli:cli",
        ],
    },
) 