# ---------------------------------------------------------------------------
# theme.py
# Global design system for OTTO – BG S&S Pricing Engine HC3.0
# Palette:  Navy #0f2067 | Mint #85db9c | Lavender #b999f6
#           Magenta #a50091 | Pink #d03e9d
# ---------------------------------------------------------------------------

from __future__ import annotations
import base64
import pathlib
import streamlit as st


# ── Palette ────────────────────────────────────────────────────────────────
P = {
    "navy":     "#0f2067",
    "navy_mid": "#152880",
    "mint":     "#85db9c",
    "lavender": "#b999f6",
    "magenta":  "#a50091",
    "pink":     "#d03e9d",
    "bg":       "#f4f6fb",
    "white":    "#ffffff",
    "border":   "#e0e6f0",
    "muted":    "#6b7280",
}

# ── Helpers ────────────────────────────────────────────────────────────────

def _img_b64(rel_path: str) -> str | None:
    """Read a file relative to the workspace root and return base64 string."""
    p = pathlib.Path(rel_path)
    if not p.exists():
        return None
    return base64.b64encode(p.read_bytes()).decode()


def _ext(path: str) -> str:
    return pathlib.Path(path).suffix.lstrip(".").lower() or "png"


# ── Global CSS ─────────────────────────────────────────────────────────────

