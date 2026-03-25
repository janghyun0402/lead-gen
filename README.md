# Property Management Lead Generation Pipeline

An automated lead generation system that discovers property management companies via Google Maps, crawls their websites, extracts structured business intelligence using Gemini AI, and optionally enriches missing data through LLM-driven browser automation ([browser-use](https://github.com/browser-use/browser-use)).

## How It Works

```
Google Maps Search → Web Crawling → Gemini AI Analysis → Browser Enhancement (optional) → CSV Export
```

1. **Discover** — Search for PM companies by city using Google Maps Places API. Optionally filter cities by population via the US Census Bureau API.
2. **Crawl** — BFS-based crawler extracts text content from each company's website (configurable depth and page limits).
3. **Analyze** — Gemini 2.5 Pro parses crawled data into structured JSON: owner info, services, software, team, reviews, social links.
4. **Enhance** — If enabled, browser-use (LLM controlling a real browser) navigates JS-heavy pages to fill in missing fields.
5. **Export** — Results are flattened into a CSV file. In web mode, files are stored in MongoDB GridFS.

## Extracted Data

| Category | Fields |
|----------|--------|
| Company | Name, website, phone, city, state |
| Owner | Name, phone, email |
| Operations | PM software used, number of doors managed |
| Team | Leasing manager, maintenance manager |
| Services | Services offered, portfolio focus |
| Social | LinkedIn, Instagram, Facebook URLs |
| Reviews | Google rating, review count, summary |
| AI Output | Summary report, example outreach email |

## Getting Started

### Prerequisites

- Python 3.10+
- API keys for Google Maps, Google Gemini, and US Census Bureau
- MongoDB (only for web mode)

### Installation

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
CENSUS_API_KEY=your_census_api_key

# Required only for web mode
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=leadgen_db
```

## Usage

### CLI

```bash
# Single city (default: 10 companies, 15 pages/site, depth 3, browser on)
python run.py city "Kansas City"

# Custom parameters
python run.py city "San Antonio" 5 30 2

# Disable browser enhancement
python run.py city "Dallas" 10 50 3 --no-browser

# Process companies from a CSV file
python run.py csv companies.csv

# Multiple cities
python run.py city "New York, Los Angeles, Chicago"
```

**CLI Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_results` | 10 | Max companies per city (city mode only) |
| `max_pages` | 15 | Max pages to crawl per website |
| `max_depth` | 3 | Max crawl depth |
| `--no-browser` | off | Disable browser-use enhancement |

### CSV Input Format

| Column | Required | Description |
|--------|----------|-------------|
| `Organization Name` | Yes | Company name to search |
| `City` | No | Improves search accuracy |

```csv
Organization Name,City
"ABC Property Management","San Antonio"
"XYZ Residential Services","Dallas"
```

### Web Mode

```bash
# Start the Gradio UI (connects to FastAPI backend)
python app.py
```

The web interface provides city-based and CSV-based analysis with real-time progress tracking and file downloads.

## Output

Results are saved as CSV files in the `outputs/` directory:

```
outputs/city_analysis_Kansas_City_20250325_153045.csv
outputs/csv_analysis_companies_20250325_160012.csv
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| AI / LLM | Google Gemini 2.5 Pro |
| Browser Automation | browser-use, Playwright |
| Web Scraping | BeautifulSoup4, requests |
| Web Framework | FastAPI, Gradio |
| Database | MongoDB (Motor async driver), GridFS |
| Data APIs | Google Maps Places, US Census Bureau |
| Data Processing | Pandas |
