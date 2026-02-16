"""
Budget Baker - Transaction Categorization Web App
A privacy-first tool for analyzing bank transaction CSVs
"""

import streamlit as st
import polars as pl
import pandas as pd
from datetime import datetime
from modules.csv_parser import parse_csv
from modules.categorizer import categorize_transactions, get_category_summary, CATEGORIES
from modules.visualizations import create_expense_pie_chart, create_category_bar_chart, create_monthly_trend_chart
from modules.export import export_to_csv, export_to_pdf


# Page configuration
st.set_page_config(
    page_title="Budget Baker",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
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

# Custom CSS for baking theme
st.markdown("""
<style>
    /* Hide sidebar completely */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Add symmetric padding to main content */
    .stMainBlockContainer {
        padding-left: 5rem !important;
        padding-right: 5rem !important;
        max-width: 1400px !important;
        margin: 0 auto !important;
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

    /* Primary buttons (Bake button) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #DC2626 0%, #EA580C 100%) !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        padding: 0.75rem 2rem !important;
        border-radius: 15px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 16px rgba(220, 38, 38, 0.4) !important;
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
</style>
""", unsafe_allow_html=True)

def main():
    # Modern header with better spacing
    st.title("🍞 Budget Baker")
    st.markdown("### Privacy-first transaction categorization")
    st.caption("All processing happens locally in your browser • No data saved to disk")

    st.divider()

    # Check if API key exists in secrets
    api_key = None
    if 'ANTHROPIC_API_KEY' in st.secrets:
        api_key = st.secrets['ANTHROPIC_API_KEY']
        st.session_state.api_key = api_key

    # Main content - cleaner section headers
    st.markdown("## 🥣 Add Your Ingredients")

    uploaded_files = st.file_uploader(
        "Drop your transaction files into the mixing bowl",
        type=['csv'],
        accept_multiple_files=True,
        help="Add one or multiple CSV files - we'll mix them together automatically",
        label_visibility="collapsed"
    )

    st.caption("🧑‍🍳 Works with AFCU, Chase, and most bank CSV formats • Mix in multiple files at once")

    if uploaded_files:
        # Create a unique identifier for the uploaded files
        file_names = sorted([f.name for f in uploaded_files])
        files_key = "|".join(file_names)

        # Check if new files uploaded
        if st.session_state.uploaded_file_name != files_key:
            st.session_state.uploaded_file_name = files_key
            st.session_state.parsed_df = None
            st.session_state.format_name = None
            st.session_state.categorized_df = None
            st.session_state.category_edits = {}

            # Parse all CSV files
            all_dfs = []
            all_formats = []

            with st.spinner(f"🥄 Mixing in {len(uploaded_files)} ingredient(s)..."):
                for uploaded_file in uploaded_files:
                    file_bytes = uploaded_file.read()
                    df, format_name, errors = parse_csv(file_bytes, uploaded_file.name)

                    if errors:
                        st.error(f"Error parsing {uploaded_file.name}:")
                        for error in errors:
                            st.error(f"- {error}")
                        continue

                    all_dfs.append(df)
                    all_formats.append(format_name)
                    st.success(f"✅ Mixed in {uploaded_file.name}: {len(df)} transactions")

                if not all_dfs:
                    st.error("No files were successfully parsed.")
                    return

                # Combine all dataframes
                combined_df = pl.concat(all_dfs)

                # Remove duplicates (same date, description, and amount)
                original_count = len(combined_df)
                combined_df = combined_df.unique(subset=['date', 'description', 'amount'])
                dedupe_count = original_count - len(combined_df)

                if dedupe_count > 0:
                    st.info(f"ℹ️ Removed {dedupe_count} duplicate transaction(s)")

                # Sort by date (newest first)
                combined_df = combined_df.sort('date', descending=True)

                st.session_state.parsed_df = combined_df
                # Store format as "multiple" if different formats, otherwise the single format
                unique_formats = set(f for f in all_formats if f)
                if len(unique_formats) == 1:
                    st.session_state.format_name = unique_formats.pop()
                else:
                    st.session_state.format_name = "multiple"

        # Display parsed data
        if st.session_state.parsed_df is not None:
            df = st.session_state.parsed_df

            # Show success message with format detection
            st.divider()
            st.success(f"🥣 Mixed {len(uploaded_files)} file(s) → {len(df)} ingredients ready to bake!")

            if st.session_state.format_name == "multiple":
                st.caption("Multiple CSV formats detected and combined")
            elif st.session_state.format_name:
                st.caption(f"Format: {st.session_state.format_name.upper()}")

            # Show summary stats
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Transactions", len(df))

            with col2:
                min_date = df['date'].min()
                max_date = df['date'].max()
                date_range = f"{min_date.strftime('%m/%d/%Y')} - {max_date.strftime('%m/%d/%Y')}"
                st.metric("Date Range", date_range)

            with col3:
                total_income = df.filter(pl.col('amount') > 0).select(pl.col('amount').sum()).item()
                st.metric("Total Income", f"${total_income:,.2f}")

            with col4:
                total_expenses = df.filter(pl.col('amount') < 0).select(pl.col('amount').sum()).item()
                st.metric("Total Expenses", f"${abs(total_expenses):,.2f}")

            # Show data preview
            st.subheader("Transaction Preview")
            st.markdown("*First 10 transactions:*")

            # Format the dataframe for display (Polars)
            display_df = df.head(10).with_columns([
                pl.col('date').dt.strftime('%m/%d/%Y').alias('date')
            ])

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "amount": st.column_config.NumberColumn(
                        "Amount",
                        format="$%.2f"
                    )
                }
            )

            # Show full data in expander
            with st.expander("View All Transactions"):
                full_display_df = df.with_columns([
                    pl.col('date').dt.strftime('%m/%d/%Y').alias('date')
                ])

                st.dataframe(
                    full_display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "amount": st.column_config.NumberColumn(
                            "Amount",
                            format="$%.2f"
                        )
                    }
                )

            st.divider()

            # Categorization Section
            st.markdown("## 🔥 Bake Your Budget")

            # AI toggle - right before categorization button
            col1, col2 = st.columns([3, 1])

            with col1:
                # Check if API key is available
                has_api_key = st.session_state.get('api_key') is not None

                use_ai = st.checkbox(
                    "⚡ Add secret ingredient (AI enhancement)",
                    value=False,
                    disabled=(not has_api_key),
                    help="AI will categorize unclear transactions (confidence <70%). Requires API key configured in sidebar.",
                    key="use_ai_checkbox"
                )

                if not has_api_key:
                    st.caption("🧂 Configure API key in Settings (sidebar) to add secret ingredient")
                else:
                    st.caption("✨ Secret ingredient ready - adds AI magic to your budget!")

                # Store in session state
                st.session_state.use_ai = use_ai and has_api_key

            # Categorization button
            button_label = "🔥 Start Baking!"
            if st.session_state.get('use_ai', False):
                button_label = "🔥 Bake with Secret Ingredient"

            if st.button(button_label, type="primary", use_container_width=True):
                with st.spinner("🔥 Preheating the oven and baking your budget..."):
                    if st.session_state.use_ai:
                        st.info("✨ Adding a dash of AI magic...")
                    categorized_df = categorize_transactions(
                        df,
                        use_ai=st.session_state.use_ai,
                        api_key=st.session_state.api_key
                    )
                    st.session_state.categorized_df = categorized_df
                    # Reset category edits when recategorizing
                    st.session_state.category_edits = {}

                if st.session_state.use_ai:
                    st.success("🍰 Fresh from the oven! Your budget is perfectly baked with AI magic!")
                else:
                    st.success("🍰 Fresh from the oven! Your budget is ready!")

            # Display categorized results
            if st.session_state.categorized_df is not None:
                cat_df = st.session_state.categorized_df

                # Initialize category edits mapping in session state if not exists
                if 'category_edits' not in st.session_state:
                    st.session_state.category_edits = {}

                st.divider()
                st.markdown("## 🍰 Fresh Out of the Oven")

                # Date range and aggregation controls
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
                        help="Aggregate transactions by month for monthly analysis"
                    )

                # Filter by date range
                cat_df = cat_df.filter(
                    (pl.col('date') >= pl.lit(start_date)) &
                    (pl.col('date') <= pl.lit(end_date))
                )

                # Show transaction count
                st.caption(f"Showing {len(cat_df)} transactions from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")

                st.divider()

                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    income = cat_df.filter(pl.col('type') == 'Income').select(pl.col('amount').sum()).item()
                    st.metric("Income", f"${income:,.2f}", delta=None)

                with col2:
                    expenses = cat_df.filter(pl.col('type') == 'Expense').select(pl.col('amount').sum()).item()
                    st.metric("Expenses", f"${abs(expenses):,.2f}", delta=None)

                with col3:
                    net = income + expenses
                    delta_color = "normal" if net >= 0 else "inverse"
                    st.metric("Net", f"${net:,.2f}", delta=f"${net:,.2f}")

                with col4:
                    uncategorized = len(cat_df.filter(pl.col('category') == 'Uncategorized'))
                    st.metric("Uncategorized", uncategorized)

                st.divider()

                # Visualizations
                st.subheader("📊 Visual Breakdown")

                # Create two columns for charts
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    pie_chart = create_expense_pie_chart(cat_df)
                    st.plotly_chart(pie_chart, use_container_width=True)

                with chart_col2:
                    bar_chart = create_category_bar_chart(cat_df)
                    st.plotly_chart(bar_chart, use_container_width=True)

                # Monthly trend if applicable
                monthly_chart = create_monthly_trend_chart(cat_df)
                if monthly_chart:
                    st.plotly_chart(monthly_chart, use_container_width=True)

                st.divider()

                # Monthly aggregation view
                if group_by_month:
                    st.subheader("📊 Monthly Breakdown")

                    # Add month column
                    monthly_df = cat_df.with_columns([
                        pl.col('date').dt.strftime('%Y-%m').alias('month')
                    ])

                    # Calculate monthly totals by type
                    monthly_summary = monthly_df.group_by(['month', 'type']).agg([
                        pl.col('amount').sum().alias('total'),
                        pl.count().alias('count')
                    ]).sort('month', descending=True)

                    # Pivot to show Income, Expenses, Net per month
                    months = sorted(monthly_summary['month'].unique().to_list(), reverse=True)

                    monthly_data = []
                    for month in months:
                        month_data = monthly_summary.filter(pl.col('month') == month)

                        income = month_data.filter(pl.col('type') == 'Income').select(pl.col('total').sum()).item() or 0
                        expenses = month_data.filter(pl.col('type') == 'Expense').select(pl.col('total').sum()).item() or 0
                        transfers = month_data.filter(pl.col('type') == 'Transfer').select(pl.col('total').sum()).item() or 0

                        monthly_data.append({
                            'Month': month,
                            'Income': f"${income:,.2f}",
                            'Expenses': f"${abs(expenses):,.2f}",
                            'Transfers': f"${abs(transfers):,.2f}",
                            'Net': f"${(income + expenses):,.2f}"
                        })

                    monthly_summary_df = pl.DataFrame(monthly_data)

                    st.dataframe(
                        monthly_summary_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    # Category breakdown by month
                    with st.expander("Category Breakdown by Month"):
                        # Group by month and category
                        monthly_category = monthly_df.filter(pl.col('type') == 'Expense').group_by(['month', 'category']).agg([
                            pl.col('amount').sum().abs().alias('total')
                        ]).sort(['month', 'total'], descending=[True, True])

                        # Convert to pandas for better pivot display
                        monthly_cat_pd = monthly_category.to_pandas()
                        pivot_table = monthly_cat_pd.pivot_table(
                            index='category',
                            columns='month',
                            values='total',
                            fill_value=0,
                            aggfunc='sum'
                        )

                        # Format as currency
                        pivot_display = pivot_table.applymap(lambda x: f"${x:,.2f}" if x > 0 else "-")

                        st.dataframe(
                            pivot_display,
                            use_container_width=True
                        )

                    st.divider()

                # Category breakdown
                st.subheader("Spending by Category")

                summary = get_category_summary(cat_df)

                # Display as formatted table (Polars)
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

                # Date range filter
                st.subheader("Filter & Edit Transactions")

                col1, col2 = st.columns(2)
                with col1:
                    min_date = cat_df['date'].min()
                    max_date = cat_df['date'].max()

                    start_date = st.date_input(
                        "Start Date",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date
                    )

                with col2:
                    end_date = st.date_input(
                        "End Date",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date
                    )

                # Filter by date range
                filtered_df = cat_df.filter(
                    (pl.col('date') >= pl.lit(start_date)) &
                    (pl.col('date') <= pl.lit(end_date))
                )

                st.caption(f"Showing {len(filtered_df)} of {len(cat_df)} transactions")

                st.divider()

                # Quick fix uncategorized section
                uncategorized_count = len(filtered_df.filter(pl.col('category') == 'Uncategorized'))

                if uncategorized_count > 0:
                    st.warning(f"⚠️ You have {uncategorized_count} uncategorized transaction(s)")

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown("**Quick Fix:** Review and categorize unclear transactions below")
                    with col2:
                        show_only_uncat = st.checkbox("Show only uncategorized", value=False, key="show_uncat")

                    st.divider()

                # Filter dataframe if "show only uncategorized" is checked
                if uncategorized_count > 0 and st.session_state.get('show_uncat', False):
                    display_filtered_df = filtered_df.filter(pl.col('category') == 'Uncategorized')
                    st.info(f"Showing {len(display_filtered_df)} uncategorized transactions")
                else:
                    display_filtered_df = filtered_df

                # Editable transaction table
                st.subheader("Edit Categories")

                # Get all valid categories for dropdown
                all_categories = sorted(list(CATEGORIES.keys()) + ['Income', 'Transfer', 'Uncategorized'])

                # Apply any previous edits from session state to the current display
                if st.session_state.category_edits:
                    # Create a mapping and apply it to the current display
                    display_with_edits = display_filtered_df.with_columns([
                        pl.col('description').map_elements(
                            lambda desc: st.session_state.category_edits.get(desc, display_filtered_df.filter(pl.col('description') == desc)['category'][0] if len(display_filtered_df.filter(pl.col('description') == desc)) > 0 else 'Uncategorized'),
                            return_dtype=pl.String
                        ).alias('category')
                    ])
                else:
                    display_with_edits = display_filtered_df

                # Convert to pandas for st.data_editor
                edit_df = display_with_edits.select([
                    'date', 'description', 'amount', 'category', 'confidence', 'type'
                ]).to_pandas()

                # Keep numeric amount for sorting, add formatted version for display
                edit_df['amount_numeric'] = edit_df['amount']  # Keep original for sorting
                edit_df['date'] = pd.to_datetime(edit_df['date']).dt.strftime('%m/%d/%Y')
                edit_df['confidence'] = edit_df['confidence'].apply(lambda x: f"{x:.0%}")

                # Create editable dataframe with proper numeric sorting
                edited_df = st.data_editor(
                    edit_df,
                    column_config={
                        "date": st.column_config.TextColumn("Date", disabled=True, width="small"),
                        "description": st.column_config.TextColumn("Description", disabled=True, width="large"),
                        "amount_numeric": st.column_config.NumberColumn(
                            "Amount",
                            disabled=True,
                            width="small",
                            format="$%.2f"
                        ),
                        "category": st.column_config.SelectboxColumn(
                            "Category",
                            help="Click to edit category",
                            options=all_categories,
                            required=True,
                            width="medium"
                        ),
                        "confidence": st.column_config.TextColumn("Confidence", disabled=True, width="small"),
                        "type": st.column_config.TextColumn("Type", disabled=True, width="small"),
                        "amount": None  # Hide the original amount column
                    },
                    hide_index=True,
                    use_container_width=True,
                    num_rows="dynamic" if uncategorized_count > 0 and st.session_state.get('show_uncat', False) else "fixed",
                    key="transaction_editor"
                )

                # Show helpful tip for uncategorized items
                if uncategorized_count > 0:
                    st.caption("💡 Tip: Check 'Show only uncategorized' above to focus on unclear items")

                # Check if any edits were made
                if not edit_df.equals(edited_df):
                    st.info("💡 Categories have been edited. Changes are shown below but not saved until you export.")

                    # Store edits in session state as description -> category mapping
                    for idx, row in edited_df.iterrows():
                        desc = row['description']
                        new_cat = row['category']
                        # Only store if different from original
                        original_cat = edit_df.loc[edit_df['description'] == desc, 'category'].values[0]
                        if new_cat != original_cat:
                            st.session_state.category_edits[desc] = new_cat

                    # Apply all edits (from session state) to the main categorized dataframe
                    updated_df = cat_df.with_columns([
                        pl.col('description').map_elements(
                            lambda desc: st.session_state.category_edits.get(desc, cat_df.filter(pl.col('description') == desc)['category'][0] if len(cat_df.filter(pl.col('description') == desc)) > 0 else 'Uncategorized'),
                            return_dtype=pl.String
                        ).alias('category')
                    ])

                    # Recalculate type based on new categories
                    updated_df = updated_df.with_columns([
                        pl.when(pl.col('amount') > 0)
                          .then(pl.lit('Income'))
                          .when(pl.col('category') == 'Transfers')
                          .then(pl.lit('Transfer'))
                          .otherwise(pl.lit('Expense'))
                          .alias('type')
                    ])

                    # Store updated dataframe in session state
                    st.session_state.categorized_df = updated_df

                    # Update the cat_df and filtered_df variables so all displays use the updated data
                    cat_df = updated_df
                    # Recreate filtered_df with the updated data and current date filter
                    filtered_df = cat_df.filter(
                        (pl.col('date') >= pl.lit(start_date)) &
                        (pl.col('date') <= pl.lit(end_date))
                    )
                    # Also update display_filtered_df if showing only uncategorized
                    if uncategorized_count > 0 and st.session_state.get('show_uncat', False):
                        display_filtered_df = filtered_df.filter(pl.col('category') == 'Uncategorized')
                    else:
                        display_filtered_df = filtered_df

                    # Recalculate summary
                    st.subheader("Updated Summary")
                    updated_summary = get_category_summary(updated_df)

                    summary_display = updated_summary.with_columns([
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

                # Detailed transaction list by category
                st.subheader("Transactions by Category")

                # Use filtered or updated dataframe
                display_cat_df = st.session_state.categorized_df if not edit_df.equals(edited_df) else filtered_df

                # Show transactions grouped by category
                for category in sorted(display_cat_df['category'].unique().to_list()):
                    category_data = display_cat_df.filter(pl.col('category') == category)
                    count = len(category_data)
                    total = category_data.select(pl.col('amount').sum()).item()

                    with st.expander(f"**{category}** ({count} transactions, ${abs(total):,.2f})"):
                        display_cat = category_data.select(['date', 'description', 'amount', 'confidence']).with_columns([
                            pl.col('date').dt.strftime('%m/%d/%Y').alias('date'),
                            pl.col('confidence').map_elements(lambda x: f"{x:.0%}", return_dtype=pl.String).alias('confidence')
                        ])

                        st.dataframe(
                            display_cat,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "date": "Date",
                                "description": "Description",
                                "amount": st.column_config.NumberColumn(
                                    "Amount",
                                    format="$%.2f"
                                ),
                                "confidence": "Confidence"
                            }
                        )

                st.divider()

                # Export Section
                st.markdown("## 🧁 Serve Your Results")

                # Get the dataframe to export (use updated if edited, otherwise original)
                export_df = st.session_state.categorized_df

                col1, col2 = st.columns(2)

                with col1:
                    # CSV Export
                    st.subheader("📋 Recipe Card (CSV)")
                    st.markdown("Take home all the ingredients and measurements")

                    csv_bytes = export_to_csv(export_df)

                    filename_csv = f"budget_baker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

                    st.download_button(
                        label="📋 Get Recipe Card",
                        data=csv_bytes,
                        file_name=filename_csv,
                        mime="text/csv",
                        use_container_width=True
                    )

                    st.caption(f"Contains all {len(export_df)} ingredients with categories")

                with col2:
                    # PDF Export
                    st.subheader("🎂 Bakery Box (PDF)")
                    st.markdown("Beautiful presentation of your budget masterpiece")

                    # Prepare summary stats
                    income = export_df.filter(pl.col('type') == 'Income').select(pl.col('amount').sum()).item()
                    expenses = export_df.filter(pl.col('type') == 'Expense').select(pl.col('amount').sum()).item()
                    net = income + expenses

                    summary_stats = {
                        'income': income,
                        'expenses': abs(expenses),
                        'net': net,
                        'total_transactions': len(export_df)
                    }

                    # Generate PDF with charts
                    with st.spinner("🎁 Packaging your budget in a beautiful box..."):
                        # Get the current charts
                        current_pie = create_expense_pie_chart(export_df)
                        current_bar = create_category_bar_chart(export_df)

                        pdf_bytes = export_to_pdf(
                            export_df,
                            summary_stats,
                            pie_chart=current_pie,
                            bar_chart=current_bar
                        )

                    filename_pdf = f"budget_baker_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                    st.download_button(
                        label="🎂 Get Bakery Box",
                        data=pdf_bytes,
                        file_name=filename_pdf,
                        mime="application/pdf",
                        use_container_width=True
                    )

                    st.caption("Beautifully packaged with summary, charts, and details")

                st.divider()
                st.success("🎉 Bon Appétit! Your budget is perfectly baked and ready to enjoy!")

    else:
        # Show helpful message when no file uploaded
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🧁 What's in the Recipe")
            st.markdown("""
            - **36+ Categories** - Every ingredient sorted
            - **Multi-File Mix** - Combine multiple CSVs
            - **AI Secret Ingredient** - Smart categorization
            - **Date Sifting** - Filter by time period
            - **Monthly Batches** - Track trends
            - **Take Home** - PDF & CSV export
            """)

        with col2:
            st.markdown("### 🏦 Ingredient Sources")
            st.markdown("""
            - **AFCU** (American First Credit Union)
            - **Chase** Bank
            - **Most banks** (auto-detected)

            **Handles:**
            - Different date formats
            - Debit/credit columns
            - Bank annotations
            - Multiple encodings
            - Duplicate removal
            """)

        # Expandable details
        with st.expander("📋 Full Format Details"):
            st.markdown("""
            **Multi-File Upload:**
            - Upload multiple CSV files at once (different months, accounts, etc.)
            - Files are automatically combined and duplicates removed
            - Mix different bank formats in a single upload

            **Supported Formats:**

            **AFCU (American First Credit Union)**
            - Separate Debit/Credit columns
            - Date, Description, No. (check number)

            **Chase**
            - Single Amount column
            - Transaction Date, Post Date, Description, Category

            **Generic/Other Banks**
            - Automatic column detection
            - Manual mapping available if needed

            **The app handles:**
            - Different date formats (M/D/YYYY, MM/DD/YYYY)
            - Currency symbols and thousand separators
            - Bank annotations (R), (S), (P)
            - Preamble rows before headers
            - Different encodings (UTF-8, Windows-1252)
            - Duplicate detection (same date, description, amount)
            """)


if __name__ == "__main__":
    main()