_GLOBAL_CSS = """
<style>
/* ── Font ──────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"], .stApp {{
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}}

/* ── App Background ─────────────────────────────────────────────────────── */
.stApp {{
    background: {bg};
}}

/* ── Top Header Bar ─────────────────────────────────────────────────────── */
header[data-testid="stHeader"] {{
    background: {navy} !important;
    border-bottom: 2px solid {mint};
}}
header[data-testid="stHeader"] button,
header[data-testid="stHeader"] svg {{
    color: {mint} !important;
    fill: {mint} !important;
}}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background: linear-gradient(175deg, {navy} 0%, {navy_mid} 100%) !important;
    border-right: 1px solid rgba(133,219,156,0.2);
    min-width: 16.8rem !important;
    max-width: 16.8rem !important;
    width: 16.8rem !important;
}}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span,
[data-testid="stSidebar"] .stMarkdown li {{
    color: #ffffff !important;
    font-size: 0.82rem;
}}
[data-testid="stSidebar"] hr {{
    border-color: rgba(133,219,156,0.25) !important;
}}

/* Centrica logo — fixed to top of sidebar, above nav links */
.otto-sidebar-logo-fixed {{
    position: fixed;
    top: 0;
    left: 0;
    width: 16.8rem;         /* matches narrowed sidebar width */
    padding: 10px 16px;
    background: linear-gradient(175deg, {navy} 0%, {navy_mid} 100%);
    border-bottom: 1px solid rgba(133,219,156,0.25);
    z-index: 9999;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.otto-sidebar-logo-fixed img {{
    height: 44px;
    width: auto;
    max-width: 60%;         /* 40% narrower than the full bar */
    object-fit: contain;
    display: block;
}}
/* Push sidebar nav down to clear the fixed logo bar (~64px bar) */
[data-testid="stSidebarContent"] {{
    padding-top: 74px !important;
}}

/* Remove any CSS for st.logo() — no longer used */

/* Nav links — broad selectors to cover all Streamlit versions */
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] a span,
[data-testid="stSidebarNav"] a p,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] li span,
[data-testid="stSidebarNav"] li p,
[data-testid="stSidebarNav"] div,
[data-testid="stSidebarNav"] div span,
section[data-testid="stSidebar"] nav a,
section[data-testid="stSidebar"] nav span,
section[data-testid="stSidebar"] nav li,
section[data-testid="stSidebar"] nav p {{
    color: #ffffff !important;
    border-radius: 6px !important;
}}
[data-testid="stSidebarNav"] a {{
    padding: 0.45rem 0.75rem !important;
    margin: 1px 4px !important;
    transition: all 0.18s ease;
    font-size: 0.88rem;
    font-weight: 400;
}}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebarNav"] a:hover span,
[data-testid="stSidebarNav"] a:hover p {{
    background: rgba(133,219,156,0.14) !important;
    color: {mint} !important;
}}
[data-testid="stSidebarNav"] a[aria-selected="true"],
[data-testid="stSidebarNav"] a[aria-current="page"],
[data-testid="stSidebarNav"] a[aria-selected="true"] span,
[data-testid="stSidebarNav"] a[aria-current="page"] span {{
    background: rgba(133,219,156,0.18) !important;
    color: {mint} !important;
    font-weight: 600 !important;
    border-left: 3px solid {mint};
}}

/* Nav section separators — bold pill badges */
[data-testid="stSidebarNavSeparator"],
[data-testid="stSidebarNavSeparator"] > div {{
    background: rgba(208,62,157,0.22) !important;
    border-left: 3px solid {pink} !important;
    border-radius: 0 6px 6px 0 !important;
    margin: 8px 4px 2px 0 !important;
    padding: 4px 10px !important;
}}
[data-testid="stSidebarNavSeparator"] p,
[data-testid="stSidebarNavSeparator"] span {{
    color: #ffffff !important;
    font-size: 0.72rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    margin: 0 !important;
}}

/* Always expand nav — override Streamlit's collapsed max-height */
[data-testid="stSidebarNavItems"] {{
    max-height: none !important;
    overflow: visible !important;
}}
/* Hide the 'Show more / Show less' toggle button */
[data-testid="stSidebarNav"] > div > button,
[data-testid="stSidebarNavCollapseButton"],
section[data-testid="stSidebar"] nav > button {{
    display: none !important;
}}

/* ── Page Headings ──────────────────────────────────────────────────────── */
h1 {{ color: {navy} !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }}
h2 {{ color: {navy} !important; font-weight: 600 !important; }}
h3 {{ color: {navy_mid} !important; font-weight: 500 !important; }}

/* ── Divider ────────────────────────────────────────────────────────────── */
hr {{
    border: none !important;
    border-top: 1px solid {mint} !important;
    margin: 1.25rem 0 !important;
    opacity: 0.5;
}}

/* ── Buttons ────────────────────────────────────────────────────────────── */
.stButton > button {{
    background: {navy};
    color: #ffffff;
    border: 1px solid transparent;
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.875rem;
    letter-spacing: 0.02em;
    padding: 0.5rem 1.5rem;
    transition: all 0.18s ease;
    box-shadow: 0 1px 3px rgba(15,32,103,0.15);
}}
.stButton > button:hover {{
    background: {navy_mid};
    border-color: {mint};
    color: {mint};
    box-shadow: 0 4px 12px rgba(15,32,103,0.25);
    transform: translateY(-1px);
}}
.stButton > button:active {{
    transform: translateY(0);
}}
/* Primary button */
[data-testid="stBaseButton-primary"] {{
    background: linear-gradient(135deg, {magenta} 0%, {pink} 100%) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(165,0,145,0.3) !important;
}}
[data-testid="stBaseButton-primary"]:hover {{
    background: linear-gradient(135deg, {pink} 0%, {magenta} 100%) !important;
    box-shadow: 0 4px 14px rgba(165,0,145,0.45) !important;
    color: #ffffff !important;
    border-color: transparent !important;
    transform: translateY(-1px);
}}

/* ── Download Button ────────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {{
    background: {navy} !important;
    color: {mint} !important;
    border: 1px solid {mint} !important;
    border-radius: 6px;
    font-weight: 500;
}}
[data-testid="stDownloadButton"] > button:hover {{
    background: {mint} !important;
    color: {navy} !important;
    box-shadow: 0 4px 12px rgba(133,219,156,0.35) !important;
}}

/* ── Metrics ────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background: {white};
    border: 1px solid {border};
    border-top: 3px solid {navy};
    border-radius: 8px;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 2px 8px rgba(15,32,103,0.06);
}}
[data-testid="stMetricLabel"] > div {{
    color: {muted} !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}
[data-testid="stMetricValue"] > div {{
    color: {navy} !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.8rem !important;
}}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 2px solid {border};
    gap: 0;
    background: transparent;
}}
[data-testid="stTabs"] button[role="tab"] {{
    color: {muted};
    font-weight: 500;
    font-size: 0.88rem;
    padding: 0.7rem 1.4rem;
    border: none;
    border-bottom: 3px solid transparent;
    background: transparent;
    transition: all 0.18s ease;
    letter-spacing: 0.01em;
}}
[data-testid="stTabs"] button[role="tab"]:hover {{
    color: {navy};
    background: rgba(133,219,156,0.08);
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: {navy};
    font-weight: 700;
    border-bottom: 3px solid {mint};
    background: transparent;
}}

/* ── DataFrames ─────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid {border};
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(15,32,103,0.05);
}}
[data-testid="stDataFrame"] th {{
    background: {navy} !important;
    color: #ffffff !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ── File Uploader ──────────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {{
    border: 2px dashed {lavender} !important;
    border-radius: 8px !important;
    background: rgba(185,153,246,0.04) !important;
    transition: all 0.2s;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {navy} !important;
    background: rgba(15,32,103,0.03) !important;
}}
[data-testid="stFileUploader"] small {{
    color: {muted} !important;
}}

/* ── Selectbox / Multiselect ─────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {{
    border-radius: 6px !important;
}}

/* ── Alert / Info boxes ─────────────────────────────────────────────────── */
[data-testid="stAlert"][data-baseweb="notification"][kind="info"],
div[data-testid="stInfo"] {{
    background: rgba(15,32,103,0.05) !important;
    border-left: 4px solid {navy} !important;
    border-radius: 0 8px 8px 0 !important;
    color: {navy} !important;
}}
[data-testid="stAlert"][data-baseweb="notification"][kind="success"],
div[data-testid="stSuccess"] {{
    background: rgba(133,219,156,0.12) !important;
    border-left: 4px solid {mint} !important;
    border-radius: 0 8px 8px 0 !important;
}}
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"],
div[data-testid="stWarning"] {{
    border-left: 4px solid {lavender} !important;
    border-radius: 0 8px 8px 0 !important;
}}
[data-testid="stAlert"][data-baseweb="notification"][kind="error"],
div[data-testid="stError"] {{
    border-left: 4px solid {magenta} !important;
    border-radius: 0 8px 8px 0 !important;
}}

/* ── Spinner ────────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] > div {{
    border-top-color: {navy} !important;
    border-right-color: {mint} !important;
}}
[data-testid="stSpinner"] p {{
    color: {navy} !important;
    font-weight: 500;
}}

/* ── Expander ───────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    border: 1px solid {border} !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 4px rgba(15,32,103,0.05);
}}
details[data-testid="stExpander"] summary {{
    color: {navy} !important;
    font-weight: 600 !important;
    font-size: 0.9rem;
}}

/* ── Data Editor ────────────────────────────────────────────────────────── */
[data-testid="stDataEditor"] {{
    border: 1px solid {border} !important;
    border-radius: 8px !important;
    overflow: hidden;
}}

/* ── Radio ──────────────────────────────────────────────────────────────── */
[data-testid="stRadio"] label {{
    color: {navy} !important;
    font-weight: 500 !important;
}}

/* ── Custom spinner keyframes ───────────────────────────────────────────── */
@keyframes otto-pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.4; }}
}}
@keyframes otto-spin {{
    0% {{ transform: rotate(0deg); }}
    100% {{ transform: rotate(360deg); }}
}}
.otto-spinner-ring {{
    display: inline-block; width: 36px; height: 36px;
    border: 4px solid rgba(15,32,103,0.12);
    border-top: 4px solid {navy};
    border-right: 4px solid {mint};
    border-radius: 50%;
    animation: otto-spin 0.75s linear infinite;
    vertical-align: middle; margin-right: 12px;
}}
.otto-loading-row {{
    display: flex; align-items: center;
    padding: 1rem 0; color: {navy};
    font-weight: 500; font-size: 0.95rem;
}}

/* ── Section card ───────────────────────────────────────────────────────── */
.otto-section-card {{
    background: {white};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 2px 8px rgba(15,32,103,0.05);
}}

/* ── OTTO Logo top-right fixed overlay ──────────────────────────────────── */
.otto-logo-bar {{
    position: fixed;
    top: 8px;
    right: 18px;
    z-index: 9999;
    height: 46px;
    display: flex; align-items: center;
}}
.otto-logo-bar img {{
    height: 40px;
    object-fit: contain;
    filter: brightness(0) invert(1);  /* white when on dark header */
}}

/* ── Page header block ──────────────────────────────────────────────────── */
.otto-page-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0 0.25rem 0;
    margin-bottom: 0.5rem;
}}
.otto-page-header .header-left {{
    display: flex;
    align-items: center;
    gap: 0.85rem;
    flex: 1;
}}
.otto-page-header .icon {{
    font-size: 1.75rem;
    line-height: 1;
}}
.otto-page-header h1 {{
    margin: 0 !important;
    padding: 0 !important;
    font-weight: 700 !important;
    font-size: 1.7rem !important;
    color: {navy} !important;
    letter-spacing: -0.02em;
}}
.otto-page-header .subtitle {{
    margin: 2px 0 0 0 !important;
    color: {muted} !important;
    font-size: 0.82rem !important;
    font-weight: 400;
}}
.otto-divider {{
    height: 2px;
    background: linear-gradient(90deg, {mint} 0%, {lavender} 60%, transparent 100%);
    border: none !important;
    margin: 0.6rem 0 1.25rem 0 !important;
    opacity: 0.6;
    border-radius: 2px;
}}
.otto-section-heading {{
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    color: {navy} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin: 1rem 0 0.5rem !important;
    padding-bottom: 0.35rem;
    border-bottom: 1.5px solid {mint};
    display: inline-block;
}}

/* ── Tabs: mint background, navy text, active = navy bg + white text ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    background-color: {mint} !important;
    color: {navy} !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 8px 20px !important;
    border: none !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    background-color: #6ecf88 !important;
    color: {navy} !important;
}}
.stTabs [aria-selected="true"] {{
    background-color: {navy} !important;
    color: #ffffff !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{
    display: none !important;
}}
.stTabs [data-baseweb="tab-border"] {{
    background-color: {mint} !important;
    height: 2px !important;
}}
</style>
""".format(**P)


