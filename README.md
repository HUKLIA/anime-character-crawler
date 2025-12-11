# Anime Character Crawler

A user-friendly desktop application to search and collect anime character images with pagination support - displaying 20 images per page.

## Features

- **Desktop GUI Application**: Easy-to-use interface - no command line needed!
- **Search with Autocomplete**: Type character names and get tag suggestions
- **Multi-Site Support**: Works with Danbooru, Safebooru, and Gelbooru
- **Tag Filtering**: Filter by character, series, artist, and more
- **Image Preview**: See thumbnails before downloading
- **Image Deduplication**: Uses perceptual hashing (pHash) to detect duplicate images
- **One-Click Download**: Automatically downloads images to your chosen folder
- **Dark Theme**: Beautiful modern dark interface

## Quick Start (GUI Application)

### Option 1: Run the App (Recommended)

```bash
# Clone and setup
git clone https://github.com/HUKLIA/anime-character-crawler.git
cd anime-character-crawler

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Option 2: Build Standalone Executable

```bash
# Build the .exe (Windows) or executable (Mac/Linux)
python build_exe.py

# Find your executable in:
# Windows: dist/AnimeCharacterCrawler/AnimeCharacterCrawler.exe
# Mac/Linux: dist/AnimeCharacterCrawler/AnimeCharacterCrawler
```

## Visual Guide - How to Use the App

### App Interface Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  File   Help                                              Anime Character   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    🎨 Anime Image Crawler                                   │
│           Search and download anime images from popular booru sites         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────┐  ┌──────────┐ │
│  │ 🔍 Enter character name or tags...                      │  │  Search  │ │
│  └─────────────────────────────────────────────────────────┘  └──────────┘ │
│                                                                             │
│  Site: [Danbooru ▼]   Rating: [General ▼]   Pages: [5]   ☑ Download Images │
│                                                                             │
│  Quick Tags:  [1girl] [blue_hair] [school_uniform] [smile] [rating:general] │
│                                                                             │
├──────────────────────┬──────────────────────────────────────────────────────┤
│                      │                                                      │
│  🏷️ Tags & Filters   │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│
│                      │   │  IMG 1  │  │  IMG 2  │  │  IMG 3  │  │  IMG 4  ││
│  👤 Characters       │   │         │  │         │  │         │  │         ││
│  ┌────────────────┐  │   │ Name    │  │ Name    │  │ Name    │  │ Name    ││
│  │ hatsune_miku   │  │   │ ⭐ 150  │  │ ⭐ 89   │  │ ⭐ 234  │  │ ⭐ 67   ││
│  │ rem            │  │   └─────────┘  └─────────┘  └─────────┘  └─────────┘│
│  └────────────────┘  │                                                      │
│                      │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│
│  📺 Series / Anime   │   │  IMG 5  │  │  IMG 6  │  │  IMG 7  │  │  IMG 8  ││
│  ┌────────────────┐  │   │         │  │         │  │         │  │         ││
│  │ vocaloid       │  │   │ Name    │  │ Name    │  │ Name    │  │ Name    ││
│  │ re:zero        │  │   │ ⭐ 45   │  │ ⭐ 178  │  │ ⭐ 92   │  │ ⭐ 56   ││
│  └────────────────┘  │   └─────────┘  └─────────┘  └─────────┘  └─────────┘│
│                      │                                                      │
│  🎨 Artists          │                                                      │
│  ┌────────────────┐  │                                                      │
│  │ artist_name    │  │                                                      │
│  └────────────────┘  │                                                      │
│                      │                                                      │
├──────────────────────┴──────────────────────────────────────────────────────┤
│  Ready                                              ████████░░  12 images   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Guide

#### Step 1: Launch the App
```
┌────────────────────────────────────────┐
│                                        │
│   Double-click:                        │
│                                        │
│   🖥️  AnimeCharacterCrawler.exe       │
│                                        │
│   OR run in terminal:                  │
│                                        │
│   > python app.py                      │
│                                        │
└────────────────────────────────────────┘
```

#### Step 2: Enter Search Terms
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Type character name or tags in the search bar:                 │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🔍 hatsune_miku blue_hair                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  💡 Tips:                                                       │
│  • Use underscores for multi-word tags: hatsune_miku           │
│  • Combine multiple tags with spaces: 1girl blue_hair smile    │
│  • Autocomplete suggestions appear as you type!                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 3: Choose Settings
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Site:     [Danbooru ▼]     ← Choose image source               │
│            • Danbooru - Large collection, some restrictions     │
│            • Safebooru - All safe/general images                │
│            • Gelbooru - Large collection                        │
│                                                                 │
│  Rating:   [General ▼]      ← Filter content                    │
│            • General (Safe) - Family-friendly images only       │
│            • All Ratings - Include all content                  │
│                                                                 │
│  Pages:    [5    ]          ← How many pages (20 images each)   │
│            • 1 page = ~20 images                                │
│            • 5 pages = ~100 images                              │
│            • 10 pages = ~200 images                             │
│                                                                 │
│  ☑ Download Images          ← Save images to your computer      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 4: Click Search
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│          ┌──────────────────┐                                   │
│          │    🔍 Search     │  ← Click this button!             │
│          └──────────────────┘                                   │
│                                                                 │
│  While searching:                                               │
│  ┌──────────────────┐                                           │
│  │     Cancel       │  ← Button changes to Cancel               │
│  └──────────────────┘                                           │
│                                                                 │
│  Progress bar shows status:                                     │
│  ████████████░░░░░░░░  Page 3 of 5...                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 5: View Results
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Images appear in the grid:                                     │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │             │  │             │  │             │             │
│  │   [Image]   │  │   [Image]   │  │   [Image]   │             │
│  │             │  │             │  │             │             │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤             │
│  │ Miku        │  │ Blue Hair   │  │ Vocaloid    │             │
│  │ Danbooru ⭐150│  │ Danbooru ⭐89│  │ Danbooru ⭐234│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  • Left-click: Open image in browser                           │
│  • Right-click: More options (copy URL, open file)             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 6: Use Tag Filters (Optional)
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Click tags in the left panel to refine your search:           │
│                                                                 │
│  🏷️ Tags & Filters                                              │
│  ┌─────────────────────────────────────────┐                    │
│  │ 👤 Characters                           │                    │
│  │ [hatsune_miku (45)] [rem (23)]         │ ← Click to filter  │
│  ├─────────────────────────────────────────┤                    │
│  │ 📺 Series / Anime                       │                    │
│  │ [vocaloid (45)] [re:zero (23)]         │                    │
│  ├─────────────────────────────────────────┤                    │
│  │ 🎨 Artists                              │                    │
│  │ [artist_name (12)]                     │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                 │
│  Number in brackets = how many images have this tag            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════════╗
║                    QUICK REFERENCE CARD                           ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  🚀 START APP         python app.py                               ║
║                                                                   ║
║  🔍 SEARCH TIPS                                                   ║
║     • Use underscores: hatsune_miku (not "hatsune miku")         ║
║     • Combine tags: 1girl blue_hair long_hair                    ║
║     • Safe content: add rating:general                           ║
║                                                                   ║
║  🖱️ MOUSE ACTIONS                                                 ║
║     • Left-click image  → Open in browser                        ║
║     • Right-click image → Copy URL / Open downloaded file        ║
║     • Click tag button  → Add to search                          ║
║                                                                   ║
║  ⌨️ KEYBOARD                                                      ║
║     • Enter            → Start search                            ║
║     • Ctrl + ,         → Open settings                           ║
║     • Ctrl + Q         → Quit app                                ║
║                                                                   ║
║  📁 FILES SAVED TO                                                ║
║     Windows: C:\Users\YOU\Downloads\AnimeImages\                 ║
║     Mac/Linux: ~/Downloads/AnimeImages/                          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Common Tag Examples

| What you want | Tags to use |
|---------------|-------------|
| Specific character | `hatsune_miku`, `rem`, `zero_two` |
| Hair color | `blue_hair`, `pink_hair`, `blonde_hair` |
| Style | `school_uniform`, `dress`, `kimono` |
| Expression | `smile`, `blush`, `crying` |
| Quality | `highres`, `absurdres` |
| Safe content | `rating:general` |

---

## Installation (Detailed)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/HUKLIA/anime-character-crawler.git
cd anime-character-crawler

# Run setup script
chmod +x setup.sh
./setup.sh
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## Usage

### Basic Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run with default settings (safe images from Danbooru)
python run_crawler.py --tags "rating:general" --max-pages 5

# Scrape specific character
python run_crawler.py --tags "hatsune_miku" --site danbooru --max-pages 3

# Use Safebooru
python run_crawler.py --tags "1girl blue_hair" --site safebooru
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--tags` | `-t` | Search tags (space-separated) | `rating:general` |
| `--site` | `-s` | Target site (danbooru, safebooru, gelbooru) | `danbooru` |
| `--max-pages` | `-m` | Maximum pages to scrape | unlimited |
| `--start-page` | `-p` | Page to start from | `1` |
| `--delay` | `-d` | Delay between requests (seconds) | `3.0` |
| `--images-per-page` | `-i` | Images per page | `20` |
| `--output-dir` | `-o` | Download directory | `downloaded_images` |
| `--log-level` | `-l` | Logging level | `info` |

