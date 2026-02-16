"""
Progress Indicator Module
Visual breadcrumb navigation showing workflow steps with clickable links
"""

import streamlit as st


def render_progress_indicator(current_step: int):
    """
    Render a visual progress indicator in the sidebar with clickable navigation.

    Uses st.page_link() for completed and future steps so users can navigate
    between pages. The current step is highlighted but not clickable.

    Args:
        current_step: Current step number (1-4)
            1 = Add Ingredients (Home)
            2 = Bake Budget (Categorize)
            3 = Review Results (Results)
            4 = Serve (Export)
    """
    st.sidebar.markdown("### 📍 Your Recipe Progress")

    steps = [
        ("🥣", "Add Ingredients", 1, "pages/0_🥣_Home.py"),
        ("🔥", "Bake Budget", 2, "pages/1_🔥_Bake.py"),
        ("🍰", "Review Results", 3, "pages/2_🍰_Results.py"),
        ("🧁", "Serve", 4, "pages/3_🧁_Serve.py")
    ]

    for icon, label, step, page_path in steps:
        if step < current_step:
            # Completed step - clickable link back
            st.sidebar.page_link(page_path, label=f"{icon} {label}  ✓", icon=None)
        elif step == current_step:
            # Current step - highlighted, not a link
            st.sidebar.markdown(
                f"**{icon} {label}** &larr; You are here",
                help="Current step"
            )
        else:
            # Future step - clickable but visually muted
            st.sidebar.page_link(page_path, label=f"{icon} {label}", icon=None)

    st.sidebar.markdown("---")


def render_privacy_reminder():
    """
    Render privacy reminder at bottom of sidebar
    """
    st.sidebar.markdown("---")
    st.sidebar.info("🔒 **Privacy First**\n\nAll processing happens locally in your browser. No data saved to disk.")