# ── Public API ─────────────────────────────────────────────────────────────

def inject_css() -> None:
    """Inject global CSS. Call from app_main.py immediately after set_page_config."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    _inject_nav_section_js()


def _inject_nav_section_js() -> None:
    """Inject JS via components.html so it executes in a real browser context.
    Uses window.parent.document to reach Streamlit's sidebar nav from the iframe."""
    try:
        import streamlit.components.v1 as components
    except ImportError:
        return

    components.html(
        """
        <script>
        (function() {
            var NAMES = ['Info','Upload','Calculate','Explore','Download'];
            var PILL  = [
                'color:#ffffff',
                'font-weight:800',
                'font-size:0.72rem',
                'letter-spacing:0.14em',
                'text-transform:uppercase',
                'background:rgba(208,62,157,0.22)',
                'border-left:3px solid #d03e9d',
                'border-radius:0 6px 6px 0',
                'padding:4px 10px',
                'margin:8px 4px 2px 0',
                'display:block'
            ].join(';');

            function run() {
                try {
                    var doc = window.parent.document;
                    var nav = doc.querySelector('[data-testid="stSidebarNav"]');
                    if (!nav) return;

                    // 1. Target known data-testid separators
                    var tids = ['stSidebarNavSeparator','stSidebarNavSectionHeader',
                                'stSidebarNavGroupHeader','stSidebarNavHeader'];
                    tids.forEach(function(tid) {
                        doc.querySelectorAll('[data-testid="' + tid + '"]').forEach(function(el) {
                            el.setAttribute('style', PILL);
                        });
                    });

                    // 2. Scan every leaf text node for exact section name matches
                    nav.querySelectorAll('*').forEach(function(el) {
                        if (el.children.length > 0) return;
                        var txt = (el.textContent || '').trim();
                        if (NAMES.indexOf(txt) === -1) return;
                        // Skip page links (About, Rating & Input, etc.)
                        if (el.closest('a')) return;
                        // Style el itself as a full-width block — never touch the parent
                        // (parent also contains page-link rows so we must not style it)
                        el.setAttribute('style',
                            'display:block !important;' +
                            'width:100% !important;' +
                            'box-sizing:border-box !important;' +
                            'background:rgba(208,62,157,0.25) !important;' +
                            'border-left:3px solid #d03e9d !important;' +
                            'padding:4px 10px 4px 8px !important;' +
                            'margin:6px 0 2px 0 !important;' +
                            'color:#ffffff !important;' +
                            'font-weight:800 !important;' +
                            'font-size:0.72rem !important;' +
                            'letter-spacing:0.14em !important;' +
                            'text-transform:uppercase !important;'
                        );
                    });
                } catch(e) {}
            }

            // Run now and after each DOM mutation
            run();
            var ob = new MutationObserver(run);
            try {
                ob.observe(window.parent.document.body,
                           {childList: true, subtree: true});
            } catch(e) {}
        })();
        </script>
        """,
        height=0,
    )