### Using Scrapy Directly

```bash
# Basic crawl
scrapy crawl booru_html -a tags="rating:general" -a site=danbooru

# With pagination limit
scrapy crawl booru_html -a tags="1girl" -a max_pages=10 -a site=safebooru
```

## Project Structure

```
anime-character-crawler/
├── gui/                      # Desktop GUI application
│   ├── __init__.py
│   ├── main_window.py        # Main application window
│   ├── search_widget.py      # Search bar with autocomplete
│   ├── image_grid.py         # Image display grid
│   ├── tag_panel.py          # Tag filtering panel
│   ├── settings_dialog.py    # Settings configuration
│   ├── crawler_thread.py     # Background crawler
│   └── styles.py             # UI styling
├── anime_scraper/            # Scrapy crawler (advanced)
│   ├── __init__.py
│   ├── items.py              # Data models
│   ├── middlewares.py        # Request/response processing
│   ├── pipelines.py          # Item processing (dedup, download)
│   ├── settings.py           # Scrapy configuration
│   └── spiders/
│       └── booru_html.py     # Main spider
├── app.py                    # GUI application entry point
├── build_exe.py              # Build executable script
├── run_crawler.py            # CLI entry point
├── requirements.txt
├── scrapy.cfg
├── setup.sh
└── README.md
```

