# Use Python 3.10 slim as the base image
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Second stage to keep the image small
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Working directory
WORKDIR /app

# Copy only the installed packages from the builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY . /app/

# Install the package in development mode
RUN pip install -e . && \
    mkdir -p /app/output && \
    chmod +x /app/docscraper.sh

# Create a non-root user to run the application
RUN useradd -m scraper && \
    chown -R scraper:scraper /app/output

# Set the user
USER scraper

# Set volume for output
VOLUME ["/app/output"]

# Set the entrypoint to the docscraper script
ENTRYPOINT ["/app/docscraper.sh"]

# Default command (can be overridden)
CMD ["--help"]