def page_header(title: str, icon: str = "", subtitle: str = "") -> None:
    """Render a branded page header: title on left, OTTO logo on right via st.image."""

    icon_html = f'<span class="icon">{icon}</span>' if icon else ""
    sub_html  = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""

    # Use st.columns so st.image() controls the logo — bypasses HTML/CSS size constraints
    col_title, col_logo = st.columns([7, 1])

    with col_title:
        st.markdown(
            f"""
            <div class="otto-page-header" style="justify-content:flex-start;">
                <div class="header-left">
                    {icon_html}
                    <div>
                        <h1>{title}</h1>
                        {sub_html}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_logo:
        logo_path = pathlib.Path("OTTO_Logo.png")
        if logo_path.exists():
            st.image(str(logo_path), use_column_width=True)

    st.markdown('<div class="otto-divider"></div>', unsafe_allow_html=True)


def inject_centrica_logo(logo_path: str = "Centrica_home.png") -> None:
    """Render Centrica logo as a full-width horizontal banner in the sidebar.
    Call from app_main.py instead of st.logo()."""
    b64 = _img_b64(logo_path)
    ext = _ext(logo_path)
    if b64 is None:
        return
    st.sidebar.markdown(
        f"""
        <div class="otto-sidebar-logo-fixed">
            <div style="background:rgba(255,255,255,0.92); border-radius:7px;
                        padding:6px 14px; display:inline-block;">
                <img src="data:image/{ext};base64,{b64}"
                     alt="Centrica"
                     class="">
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_divider() -> None:
    """Render a subtle gradient divider between page sections."""
    st.markdown('<div class="otto-divider"></div>', unsafe_allow_html=True)


def section_heading(text: str) -> None:
    """Render a small uppercase section label."""
    st.markdown(f'<p class="otto-section-heading">{text}</p>', unsafe_allow_html=True)


def loading_html(message: str = "Processing…") -> str:
    """Return HTML for a branded loading indicator (use inside st.markdown)."""
    return f"""
    <div class="otto-loading-row">
        <span class="otto-spinner-ring"></span>
        <span>{message}</span>
    </div>
    """


def kpi_card(label: str, value: str, color: str = P["navy"], bg: str = "#ffffff") -> str:
    """Return HTML for a single KPI card (to embed in st.markdown)."""
    return f"""
    <div style="background:{bg}; border:1px solid {P['border']}; border-top:3px solid {color};
                border-radius:8px; padding:1rem 1.25rem;
                box-shadow:0 2px 8px rgba(15,32,103,0.06); text-align:center;">
        <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase;
                    letter-spacing:0.08em; color:{P['muted']}; margin-bottom:0.3rem;">
            {label}
        </div>
        <div style="font-size:1.55rem; font-weight:700; color:{color};">
            {value}
        </div>
    </div>
    """


def render_table(df, stripe: bool = True, compact: bool = False) -> None:
    """Render a pandas DataFrame as a styled HTML table.

    Uses st.components.v1.html() to guarantee the table renders with full
    inline CSS — st.markdown() sanitises <table> elements in some Streamlit
    versions which strips the styling silently.

    Parameters
    ----------
    df      : DataFrame to render.
    stripe  : Alternate row shading (default True).
    compact : Smaller font / padding for tight column layouts (default False).
    """
    import streamlit.components.v1 as components
    import pandas as pd

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.info("No data to display.")
        return

    pad   = "5px 10px"  if compact else "8px 14px"
    fsize = "13px"      if compact else "14px"
    navy  = P["navy"]
    white = "#ffffff"
    light = "#f4f6fb"
    bdr   = P["border"]

    # Header row
    th_style = (
        f"background:{navy}; color:{white}; padding:{pad}; font-size:{fsize}; "
        f"font-weight:700; text-align:left; border:1px solid {bdr}; "
        f"letter-spacing:0.04em; white-space:nowrap;"
    )
    headers = "".join(f'<th style="{th_style}">{col}</th>' for col in df.columns)

    # Data rows
    row_html = []
    for i, (_, row) in enumerate(df.iterrows()):
        bg = light if (stripe and i % 2 == 0) else white
        cells = "".join(
            f'<td style="background:{bg}; color:#1a1a2e; padding:{pad}; '
            f'font-size:{fsize}; border:1px solid {bdr}; white-space:nowrap;">{val}</td>'
            for val in row
        )
        row_html.append(f"<tr>{cells}</tr>")

    table_html = (
        '<div style="overflow-x:auto; border-radius:8px; '
        'box-shadow:0 2px 10px rgba(15,32,103,0.10); margin-bottom:2px;">'
        '<table style="width:100%; border-collapse:collapse; '
        'font-family:Inter,Arial,sans-serif;">'
        f'<thead><tr>{headers}</tr></thead>'
        f'<tbody>{"".join(row_html)}</tbody>'
        '</table></div>'
    )

    full_html = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8">'
        '<style>*{margin:0;padding:0;box-sizing:border-box;}</style>'
        '</head>'
        f'<body style="background:{light}; font-family:Inter,Arial,sans-serif;">'
        f'{table_html}'
        '</body></html>'
    )

    row_h  = 32 if compact else 40
    height = (len(df) + 1) * row_h + 24   # +1 for header, +24 for shadow/margin
    components.html(full_html, height=height, scrolling=False)