## Configuration

Key settings in `anime_scraper/settings.py`:

```python
# Politeness settings
DOWNLOAD_DELAY = 3.0           # Seconds between requests
CONCURRENT_REQUESTS = 1        # One request at a time
ROBOTSTXT_OBEY = True          # Respect robots.txt

# Image settings
IMAGES_PER_PAGE = 20           # Images per display page
IMAGES_MIN_WIDTH = 200         # Filter out thumbnails
IMAGES_MIN_HEIGHT = 200

# Deduplication
DEDUP_HAMMING_THRESHOLD = 10   # Hash similarity threshold
```

## Important Notes

### Avoiding Common Traps

1. **Thumbnail Trap**: The spider extracts full-resolution URLs from `data-file-url` attributes, not thumbnail `<img>` sources.

2. **Rate Limiting**: Default 3-second delay between requests. Adjust with `--delay` if needed.

3. **Layout Changes**: CSS selectors may break if sites update their HTML. Check logs for "0 items scraped" warnings.

4. **Anti-Bot Protection**: Playwright handles most protections, but some sites may still block scrapers.

### Ethical Usage

- **Research Only**: This tool is for personal/research use
- **Respect Rate Limits**: Don't reduce delays below 3 seconds
- **Check Terms of Service**: Each site has different policies
- **Don't Redistribute**: Downloaded images may be copyrighted

## Output

### Downloaded Images

Images are saved to `downloaded_images/{site}/{post_id}.{ext}`

### JSON Metadata

Metadata is exported to `output/images_{tags}_{timestamp}.json`:

```json
{
  "metadata": {
    "spider": "booru_html",
    "search_tags": "rating:general",
    "total_items": 100,
    "exported_at": "2024-01-15T12:00:00"
  },
  "images": [
    {
      "post_id": "12345",
      "image_url": "https://...",
      "tags": "1girl blue_hair",
      "rating": "g",
      "is_duplicate": false
    }
  ]
}
```

## Troubleshooting

### No images scraped

- Check if the site's HTML structure has changed
- Verify your search tags are valid
- Check the logs for error messages

### Cloudflare blocking

- Playwright should handle this automatically
- Try increasing `--delay` to 5-10 seconds
- Some sites may require additional configuration

### Import errors

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version (3.8+ required)

## License

This project is for educational and research purposes only
