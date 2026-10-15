"""
Unified Newspaper Scraping Dashboard
=====================================
A Streamlit webapp that combines 6 newspaper scrapers into one
clean, modular, production-ready interface.

Run with:  streamlit run app.py
"""

import os
import streamlit as st
import pandas as pd
from datetime import date, datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import scrapers
from scrapers.nyt import search_nyt
from scrapers.daily_mail import search_daily_mail
from scrapers.latimes import search_latimes
from scrapers.wsj import search_wsj
from scrapers.zeit import search_zeit
from scrapers.guardian import search_guardian

# Import utilities
from utils.helpers import normalize_results, NEWSPAPER_CONFIG
from utils.export import results_to_csv_bytes


# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="NewsScraper Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ──────────────────────────────────────────────
# Custom CSS for Professional Styling
# ──────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ── Header ── */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
    }
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }
    .main-header p {
        font-size: 1rem;
        color: #6b7280;
        margin-top: 0;
    }

    /* ── Newspaper Cards ── */
    .newspaper-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.2s ease;
        height: 100%;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .newspaper-card:hover {
        border-color: #6366f1;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.12);
        transform: translateY(-2px);
    }
    .newspaper-card .card-emoji {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .newspaper-card .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.35rem;
    }
    .newspaper-card .card-country {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }
    .newspaper-card .card-desc {
        font-size: 0.78rem;
        color: #6b7280;
        line-height: 1.4;
    }

    /* ── Input Info Badges ── */
    .input-badge {
        display: inline-block;
        background: #f3f4f6;
        color: #4b5563;
        font-size: 0.7rem;
        font-weight: 500;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        margin: 0.15rem 0.1rem;
    }

    /* ── Status indicators ── */
    .api-badge {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 500;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        margin-top: 0.4rem;
    }
    .api-badge.api {
        background: #dbeafe;
        color: #1d4ed8;
    }
    .api-badge.html {
        background: #dcfce7;
        color: #166534;
    }
    .api-badge.selenium {
        background: #fef3c7;
        color: #92400e;
    }

    /* ── Results metric cards ── */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        flex: 1;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        text-align: center;
    }
    .metric-card .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f2937;
    }
    .metric-card .metric-label {
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: 0.2rem;
    }

    /* ── Section dividers ── */
    .section-divider {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 1.5rem 0;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>📰 NewsScraper Dashboard</h1>
    <p>Unified newspaper search across 6 international sources</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Navigation — Tabs for each newspaper + Home
# ──────────────────────────────────────────────

tab_names = ["🏠 Home"] + [
    f"{cfg['emoji']} {name}" for name, cfg in NEWSPAPER_CONFIG.items()
]

tabs = st.tabs(tab_names)


# ──────────────────────────────────────────────
# HOME TAB
# ──────────────────────────────────────────────

with tabs[0]:
    st.markdown("### Available Newspapers")
    st.markdown(
        "Select any newspaper tab above to run its scraper. "
        "Each scraper has its own search form tailored to the source."
    )

    # Newspaper overview cards — 3 per row
    names = list(NEWSPAPER_CONFIG.keys())
    for row_start in range(0, len(names), 3):
        cols = st.columns(3)
        for col_idx, col in enumerate(cols):
            name_idx = row_start + col_idx
            if name_idx >= len(names):
                break
            name = names[name_idx]
            cfg = NEWSPAPER_CONFIG[name]

            # Determine method badge
            if cfg.get("requires_api_key"):
                method_badge = '<span class="api-badge api">API</span>'
            elif cfg["key"] == "wsj":
                method_badge = '<span class="api-badge selenium">Selenium</span>'
            else:
                method_badge = '<span class="api-badge html">HTML</span>'

            # Input type badges
            input_badges = ""
            for field in cfg["fields"]:
                label = cfg["field_labels"].get(field, field)
                input_badges += f'<span class="input-badge">{label}</span> '

            with col:
                st.markdown(f"""
                <div class="newspaper-card">
                    <div>
                        <div class="card-emoji">{cfg['emoji']}</div>
                        <div class="card-title">{name}</div>
                        <div class="card-country">{cfg['country']}</div>
                        {method_badge}
                    </div>
                    <div class="card-desc" style="margin-top: 0.6rem;">
                        {cfg['description'][:120]}...
                    </div>
                    <div style="margin-top: 0.5rem;">
                        {input_badges}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # Quick reference table
    st.markdown("### Quick Reference")
    ref_data = []
    for name, cfg in NEWSPAPER_CONFIG.items():
        method = "API" if cfg.get("requires_api_key") else (
            "Selenium" if cfg["key"] == "wsj" else "HTML"
        )
        inputs = ", ".join(cfg["field_labels"].values())
        api_key = cfg.get("requires_api_key", "—") or "—"
        ref_data.append({
            "Newspaper": f"{cfg['emoji']} {name}",
            "Country": cfg["country"],
            "Method": method,
            "Inputs": inputs,
            "API Key": api_key,
        })
    st.dataframe(
        pd.DataFrame(ref_data),
        use_container_width=True,
        hide_index=True,
    )


# ──────────────────────────────────────────────
# SCRAPER TABS — Dynamic form for each newspaper
# ──────────────────────────────────────────────

def render_scraper_tab(tab, newspaper_name: str, config: dict):
    """Render the search form and results area for a single newspaper."""

    with tab:
        # Header with description
        st.markdown(f"### {config['emoji']} {newspaper_name}")
        st.markdown(f"_{config['description']}_")

        # API key warning
        api_key_env = config.get("requires_api_key")
        if api_key_env:
            key_value = os.getenv(api_key_env, "")
            if not key_value:
                signup_url = config.get("api_signup_url", "")
                st.warning(
                    f"**{api_key_env}** is not set. "
                    f"Add it to your `.env` file or set it as an environment variable. "
                    f"[Get an API key]({signup_url})" if signup_url else ""
                )

        # Notes
        if config.get("notes"):
            st.info(f"ℹ️ {config['notes']}")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ── Dynamic Search Form ──
        st.markdown("#### Search Parameters")

        form_key = f"form_{config['key']}"
        with st.form(form_key):
            form_values = {}

            # Render fields dynamically based on config
            num_fields = len(config["fields"])
            # Layout: up to 3 columns for fields
            if num_fields <= 3:
                cols = st.columns(num_fields)
            else:
                cols = st.columns(3)

            for i, field in enumerate(config["fields"]):
                col = cols[i % len(cols)]
                label = config["field_labels"].get(field, field)
                field_type = config["field_types"].get(field, "text")
                default = config["field_defaults"].get(field, "")

                with col:
                    if field_type == "text":
                        form_values[field] = st.text_input(
                            label, value=str(default),
                            key=f"{config['key']}_{field}"
                        )

                    elif field_type == "text_date_yyyymmdd":
                        form_values[field] = st.text_input(
                            label, value=str(default),
                            key=f"{config['key']}_{field}",
                            help="Format: YYYYMMDD (e.g., 20200101)"
                        )

                    elif field_type == "date":
                        try:
                            default_date = datetime.strptime(
                                str(default), "%Y-%m-%d"
                            ).date()
                        except (ValueError, TypeError):
                            default_date = date.today()
                        form_values[field] = st.date_input(
                            label, value=default_date,
                            key=f"{config['key']}_{field}"
                        )

                    elif field_type == "year":
                        form_values[field] = st.number_input(
                            label, min_value=1850, max_value=2030,
                            value=int(default),
                            step=1,
                            key=f"{config['key']}_{field}"
                        )

                    elif field_type == "number":
                        form_values[field] = st.number_input(
                            label, min_value=1, max_value=500,
                            value=int(default),
                            key=f"{config['key']}_{field}"
                        )

                    elif field_type == "select":
                        options = config["field_options"].get(field, [])
                        form_values[field] = st.selectbox(
                            label, options=options,
                            key=f"{config['key']}_{field}"
                        )

            submitted = st.form_submit_button(
                f"🔍 Search {newspaper_name}",
                use_container_width=True,
                type="primary",
            )

        # ── Execute Scraper on Submit ──
        if submitted:
            _run_scraper(newspaper_name, config, form_values)


def _run_scraper(newspaper_name: str, config: dict, form_values: dict):
    """Execute the appropriate scraper and display results."""

    # Validate required text fields are not empty
    for field in config["fields"]:
        if config["field_types"].get(field, "text") in ("text", "text_date_yyyymmdd"):
            if not str(form_values.get(field, "")).strip():
                st.error(f"Please fill in: {config['field_labels'][field]}")
                return

    # Progress container
    progress_placeholder = st.empty()
    log_expander = st.expander("📋 Progress Log", expanded=True)
    log_lines = []

    def progress_callback(msg):
        log_lines.append(msg)
        with log_expander:
            st.text("\n".join(log_lines[-15:]))  # Show last 15 lines

    results = []

    try:
        with st.spinner(f"Searching {newspaper_name}... This may take a while."):

            key = config["key"]

            if key == "nyt":
                results = search_nyt(
                    keyword=form_values["keyword"].strip(),
                    begin_date=form_values["begin_date"].strip(),
                    end_date=form_values["end_date"].strip(),
                    sort=form_values.get("sort", "best"),
                    progress_callback=progress_callback,
                )

            elif key == "daily_mail":
                results = search_daily_mail(
                    keyword=form_values["keyword"].strip(),
                    start_date=form_values["start_date"],
                    end_date=form_values["end_date"],
                    progress_callback=progress_callback,
                )

            elif key == "latimes":
                results = search_latimes(
                    keywords=form_values["keywords"].strip(),
                    start_year=int(form_values["start_year"]),
                    end_year=int(form_values["end_year"]),
                    progress_callback=progress_callback,
                )

            elif key == "wsj":
                results = search_wsj(
                    keyword=form_values["keyword"].strip(),
                    start_year=int(form_values["start_year"]),
                    end_year=int(form_values["end_year"]),
                    progress_callback=progress_callback,
                )

            elif key == "zeit":
                results = search_zeit(
                    keywords=form_values["keywords"].strip(),
                    start_year=int(form_values["start_year"]),
                    end_year=int(form_values["end_year"]),
                    progress_callback=progress_callback,
                )

            elif key == "guardian":
                from_date = form_values["from_date"]
                to_date = form_values["to_date"]
                # Convert date objects to strings if needed
                if isinstance(from_date, date):
                    from_date = from_date.isoformat()
                if isinstance(to_date, date):
                    to_date = to_date.isoformat()

                results = search_guardian(
                    keyword=form_values["keyword"].strip(),
                    from_date=from_date,
                    to_date=to_date,
                    page_size=int(form_values.get("page_size", 50)),
                    max_pages=int(form_values.get("max_pages", 10)),
                    progress_callback=progress_callback,
                )

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return

    # ── Display Results ──
    progress_placeholder.empty()

    if not results:
        st.warning(
            f"No results found for the given search parameters. "
            f"Try adjusting your keyword or date range."
        )
        return

    # Normalize to standard DataFrame
    df = normalize_results(results, newspaper_name)

    # Metrics row
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("#### Results")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Articles", len(df))
    with col2:
        unique_dates = df["Date"].nunique()
        st.metric("Unique Dates", unique_dates)
    with col3:
        st.metric("Source", newspaper_name)

    # Results table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "URL": st.column_config.LinkColumn("URL", display_text="Open"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Newspaper": st.column_config.TextColumn("Newspaper", width="small"),
        },
    )

    # CSV download
    csv_bytes = results_to_csv_bytes(df)
    safe_name = config["key"]
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_bytes,
        file_name=f"{safe_name}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.success(f"Found {len(df)} articles from {newspaper_name}.")


# ──────────────────────────────────────────────
# Render all scraper tabs
# ──────────────────────────────────────────────

for i, (name, cfg) in enumerate(NEWSPAPER_CONFIG.items(), start=1):
    render_scraper_tab(tabs[i], name, cfg)


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown(
    '<p style="text-align: center; color: #9ca3af; font-size: 0.8rem;">'
    'NewsScraper Dashboard — Built with Streamlit | '
    '6 newspapers, one interface | '
    'Developer: MD FAZLEY ELAHI'
    '</p>',
    unsafe_allow_html=True,
)
