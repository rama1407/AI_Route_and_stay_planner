"""Smart packing checklist rendered on its dedicated Streamlit Page 6."""

from __future__ import annotations

import hashlib
import streamlit as st


CATEGORIES = {
    "Travel Essentials": [
        "Government ID / passport",
        "Tickets and booking confirmations",
        "Wallet and payment cards",
        "Phone and charger",
    ],
    "Clothing & Personal Care": [
        "Clothes for the trip",
        "Comfortable footwear",
        "Toiletries and toothbrush",
        "Sunscreen and personal care items",
    ],
    "Health & Safety": [
        "Personal medicines, if needed",
        "Basic first-aid supplies",
        "Emergency contact details",
    ],
    "Trip Essentials": [
        "Hotel booking details",
        "Water bottle",
        "Power bank",
        "Camera or other travel accessories",
    ],
}


def _widget_key(item: str, prefix: str = "travel_check") -> str:
    """Return a stable, Streamlit-safe key for an item label."""
    digest = hashlib.sha1(item.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _reset_checklist(keys: list[str]) -> None:
    """Reset checkbox state in a button callback before the next rerun."""
    for key in keys:
        st.session_state[key] = False


def _remove_custom_item(item: str) -> None:
    custom_items = st.session_state.get("travel_checklist_custom", [])
    if item in custom_items:
        custom_items.remove(item)
    st.session_state.pop(_widget_key(item, "travel_custom_check"), None)


def render_travel_checklist() -> None:
    """Render an interactive packing checklist with custom items and progress."""
    st.markdown(
        """
        <style>
        .checklist-hero {
            background: #102F26;
            color: #F7F0E2;
            padding: 24px 28px;
            border-radius: 16px;
            margin: 22px 0;
        }
        .checklist-hero h2 { color: #F7F0E2; margin: 0 0 8px 0; }
        .checklist-hero p { color: #E2E9E2; margin: 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.write("Check items as you pack. Your progress updates automatically.")

    if "travel_checklist_custom" not in st.session_state:
        st.session_state["travel_checklist_custom"] = []

    custom_items = st.session_state["travel_checklist_custom"]
    base_items = [item for items in CATEGORIES.values() for item in items]
    # Avoid duplicate progress entries if a custom item matches a standard one.
    custom_items[:] = [item for item in custom_items if item not in base_items]
    all_items = base_items + custom_items
    all_keys = [
        _widget_key(item, "travel_check" if item in base_items else "travel_custom_check")
        for item in all_items
    ]

    for key, item in zip(all_keys, all_items):
        if key not in st.session_state:
            st.session_state[key] = False

    for category, items in CATEGORIES.items():
        st.markdown(f"### {category}")
        with st.container(border=True):
            for item in items:
                st.checkbox(item, key=_widget_key(item, "travel_check"))

    st.markdown("### My Custom Items")
    with st.form("travel_checklist_custom_form", clear_on_submit=True):
        new_item = st.text_input("Add your own item", placeholder="e.g. Sunglasses")
        submitted = st.form_submit_button("➕ Add Item")

    if submitted and new_item.strip():
        item = new_item.strip()
        if item not in all_items:
            custom_items.append(item)
            st.rerun()
        else:
            st.info("That item is already on your checklist.")

    if custom_items:
        with st.container(border=True):
            for item in custom_items:
                col_item, col_remove = st.columns([5, 1])
                with col_item:
                    st.checkbox(item, key=_widget_key(item, "travel_custom_check"))
                with col_remove:
                    st.button(
                        "Remove",
                        key=_widget_key(item, "remove_custom"),
                        on_click=_remove_custom_item,
                        args=(item,),
                    )

    checked_count = sum(bool(st.session_state.get(key, False)) for key in all_keys)
    total_count = len(all_items)
    progress = checked_count / total_count if total_count else 0.0

    st.markdown("---")
    st.markdown("### 🎯 Your Packing Progress")
    st.progress(progress)
    st.write(f"**{checked_count} of {total_count} items packed**")

    if total_count and checked_count == total_count:
        st.success("You're all packed! Have a wonderful trip! 🎉")

    st.button(
        "Reset Checklist",
        key="reset_travel_checklist",
        on_click=_reset_checklist,
        args=(all_keys,),
    )
