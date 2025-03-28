#!/bin/bash

echo "Building Docker image..."
docker build -t docscraper .

echo "Testing Docker image..."
docker run --rm -v "$(pwd)/output:/app/output" docscraper https://docs.databricks.com/aws/en/ -d 0 -f text -o output

if [ $? -eq 0 ]; then
    echo "Docker test successful!"
    echo "Output files:"
    ls -la output
else
    echo "Docker test failed!"
fi
