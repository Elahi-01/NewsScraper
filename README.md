# 📰 NewsScraper Dashboard

A unified Streamlit web application that combines 6 international newspaper scrapers into one clean, modular, production-ready dashboard.

## Supported Newspapers

| Newspaper | Country | Method | Coverage |
|---|---|---|---|
| 🗽 New York Times | 🇺🇸 USA | REST API | 1851–present |
| 📰 Daily Mail | 🇬🇧 UK | HTML Archive | 1994–present |
| 🌴 Los Angeles Times | 🇺🇸 USA | HTML Sitemap | Varies by year |
| 📊 Wall Street Journal | 🇺🇸 USA | Selenium | 1997–present |
| 🇩🇪 DIE ZEIT | 🇩🇪 Germany | HTML Archive | Varies by year |
| 🛡️ The Guardian | 🇬🇧 UK | REST API | 1999–present |

## Features

- **One-click newspaper selection** — Tab-based navigation for all 6 scrapers
- **Dynamic search forms** — Each newspaper shows only its relevant input fields
- **Normalized output** — All results follow a common schema (Date, Title, URL, Newspaper)
- **CSV download** — Export results with one click
- **Progress tracking** — Real-time progress updates while scraping
- **Error handling** — Graceful error messages, no app crashes
- **Modular architecture** — Clean separation of UI, scraper logic, and utilities

## Project Structure

```
newspaper_webapp/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env                    # API keys (not committed)
├── .env.example            # Template for API keys
├── .gitignore
├── README.md
├── scrapers/
│   ├── __init__.py         # Package exports
│   ├── nyt.py              # New York Times (API)
│   ├── daily_mail.py       # Daily Mail (HTML archive)
│   ├── latimes.py          # LA Times (HTML sitemap)
│   ├── wsj.py              # Wall Street Journal (Selenium)
│   ├── zeit.py             # DIE ZEIT (HTML archive)
│   └── guardian.py         # The Guardian (API)
├── utils/
│   ├── __init__.py
│   ├── helpers.py          # Config registry & normalization
│   └── export.py           # CSV export utility
└── assets/                 # Optional styling files
```

## Setup

### 1. Clone or download the project

```bash
cd newspaper_webapp
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up API keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

- **NYT_API_KEY** — Get one free at [developer.nytimes.com](https://developer.nytimes.com/)
- **GUARDIAN_API_KEY** — Get one free at [open-platform.theguardian.com](https://open-platform.theguardian.com/access/)

> The other 4 scrapers (Daily Mail, LA Times, WSJ, DIE ZEIT) work without API keys.

### 5. Selenium setup (for WSJ only)

The Wall Street Journal scraper requires a Chrome browser and ChromeDriver:

```bash
# Install Chrome (if not already installed)
# Then install chromedriver matching your Chrome version
pip install webdriver-manager

# Or on Ubuntu:
sudo apt install chromium-chromedriver
```

### 6. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Usage

1. Open the app in your browser
2. The **Home** tab shows an overview of all 6 newspapers with their capabilities
3. Click any newspaper tab to open its search form
4. Fill in the required fields (keyword, dates, etc.)
5. Click the **Search** button
6. View results in the interactive table
7. Download results as CSV with the download button

## Deployment

### Streamlit Cloud

1. Push the project to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set the main file path to `app.py`
5. Add your API keys in **Settings → Secrets**:
   ```toml
   NYT_API_KEY = "your_key_here"
   GUARDIAN_API_KEY = "your_key_here"
   ```
6. Deploy

> **Note:** The WSJ scraper requires Selenium/Chrome, which is not available on Streamlit Cloud by default. Consider deploying on Render or Railway for full functionality.

### Render

1. Create a `Dockerfile` or use a Python environment
2. Set the start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
3. Add environment variables for API keys
4. For WSJ/Selenium support, use a Docker image with Chrome installed:
   ```dockerfile
   FROM python:3.11-slim
   RUN apt-get update && apt-get install -y chromium chromium-driver
   COPY . /app
   WORKDIR /app
   RUN pip install -r requirements.txt
   CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```

### Docker (local)

```bash
docker build -t newsscraper .
docker run -p 8501:8501 --env-file .env newsscraper
```

## Adding a New Scraper

1. Create a new module in `scrapers/` (e.g., `scrapers/bbc.py`)
2. Implement a `search_bbc(...)` function that returns `List[dict]` with keys: `date`, `title`, `url`
3. Add an entry to `NEWSPAPER_CONFIG` in `utils/helpers.py`
4. Import the function in `scrapers/__init__.py`
5. Add a handler in the `_run_scraper()` function in `app.py`

## Notes

- **Rate Limits:** The NYT API is rate-limited (~5 req/min). Large date ranges use automatic splitting.
- **Long-running scrapers:** Daily Mail and WSJ can take a long time for large date ranges. Start with small ranges first.
- **Selenium:** Only the WSJ scraper requires Selenium. All others use standard HTTP requests.
- **Keywords:** LA Times and DIE ZEIT accept comma-separated keywords; others accept a single keyword string.
