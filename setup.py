from setuptools import setup, find_packages

setup(
    name="web_scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.12.3",
        "requests>=2.31.0",
        "fpdf2>=2.7.8",
    ],
    entry_points={
        'console_scripts': [
            'webscraper=web_scraper.cli:cli',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A web scraper for documentation sites",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/web_scraper",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 