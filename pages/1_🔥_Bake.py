"""
Budget Baker - Bake Page
Categorize your transactions with keyword rules and optional AI enhancement
"""

import streamlit as st
import polars as pl
import pandas as pd
from modules.categorizer import categorize_transactions, CATEGORIES
from modules.progress_indicator import render_progress_indicator, render_privacy_reminder


def _apply_pending_edits():
    """Apply pending category edits to categorized_df and clear pending state."""
    pending = st.session_state.get('bake_pending_edits', {})
    if not pending or 'categorized_df' not in st.session_state:
        return

    updated_df = st.session_state.categorized_df.clone()

    for description, new_category in pending.items():
        updated_df = updated_df.with_columns(
            pl.when(pl.col('description') == description)
              .then(pl.lit(new_category))
              .otherwise(pl.col('category'))
              .alias('category')
        )

    # Update type based on new category
    updated_df = updated_df.with_columns([
        pl.when(pl.col('amount') > 0)
          .then(pl.lit('Income'))
          .when(pl.col('category') == 'Transfers')
          .then(pl.lit('Transfer'))
          .otherwise(pl.lit('Expense'))
          .alias('type')
    ])

    st.session_state.categorized_df = updated_df
    # Merge pending edits into the persistent edit history
    if 'category_edits' not in st.session_state:
        st.session_state.category_edits = {}
    st.session_state.category_edits.update(pending)
    # Clear pending edits and snapshot so they are rebuilt on next run
    st.session_state.bake_pending_edits = {}
    st.session_state.pop('bake_uncat_snapshot', None)


