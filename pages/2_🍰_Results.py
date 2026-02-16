"""
Budget Baker - Results Page
View, filter, and edit your categorized transactions
"""

import streamlit as st
import polars as pl
import pandas as pd
from modules.categorizer import get_category_summary, CATEGORIES
from modules.visualizations import create_expense_pie_chart, create_category_bar_chart, create_monthly_trend_chart
from modules.progress_indicator import render_progress_indicator, render_privacy_reminder


def _apply_results_edits():
    """Apply pending category edits from the Results editor to categorized_df."""
    pending = st.session_state.get('results_pending_edits', {})
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
    # Merge into persistent edit history
    if 'category_edits' not in st.session_state:
        st.session_state.category_edits = {}
    st.session_state.category_edits.update(pending)
    # Clear pending edits and snapshot
    st.session_state.results_pending_edits = {}
    st.session_state.pop('results_edit_snapshot', None)


def main():
    # Sidebar: Progress indicator and privacy
    render_progress_indicator(current_step=3)  # Step 3: Review Results
    render_privacy_reminder()

    # Header
    st.title("🍰 Fresh Out of the Oven")
    st.markdown("### Your categorized budget is ready to review")
    st.caption("Filter, analyze, and refine your categories")

    st.divider()

    # Check if data exists
    if 'categorized_df' not in st.session_state or st.session_state.categorized_df is None:
        st.warning("⚠️ No baked budget found! Please categorize your transactions first.")
        st.page_link("pages/1_🔥_Bake.py", label="← Back to Bake", icon="🔥")
        return

    cat_df = st.session_state.categorized_df

    # Date range filtering
    st.subheader("📅 Filter & Group Options")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        min_date = cat_df['date'].min()
        max_date = cat_df['date'].max()

        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="results_start_date"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="results_end_date"
        )

    with col3:
        group_by_month = st.checkbox(
            "Group by Month",
            value=False,
            help="Aggregate transactions by month"
        )

    # Apply date filter
    filtered_df = cat_df.filter(
        (pl.col('date') >= pl.lit(start_date)) &
        (pl.col('date') <= pl.lit(end_date))
    )

    st.caption(f"Showing {len(filtered_df)} transactions from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")

    st.divider()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        income = filtered_df.filter(pl.col('type') == 'Income').select(pl.col('amount').sum()).item()
        st.metric("Income", f"${income:,.2f}")

    with col2:
        expenses = filtered_df.filter(pl.col('type') == 'Expense').select(pl.col('amount').sum()).item()
        st.metric("Expenses", f"${abs(expenses):,.2f}")

    with col3:
        net = income + expenses
        st.metric("Net", f"${net:,.2f}", delta=f"${net:,.2f}")

    with col4:
        uncategorized = len(filtered_df.filter(pl.col('category') == 'Uncategorized'))
        st.metric("Uncategorized", uncategorized)

    st.divider()

    # Visualizations
    st.subheader("📊 Visual Breakdown")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        pie_chart = create_expense_pie_chart(filtered_df)
        st.plotly_chart(pie_chart, use_container_width=True)

    with chart_col2:
        bar_chart = create_category_bar_chart(filtered_df)
        st.plotly_chart(bar_chart, use_container_width=True)

    # Monthly trend
    monthly_chart = create_monthly_trend_chart(filtered_df)
    if monthly_chart:
        st.plotly_chart(monthly_chart, use_container_width=True)

    st.divider()

    # Monthly aggregation view
    if group_by_month:
        st.subheader("📊 Monthly Breakdown")

        monthly_df = filtered_df.with_columns([
            pl.col('date').dt.strftime('%Y-%m').alias('month')
        ])

        monthly_summary = monthly_df.group_by(['month', 'type']).agg([
            pl.col('amount').sum().alias('total'),
            pl.count().alias('count')
        ]).sort('month', descending=True)

        months = sorted(monthly_summary['month'].unique().to_list(), reverse=True)

        monthly_data = []
        for month in months:
            month_data = monthly_summary.filter(pl.col('month') == month)

            income_amt = month_data.filter(pl.col('type') == 'Income').select(pl.col('total').sum()).item() or 0
            expenses_amt = month_data.filter(pl.col('type') == 'Expense').select(pl.col('total').sum()).item() or 0
            transfers_amt = month_data.filter(pl.col('type') == 'Transfer').select(pl.col('total').sum()).item() or 0

            monthly_data.append({
                'Month': month,
                'Income': f"${income_amt:,.2f}",
                'Expenses': f"${abs(expenses_amt):,.2f}",
                'Transfers': f"${abs(transfers_amt):,.2f}",
                'Net': f"${(income_amt + expenses_amt):,.2f}"
            })

        monthly_summary_df = pl.DataFrame(monthly_data)

        st.dataframe(
            monthly_summary_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

    # Category summary
    st.subheader("💰 Spending by Category")

    summary = get_category_summary(filtered_df)

    summary_display = summary.with_columns([
        pl.col('total').map_elements(lambda x: f"${x:,.2f}", return_dtype=pl.String).alias('total'),
        pl.col('average').map_elements(lambda x: f"${x:,.2f}", return_dtype=pl.String).alias('average')
    ])

    st.dataframe(
        summary_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "category": "Category",
            "count": "# Transactions",
            "total": "Total Spent",
            "average": "Avg per Transaction"
        }
    )

    st.divider()

    # Edit Categories Section
    st.subheader("✏️ Edit Categories")

    if uncategorized > 0:
        st.warning(f"⚠️ You have {uncategorized} uncategorized transaction(s)")
        show_only_uncat = st.checkbox("Show only uncategorized", value=False, key="show_uncat")
    else:
        show_only_uncat = False

    # Filter for editing
    if show_only_uncat and uncategorized > 0:
        display_df = filtered_df.filter(pl.col('category') == 'Uncategorized')
        st.info(f"Showing {len(display_df)} uncategorized transactions")
    else:
        display_df = filtered_df

    # Get all categories for dropdown
    all_categories = sorted(list(CATEGORIES.keys()) + ['Income', 'Transfers', 'Uncategorized'])

    # Initialize pending edits
    if 'results_pending_edits' not in st.session_state:
        st.session_state.results_pending_edits = {}

    # Build a stable snapshot of the data for the editor.
    # We use a snapshot key that includes the filter settings so that
    # changing the date range or uncategorized filter invalidates it.
    snapshot_filter_key = f"{start_date}|{end_date}|{show_only_uncat}"
    prev_filter_key = st.session_state.get('results_snapshot_filter_key', None)

    if ('results_edit_snapshot' not in st.session_state
            or prev_filter_key != snapshot_filter_key):
        snapshot = display_df.select([
            'date', 'description', 'amount', 'category', 'confidence', 'type'
        ]).to_pandas()
        snapshot['date'] = pd.to_datetime(snapshot['date']).dt.strftime('%m/%d/%Y')
        snapshot['confidence'] = snapshot['confidence'].apply(lambda x: f"{x:.0%}")
        st.session_state.results_edit_snapshot = snapshot
        st.session_state.results_snapshot_filter_key = snapshot_filter_key
        # Clear pending edits when filter changes
        st.session_state.results_pending_edits = {}

    edit_df = st.session_state.results_edit_snapshot.copy()

    # Pre-apply pending edits into the display so user sees their changes
    pending = st.session_state.get('results_pending_edits', {})
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
                help="Click to edit",
                options=all_categories,
                required=True,
                width="medium"
            ),
            "confidence": st.column_config.TextColumn("Confidence", disabled=True, width="small"),
            "type": st.column_config.TextColumn("Type", disabled=True, width="small")
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="transaction_editor"
    )

    if uncategorized > 0:
        st.caption("💡 Tip: Check 'Show only uncategorized' to focus on unclear items")

    # Detect edits by comparing each row using integer index against the
    # original snapshot (not the pre-applied pending version).
    original_snapshot = st.session_state.results_edit_snapshot
    new_pending = dict(pending)

    for idx in edited_df.index:
        new_cat = edited_df.at[idx, 'category']
        original_cat = original_snapshot.at[idx, 'category']
        desc = original_snapshot.at[idx, 'description']

        if new_cat != original_cat:
            new_pending[desc] = new_cat
        else:
            # If user reverted back to original, remove from pending
            new_pending.pop(desc, None)

    st.session_state.results_pending_edits = new_pending

    # Show apply button if there are pending edits
    if new_pending:
        n_edits = len(new_pending)
        st.info(f"💡 You have {n_edits} pending category change(s). Click below to apply.")
        if st.button(
            f"✅ Apply {n_edits} Change(s)",
            type="primary",
            use_container_width=True,
            key="results_apply_edits"
        ):
            _apply_results_edits()
            st.rerun()

    st.divider()

    # Navigation to Export
    st.success("✅ Budget reviewed! Ready to export your results?")
    st.page_link("pages/3_🧁_Serve.py", label="Serve Results (Export) →", icon="🧁")


main()
