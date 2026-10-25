
import streamlit as st


def render_travel_checklist():
    """Render the Smart Travel Checklist page."""

    st.markdown("""
    <style>
    .checklist-hero {
        background: #102F26;
        color: #F7F0E2;
        padding: 28px;
        border-radius: 16px;
        margin-bottom: 22px;
    }
    .checklist-hero h1 {
        color: #F7F0E2;
        margin-bottom: 8px;
    }
    .checklist-hero p {
        color: #E2E9E2;
        margin-bottom: 0;
    }
    </style>
    <div class="checklist-hero">
        <h1>🧳 Smart Travel Checklist</h1>
        <p>Pack smarter. Travel happier. Get ready for your journey.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("Check items as you pack. Your progress updates automatically.")

    categories = {
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

    # Keep checked items in Streamlit session state.
    if "travel_checklist_checked" not in st.session_state:
        st.session_state["travel_checklist_checked"] = []

    if "travel_checklist_custom" not in st.session_state:
        st.session_state["travel_checklist_custom"] = []

    checked = st.session_state["travel_checklist_checked"]
    all_items = []

    for category, items in categories.items():
        st.markdown(f"### {category}")

        with st.container(border=True):
            for item in items:
                key = f"travel_check_{item}"
                all_items.append(item)

                st.checkbox(
                    item,
                    value=item in checked,
                    key=key,
                    on_change=_update_checked,
                    args=(item, key),
                )

    st.markdown("### My Custom Items")

    with st.form("travel_checklist_custom_form"):
        new_item = st.text_input(
            "Add your own item",
            placeholder="e.g. Sunglasses"
        )
        submitted = st.form_submit_button("➕ Add Item")

        if submitted and new_item.strip():
            item = new_item.strip()
            if item not in st.session_state["travel_checklist_custom"]:
                st.session_state["travel_checklist_custom"].append(item)
            st.rerun()

    if st.session_state["travel_checklist_custom"]:
        with st.container(border=True):
            for item in st.session_state["travel_checklist_custom"]:
                key = f"travel_custom_check_{item}"
                all_items.append(item)

                st.checkbox(
                    item,
                    value=item in checked,
                    key=key,
                    on_change=_update_checked,
                    args=(item, key),
                )

                if st.button(
                    f"Remove {item}",
                    key=f"remove_custom_{item}"
                ):
                    st.session_state["travel_checklist_custom"].remove(item)
                    st.session_state["travel_checklist_checked"] = [
                        x for x in checked if x != item
                    ]
                    st.session_state.pop(key, None)
                    st.rerun()

    checked_count = sum(item in checked for item in all_items)
    total_count = len(all_items)
    progress = checked_count / total_count if total_count else 0

    st.markdown("---")
    st.markdown("### 🎯 Your Packing Progress")
    st.progress(progress)
    st.write(f"**{checked_count} of {total_count} items packed**")

    if total_count and checked_count == total_count:
        st.success("You're all packed! Have a wonderful trip! 🎉")

    if st.button("Reset Checklist", key="reset_travel_checklist"):
        st.session_state["travel_checklist_checked"] = []
        for item in all_items:
            st.session_state.pop(f"travel_check_{item}", None)
            st.session_state.pop(f"travel_custom_check_{item}", None)
        st.rerun()


def _update_checked(item, widget_key):
    """Synchronize checkbox changes with the saved checklist."""
    checked_items = st.session_state["travel_checklist_checked"]
    is_checked = st.session_state.get(widget_key, False)

    if is_checked and item not in checked_items:
        checked_items.append(item)
    elif not is_checked and item in checked_items:
        checked_items.remove(item)
