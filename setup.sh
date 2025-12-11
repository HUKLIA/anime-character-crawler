#!/bin/bash
# Anime Image Crawler - Setup Script
#
# This script sets up the development environment for the anime image crawler.
# It creates a virtual environment, installs dependencies, and sets up Playwright.

set -e

echo "=========================================="
echo "Anime Image Crawler - Setup"
echo "=========================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers (this may take a while)..."
playwright install chromium

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p downloaded_images output data logs

# Make run script executable
chmod +x run_crawler.py

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start using the crawler:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the crawler:"
echo "     python run_crawler.py --tags 'rating:general' --max-pages 5"
echo ""
echo "  3. Or use Scrapy directly:"
echo "     scrapy crawl booru_html -a tags='rating:general' -a max_pages=5"
echo ""
echo "For more options, run:"
echo "     python run_crawler.py --help"
echo ""