def main():
    # Sidebar: Progress indicator and privacy
    render_progress_indicator(current_step=2)  # Step 2: Bake Budget
    render_privacy_reminder()

    # Header
    st.title("🔥 Bake Your Budget")
    st.markdown("### Transform your transactions into categorized insights")
    st.caption("Keyword-based categorization with optional AI enhancement")

    st.divider()

    # Check if data exists
    if 'parsed_df' not in st.session_state or st.session_state.parsed_df is None:
        st.warning("⚠️ No ingredients found! Please upload your CSV files on the Home page first.")
        st.page_link("pages/0_🥣_Home.py", label="← Back to Add Ingredients", icon="🥣")
        return

    df = st.session_state.parsed_df

    # Show data summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Transactions to Bake", len(df))

    with col2:
        min_date = df['date'].min()
        max_date = df['date'].max()
        date_range = f"{min_date.strftime('%m/%d')} - {max_date.strftime('%m/%d/%Y')}"
        st.metric("Date Range", date_range)

    with col3:
        total_amount = df.select(pl.col('amount').sum()).item()
        st.metric("Net Amount", f"${total_amount:,.2f}")

    st.divider()

    # AI Enhancement Option
    st.markdown("### 🎨 Baking Options")

    # Check if API key is available
    has_api_key = st.session_state.get('api_key') is not None

    use_ai = st.checkbox(
        "⚡ Add secret ingredient (AI enhancement for unclear items)",
        value=st.session_state.get('use_ai', False),
        disabled=(not has_api_key),
        help="AI will categorize transactions with low confidence (<70%). Only sends merchant names, not amounts.",
        key="use_ai_checkbox"
    )

    if not has_api_key:
        st.info("💡 **Want AI magic?** Configure your Anthropic API key in `.streamlit/secrets.toml` to enable AI enhancement.")
        with st.expander("📖 How to add API key"):
            st.code("""
# Create/edit .streamlit/secrets.toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
            """, language="toml")
    else:
        if use_ai:
            st.success("✨ Secret ingredient ready! AI will help categorize unclear transactions.")
        else:
            st.info("🧂 Using keyword-based categorization only (fast & private)")

    # Store in session state
    st.session_state.use_ai = use_ai and has_api_key

    st.divider()

    # Categorization button
    button_label = "🔥 Start Baking!"
    if st.session_state.get('use_ai', False):
        button_label = "🔥 Bake with Secret Ingredient (AI)"

    if st.button(button_label, type="primary", use_container_width=True):
        with st.spinner("🥄 Preheating the oven and baking your budget..."):
            if st.session_state.use_ai:
                st.info("✨ Whisking in a dash of AI magic...")

            categorized_df = categorize_transactions(
                df,
                use_ai=st.session_state.use_ai,
                api_key=st.session_state.get('api_key')
            )
            st.session_state.categorized_df = categorized_df
            # Reset all edit tracking when recategorizing
            st.session_state.category_edits = {}
            st.session_state.bake_pending_edits = {}
            st.session_state.pop('bake_uncat_snapshot', None)

        # Success message
        if st.session_state.use_ai:
            st.success("🍰 Bon Appétit! Your budget is perfectly baked with AI magic!")
        else:
            st.success("🍰 Bon Appétit! Your budget is ready to serve!")

        st.balloons()

    # Show categorized results (persists across reruns, outside the button block)
    if 'categorized_df' in st.session_state and st.session_state.categorized_df is not None:
        categorized_df = st.session_state.categorized_df

        # Show quick summary
        expenses = categorized_df.filter(pl.col('type') == 'Expense')
        num_categories = expenses.select(pl.col('category').n_unique()).item() if len(expenses) > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Transactions Categorized", len(categorized_df))
        with col2:
            st.metric("Expense Categories", num_categories)
        with col3:
            avg_confidence = categorized_df.select(pl.col('confidence').mean()).item()
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")

        st.divider()

        # Check for uncategorized items
        uncategorized_count = len(categorized_df.filter(pl.col('category') == 'Uncategorized'))

        if uncategorized_count > 0:
            # Show uncategorized items for manual categorization
            st.warning(f"⚠️ **{uncategorized_count} uncategorized transaction(s) need your attention**")
            st.markdown("Please categorize these items below, then click **Apply Changes**:")

            # Initialize pending edits if needed
            if 'bake_pending_edits' not in st.session_state:
                st.session_state.bake_pending_edits = {}

            # Get all valid categories for dropdown
            all_categories = sorted(list(CATEGORIES.keys()) + ['Income', 'Transfers', 'Uncategorized'])

            # Use a stable snapshot of uncategorized rows so the table doesn't
            # shift between reruns while the user is editing.  The snapshot is
            # cleared when edits are applied (see _apply_pending_edits).
            if 'bake_uncat_snapshot' not in st.session_state:
                uncat_pl = categorized_df.filter(pl.col('category') == 'Uncategorized')
                snapshot = uncat_pl.select([
                    'date', 'description', 'amount', 'category', 'confidence'
                ]).to_pandas()
                snapshot['date'] = pd.to_datetime(snapshot['date']).dt.strftime('%m/%d/%Y')
                snapshot['confidence'] = snapshot['confidence'].apply(lambda x: f"{x:.0%}")
                st.session_state.bake_uncat_snapshot = snapshot

            edit_df = st.session_state.bake_uncat_snapshot.copy()

            # Pre-apply any pending (not yet committed) edits so the user
            # sees their previous selections reflected in the editor.
            pending = st.session_state.get('bake_pending_edits', {})
            if pending:
                for idx in edit_df.index:
                    desc = edit_df.at[idx, 'description']
                    if desc in pending:
                        edit_df.at[idx, 'category'] = pending[desc]

            # Editable dataframe
            edited_df = st.data_editor(
                edit_df,
                column_config={
                    "date": st.column_config.TextColumn("Date", disabled=True, width="small"),
                    "description": st.column_config.TextColumn("Description", disabled=True, width="large"),
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        disabled=True,
                        width="small",
                        format="$%.2f"
                    ),
                    "category": st.column_config.SelectboxColumn(
                        "Category",
                        help="Select category",
                        options=all_categories,
                        required=True,
                        width="medium"
                    ),
                    "confidence": st.column_config.TextColumn("Confidence", disabled=True, width="small")
                },
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key="bake_transaction_editor"
            )

            # Detect edits by comparing each row using the integer index.
            # This avoids the old description-based matching that broke when
            # multiple transactions shared the same description text.
            original_snapshot = st.session_state.bake_uncat_snapshot
            has_changes = False
            new_pending = dict(pending)  # start from current pending

            for idx in edited_df.index:
                new_cat = edited_df.at[idx, 'category']
                original_cat = original_snapshot.at[idx, 'category']
                desc = original_snapshot.at[idx, 'description']

                if new_cat != original_cat:
                    new_pending[desc] = new_cat
                    has_changes = True
                else:
                    # If user reverted a pending edit back to original, remove it
                    new_pending.pop(desc, None)

            st.session_state.bake_pending_edits = new_pending

            # Show apply button if there are pending edits
            if new_pending:
                n_edits = len(new_pending)
                st.info(f"You have {n_edits} pending category change(s).")
                if st.button(
                    f"✅ Apply {n_edits} Change(s)",
                    type="primary",
                    use_container_width=True,
                    key="bake_apply_edits"
                ):
                    _apply_pending_edits()
                    st.rerun()

            st.divider()

        # Show navigation to results
        if uncategorized_count == 0:
            st.success("✅ **All items categorized!** Ready to view your budget breakdown?")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.page_link("pages/2_🍰_Results.py", label="🍰 View Results →", icon="🍰")
        else:
            st.info("💡 Categorize the items above to proceed to results, or skip to view partial results.")
            col1, col2 = st.columns(2)
            with col1:
                st.page_link("pages/2_🍰_Results.py", label="Skip to Results →", icon="🍰")
            with col2:
                if st.button("🔄 Re-categorize All", use_container_width=True):
                    st.session_state.categorized_df = None
                    st.session_state.category_edits = {}
                    st.session_state.bake_pending_edits = {}
                    st.session_state.pop('bake_uncat_snapshot', None)
                    st.rerun()


main()
