import streamlit as st
from streamlit.runtime.scriptrunner import RerunData, RerunException
from streamlit.source_util import get_pages


def standardize_name(name: str) -> str:
    return name.lower().replace("_", " ")


def switch_page(page_name: str):
    """
    Switch page programmatically in a multipage app

    Args:
        page_name (str): Target page name
    """
    page_name = standardize_name(page_name)
    pages = get_pages("main.py")  # Name of entrypoint script

    for page_hash, config in pages.items():
        if standardize_name(config["page_name"]) == page_name:
            raise RerunException(
                RerunData(
                    page_script_hash=page_hash,
                    page_name=page_name,
                )
            )

    page_names = [
        standardize_name(config["page_name"]) for config in pages.values()
    ]

    raise ValueError(
        f"Could not find page {page_name}. Must be one of {page_names}"
    )


def set_page_style():
    """
    Set custom CSS styles for the page
    """
    style = """
    <style>
    div[data-testid="stButton"] {
        text-align: right;
    }
    label[data-baseweb="radio"] {
        border: 1px solid rgb(50, 50, 50) !important;
        padding: 1rem 1rem;
        border-radius: 0.5rem;
        margin: 0;
        width: 100%;
        height: 100%;
    }
    label:has(.st-aw) {
        background-color: rgb(93, 50, 50);
    }
    label:has(.st-aw) * {
        color: white;
    }
    div[role="radiogroup"] {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }
    div[data-testid="stChatMessage"] {
        gap: 1rem !important;
    }
    div[data-testid="stPageLink"] div {
        align-items: flex-end;
    }
    a[data-testid="stPageLink-NavLink"] {
        border: 1px solid rgb(50, 50, 50) !important;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)
