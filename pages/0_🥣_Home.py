"""
Budget Baker - Home: Add Your Ingredients
Upload and preview your transaction CSV files
"""

import streamlit as st
import polars as pl
from modules.csv_parser import parse_csv
from modules.progress_indicator import render_progress_indicator, render_privacy_reminder


def main():
    # Sidebar: Progress indicator and privacy
    render_progress_indicator(current_step=1)  # Step 1: Add Ingredients
    render_privacy_reminder()

    # Header
    st.title("🍞 Budget Baker")
    st.markdown("### Privacy-first transaction categorization")
    st.caption("All processing happens locally in your browser • No data saved to disk")

    st.divider()

    # Check if API key exists in secrets
    api_key = None
    if 'ANTHROPIC_API_KEY' in st.secrets:
        api_key = st.secrets['ANTHROPIC_API_KEY']
        st.session_state.api_key = api_key

    # Main content
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
                    st.success(f"Mixed in {uploaded_file.name}: {len(df)} transactions")

                if not all_dfs:
                    st.error("No files were successfully parsed.")
                    return

                # Combine all dataframes
                combined_df = pl.concat(all_dfs)

                # Remove duplicates
                original_count = len(combined_df)
                combined_df = combined_df.unique(subset=['date', 'description', 'amount'])
                dedupe_count = original_count - len(combined_df)

                if dedupe_count > 0:
                    st.info(f"Removed {dedupe_count} duplicate transaction(s)")

                # Sort by date (newest first)
                combined_df = combined_df.sort('date', descending=True)

                st.session_state.parsed_df = combined_df
                # Store format
                unique_formats = set(f for f in all_formats if f)
                if len(unique_formats) == 1:
                    st.session_state.format_name = unique_formats.pop()
                else:
                    st.session_state.format_name = "multiple"

        # Display parsed data
        if st.session_state.parsed_df is not None:
            df = st.session_state.parsed_df

            st.divider()
            st.success(f"🥣 Mixed {len(uploaded_files)} file(s) -> {len(df)} ingredients ready to bake!")

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

            st.divider()

            # Next step - prominent button to navigate
            st.success("**Ingredients ready!** Proceed to the next step to categorize your transactions.")
            if st.button("🔥 Bake Budget  ->", type="primary", use_container_width=True):
                st.switch_page("pages/1_🔥_Bake.py")

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


main()