# ── Hourglass loader animation ────────────────────────────────────────────────

_HOURGLASS_HTML = """\
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#f4f6fb;display:flex;flex-direction:column;
      align-items:center;justify-content:center;height:100vh;
      font-family:Inter,Arial,sans-serif;}}
.hourglassBackground{{position:relative;background-color:rgb(71,60,60);
  height:130px;width:130px;border-radius:50%;margin:0 auto 12px;}}
.hourglassContainer{{position:absolute;top:30px;left:40px;width:50px;height:70px;
  -webkit-animation:hourglassRotate 2s ease-in 0s infinite;
  animation:hourglassRotate 2s ease-in 0s infinite;
  transform-style:preserve-3d;perspective:1000px;}}
.hourglassContainer div,.hourglassContainer div:before,
.hourglassContainer div:after{{transform-style:preserve-3d;}}
@-webkit-keyframes hourglassRotate{{0%{{transform:rotateX(0deg);}}
  50%{{transform:rotateX(180deg);}}100%{{transform:rotateX(180deg);}}}}
@keyframes hourglassRotate{{0%{{transform:rotateX(0deg);}}
  50%{{transform:rotateX(180deg);}}100%{{transform:rotateX(180deg);}}}}
.hourglassCapTop{{top:0;}}.hourglassCapTop:before{{top:-25px;}}
.hourglassCapTop:after{{top:-20px;}}.hourglassCapBottom{{bottom:0;}}
.hourglassCapBottom:before{{bottom:-25px;}}.hourglassCapBottom:after{{bottom:-20px;}}
.hourglassGlassTop{{transform:rotateX(90deg);position:absolute;top:-16px;left:3px;
  border-radius:50%;width:44px;height:44px;background-color:#999999;}}
.hourglassGlass{{perspective:100px;position:absolute;top:32px;left:20px;
  width:10px;height:6px;background-color:#999999;opacity:0.5;}}
.hourglassGlass:before,.hourglassGlass:after{{content:'';display:block;
  position:absolute;background-color:#999999;left:-17px;width:44px;height:28px;}}
.hourglassGlass:before{{top:-27px;border-radius:0 0 25px 25px;}}
.hourglassGlass:after{{bottom:-27px;border-radius:25px 25px 0 0;}}
.hourglassCurves:before,.hourglassCurves:after{{content:'';display:block;
  position:absolute;top:32px;width:6px;height:6px;border-radius:50%;
  background-color:#333;animation:hideCurves 2s ease-in 0s infinite;}}
.hourglassCurves:before{{left:15px;}}.hourglassCurves:after{{left:29px;}}
@-webkit-keyframes hideCurves{{0%{{opacity:1;}}25%{{opacity:0;}}
  30%{{opacity:0;}}40%{{opacity:1;}}100%{{opacity:1;}}}}
@keyframes hideCurves{{0%{{opacity:1;}}25%{{opacity:0;}}
  30%{{opacity:0;}}40%{{opacity:1;}}100%{{opacity:1;}}}}
.hourglassSandStream:before{{content:'';display:block;position:absolute;
  left:24px;width:3px;background-color:white;
  -webkit-animation:sandStream1 2s ease-in 0s infinite;
  animation:sandStream1 2s ease-in 0s infinite;}}
.hourglassSandStream:after{{content:'';display:block;position:absolute;
  top:36px;left:19px;border-left:6px solid transparent;
  border-right:6px solid transparent;border-bottom:6px solid #fff;
  animation:sandStream2 2s ease-in 0s infinite;}}
@-webkit-keyframes sandStream1{{0%{{height:0;top:35px;}}50%{{height:0;top:45px;}}
  60%{{height:35px;top:8px;}}85%{{height:35px;top:8px;}}100%{{height:0;top:8px;}}}}
@keyframes sandStream1{{0%{{height:0;top:35px;}}50%{{height:0;top:45px;}}
  60%{{height:35px;top:8px;}}85%{{height:35px;top:8px;}}100%{{height:0;top:8px;}}}}
@-webkit-keyframes sandStream2{{0%{{opacity:0;}}50%{{opacity:0;}}51%{{opacity:1;}}
  90%{{opacity:1;}}91%{{opacity:0;}}100%{{opacity:0;}}}}
@keyframes sandStream2{{0%{{opacity:0;}}50%{{opacity:0;}}51%{{opacity:1;}}
  90%{{opacity:1;}}91%{{opacity:0;}}100%{{opacity:0;}}}}
.hourglassSand:before,.hourglassSand:after{{content:'';display:block;
  position:absolute;left:6px;background-color:white;perspective:500px;}}
.hourglassSand:before{{top:8px;width:39px;border-radius:3px 3px 30px 30px;
  animation:sandFillup 2s ease-in 0s infinite;}}
.hourglassSand:after{{border-radius:30px 30px 3px 3px;
  animation:sandDeplete 2s ease-in 0s infinite;}}
@-webkit-keyframes sandFillup{{0%{{opacity:0;height:0;}}60%{{opacity:1;height:0;}}
  100%{{opacity:1;height:17px;}}}}
@keyframes sandFillup{{0%{{opacity:0;height:0;}}60%{{opacity:1;height:0;}}
  100%{{opacity:1;height:17px;}}}}
@-webkit-keyframes sandDeplete{{0%{{opacity:0;top:45px;height:17px;width:38px;left:6px;}}
  1%{{opacity:1;top:45px;height:17px;width:38px;left:6px;}}
  24%{{opacity:1;top:45px;height:17px;width:38px;left:6px;}}
  25%{{opacity:1;top:41px;height:17px;width:38px;left:6px;}}
  50%{{opacity:1;top:41px;height:17px;width:38px;left:6px;}}
  90%{{opacity:1;top:41px;height:0;width:10px;left:20px;}}}}
@keyframes sandDeplete{{0%{{opacity:0;top:45px;height:17px;width:38px;left:6px;}}
  1%{{opacity:1;top:45px;height:17px;width:38px;left:6px;}}
  24%{{opacity:1;top:45px;height:17px;width:38px;left:6px;}}
  25%{{opacity:1;top:41px;height:17px;width:38px;left:6px;}}
  50%{{opacity:1;top:41px;height:17px;width:38px;left:6px;}}
  90%{{opacity:1;top:41px;height:0;width:10px;left:20px;}}}}
</style></head>
<body>
  <div class="hourglassBackground">
    <div class="hourglassContainer">
      <div class="hourglassCurves"></div>
      <div class="hourglassCapTop"><div class="hourglassGlassTop"></div></div>
      <div class="hourglassCapBottom"><div class="hourglassGlass"></div></div>
      <div class="hourglassSandStream"></div>
      <div class="hourglassSand"></div>
    </div>
  </div>
  <p style="color:#0f2067;font-weight:700;font-size:15px;margin-top:4px;
            letter-spacing:0.03em;">{message}</p>
</body></html>"""


def render_loader(message: str = "Calculating prices\u2026") -> None:
    """Render the hourglass CSS animation via st.components.v1.html().
    Call inside ``with st.empty():`` to control placement and clearing."""
    import streamlit.components.v1 as components
    html = _HOURGLASS_HTML.replace("{message}", message)
    components.html(html, height=220, scrolling=False)
