"""
Budget Baker - Entrypoint
Multi-page app router using st.navigation
"""

import streamlit as st

# Page configuration - only set once in the entrypoint
st.set_page_config(
    page_title="Budget Baker",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state (shared across all pages)
if 'parsed_df' not in st.session_state:
    st.session_state.parsed_df = None
if 'format_name' not in st.session_state:
    st.session_state.format_name = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'categorized_df' not in st.session_state:
    st.session_state.categorized_df = None
if 'use_ai' not in st.session_state:
    st.session_state.use_ai = False
if 'api_key' not in st.session_state:
    st.session_state.api_key = None
if 'category_edits' not in st.session_state:
    st.session_state.category_edits = {}

# Custom CSS for baking theme (applied globally to all pages)
st.markdown("""
<style>
    /* Import Inter font for better readability */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Apply Inter font to all text elements */
    html, body, [class*="css"], .stApp,
    [data-testid="stMarkdownContainer"],
    [data-testid="stText"], p, div, span {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /*
     * Restore Material Symbols Rounded for all icon elements.
     * Streamlit renders icons as <span> elements whose text content is a
     * Material Symbols ligature (e.g. "arrow_downward").  The broad Inter
     * override above breaks these ligatures, causing raw text like
     * "keyboard_arrow_downward" to appear instead of the icon glyph.
     *
     * We fix this with a high-specificity selector and !important so it
     * wins over the Inter rule.
     */
    [data-testid="stIconMaterial"],
    [data-testid="stIconMaterial"] *,
    [data-testid*="Icon"] span[translate="no"],
    span[translate="no"][data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded' !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        font-feature-settings: 'liga' !important;
    }

    /* Also restore icons inside Glide Data Grid (st.dataframe / st.data_editor).
     * The grid renders column-type icons and sort arrows using Material Symbols
     * inside a canvas overlay and popup menus.  Target any span whose computed
     * style would be Material Symbols. */
    [data-testid="stDataFrame"] span[translate="no"],
    [data-testid="stDataFrameResizable"] span[translate="no"],
    [data-testid="stDataFrame"] [style*="Material"],
    [data-testid="stDataFrameResizable"] [style*="Material"] {
        font-family: 'Material Symbols Rounded' !important;
    }

    /* Enable tabular figures for financial data */
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"],
    .stDataFrame,
    [data-testid="stDataFrameResizable"],
    .financial-number {
        font-feature-settings: 'tnum' 1;
        font-variant-numeric: tabular-nums;
    }

    /* Main content: Light cream background */
    .stApp {
        background-color: #FFFBF0 !important;
    }

    /* Sidebar: Warmer peachy-tan color for contrast */
    [data-testid="stSidebar"] {
        background-color: #FFE8CC !important;
    }

    /* Sidebar content area */
    [data-testid="stSidebar"] > div:first-child {
        background-color: #FFE8CC !important;
    }

    /* Hide sidebar collapse button completely */
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    /* Hide collapsed sidebar expand button */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Main content area with cream background */
    .stMainBlockContainer {
        padding-left: 5rem !important;
        padding-right: 5rem !important;
        max-width: 1400px !important;
        margin: 0 auto !important;
        background-color: #FFFBF0 !important;
    }

    /* Ensure all blocks have cream background */
    .block-container {
        background-color: #FFFBF0 !important;
    }

    /* Mixing Bowl Upload Area Styling */
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, #FEF3E2 0%, #FEFAF5 100%);
        border: 3px dashed #D97706;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(217, 119, 6, 0.1);
        transition: all 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #C2690A;
        background: linear-gradient(135deg, #FEF9F2 0%, #FFF 100%);
        box-shadow: 0 6px 12px rgba(217, 119, 6, 0.15);
        transform: translateY(-2px);
    }

    /* Upload button styling */
    [data-testid="stFileUploader"] button {
        background-color: #D97706 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background-color: #C2690A !important;
        transform: scale(1.05) !important;
    }

    /* Section headers with baking theme */
    h2 {
        color: #92400E !important;
        border-bottom: 3px solid #FED7AA !important;
        padding-bottom: 0.5rem !important;
        margin-top: 2rem !important;
    }

    /* Metrics boxes */
    [data-testid="stMetricValue"] {
        color: #92400E !important;
        font-weight: 700 !important;
    }

    /* Success messages */
    .stSuccess {
        background-color: #FEF3E2 !important;
        border-left: 5px solid #D97706 !important;
    }

    /* Info messages */
    .stInfo {
        background-color: #FEF3E2 !important;
        border-left: 5px solid #D97706 !important;
    }

    /* Recipe Card Component */
    .recipe-card {
        background: linear-gradient(135deg, #FFFBF0 0%, #FEF3E2 100%);
        border: 2px solid #FED7AA;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.08);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }

    .recipe-card:hover {
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.12);
        transform: translateY(-2px);
    }

    /* Button Hierarchy */
    .stButton > button {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.3s ease !important;
    }

    /* Primary button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #EA580C 0%, #D97706 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(217, 119, 6, 0.25) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #C2410C 0%, #B45309 100%) !important;
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.35) !important;
        transform: translateY(-2px) !important;
    }

    /* Secondary button styling */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        color: #92400E !important;
        border: 2px solid #D97706 !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #FEF3E2 !important;
        border-color: #B45309 !important;
    }

    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.25) !important;
    }

    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.35) !important;
        transform: translateY(-2px) !important;
    }

    /* Touch-friendly sizing for mobile */
    @media (hover: none) {
        button, a, [role="button"] {
            min-height: 44px !important;
            min-width: 44px !important;
        }
    }

    /* Mobile responsive padding */
    @media (max-width: 768px) {
        .stMainBlockContainer {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .stButton > button {
            width: 100% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Define pages using st.Page and st.navigation (Streamlit V2 multipage API)
home_page = st.Page(
    "pages/0_🥣_Home.py",
    title="Add Ingredients",
    icon="🥣",
    default=True,
)
bake_page = st.Page(
    "pages/1_🔥_Bake.py",
    title="Bake Budget",
    icon="🔥",
)
results_page = st.Page(
    "pages/2_🍰_Results.py",
    title="Review Results",
    icon="🍰",
)
serve_page = st.Page(
    "pages/3_🧁_Serve.py",
    title="Serve",
    icon="🧁",
)

# Register navigation - this renders clickable sidebar links automatically
current_page = st.navigation(
    [home_page, bake_page, results_page, serve_page],
    position="sidebar",
    expanded=True,
)

# Run the selected page
current_page.run()
