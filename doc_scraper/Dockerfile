# Use Python 3.8 slim image as base
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create output directory
RUN mkdir -p output

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m scraper && \
    chown -R scraper:scraper /app

# Switch to non-root user
USER scraper

# Set the entry point
ENTRYPOINT ["webscraper"] 