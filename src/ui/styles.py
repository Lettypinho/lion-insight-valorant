"""CSS da aplicação. Customizações pontuais sobre os componentes nativos do Streamlit."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&display=swap');
/* fonte so nos textos: NAO usar seletor generico, senao quebra a fonte de icones do Streamlit */
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp td, .stApp th, .stApp button, .stApp input, .stApp textarea,
[data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stMetricDelta"],
[data-testid="stExpander"] summary p { font-family: 'Figtree', system-ui, sans-serif; }
.block-container { padding-top: 1.6rem; max-width: 1240px; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { line-height: 1.35; }
[data-testid="stSidebar"] hr { margin: .7rem 0; }
h1 { font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.1rem; }
[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; font-weight: 650; }
.sub { opacity: .72; font-size: .95rem; margin: 0 0 1.1rem 0; }
.chip { display:inline-flex; align-items:center; gap:.4rem; font-size:.78rem; font-weight:600;
        padding:.12rem .6rem; border-radius:999px; margin-bottom:.45rem;
        border:1px solid color-mix(in srgb, var(--c) 60%, transparent);
        background: color-mix(in srgb, var(--c) 13%, transparent); }
.chip i { color: var(--c); font-style: normal; font-weight:800; }
.ctitle { font-size:1.08rem; font-weight:650; margin:0 0 .15rem 0; }
.ctext  { margin:0 0 .6rem 0; line-height:1.45; }
.note   { opacity:.7; font-size:.85rem; }
</style>
"""


def apply_styles():
    st.markdown(CSS, unsafe_allow_html=True)
