import streamlit as st
from streamlit.runtime.scriptrunner import RerunData, RerunException
from streamlit.source_util import get_pages


def navigate_to_page(target_page: str):
    """
    Navigate to the target page

    Args:
        page_name (str): Target page name
    """
    standardize_name = lambda name: name.lower().replace("_", " ")
    target_page = standardize_name(target_page)
    pages = get_pages("main.py")  # Name of entrypoint script

    for page_hash, config in pages.items():
        if standardize_name(config["page_name"]) == target_page:
            raise RerunException(
                RerunData(
                    page_script_hash=page_hash,
                    page_name=target_page,
                )
            )

    page_names = [
        standardize_name(config["page_name"]) for config in pages.values()
    ]

    raise ValueError(f"{target_page} not found. Must be one of {page_names}")


def set_page_style(customize_style: str = ""):
    """
    Set custom CSS styles for the page
    """
    style = """
    <style>
    div[data-testid="stButton"] {
        text-align: right;
    }
    div.row-widget label[data-baseweb="radio"] {
        border: 1px solid rgb(50, 50, 50);
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
    div[data-testid="stChatMessage"],
    div[data-testid="stNotificationContentInfo"] div {
        gap: 1rem;
    }
    div[data-testid="stPageLink"] div {
        align-items: flex-end;
    }
    a[data-testid="stPageLink-NavLink"],
    button[data-testid="baseButton-secondary"] {
        border: 1px solid rgb(50, 50, 50);
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background-color: rgb(19, 23, 32) !important;
        margin: 0;
        min-height: 50px;
    }
    a[data-testid="stPageLink-NavLink"]:hover *,
    button[data-testid="baseButton-secondary"]:hover * {
        color: rgb(255, 75, 75);
    }
    a[data-testid="stPageLink-NavLink"]:hover {
        border-color: rgb(255, 75, 75);
    }
    {customize_style}
    </style>
    """
    style = style.replace("{customize_style}", customize_style)
    st.markdown(style, unsafe_allow_html=True)


def initialize_page(icon: str, title: str, custom_style: str = ""):
    st.set_page_config(page_title=title, page_icon=icon)
    st.title(f"{icon} {title}")

    # TODO: Move definition of `visited_home` here instead of entrypoint script
    st.session_state.setdefault("visited_home", False)
    if not st.session_state.visited_home:
        navigate_to_page("main")

    set_page_style(custom_style)
