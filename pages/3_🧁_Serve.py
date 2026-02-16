"""
Budget Baker - Serve Page
Export your categorized budget as CSV or PDF
"""

import streamlit as st
import polars as pl
from datetime import datetime
from modules.export import export_to_csv, export_to_pdf
from modules.visualizations import create_expense_pie_chart, create_category_bar_chart
from modules.progress_indicator import render_progress_indicator, render_privacy_reminder


def main():
    # Sidebar: Progress indicator and privacy
    render_progress_indicator(current_step=4)  # Step 4: Serve
    render_privacy_reminder()

    # Header
    st.title("🧁 Serve Your Results")
    st.markdown("### Export your perfectly baked budget")
    st.caption("Download as CSV for spreadsheets or PDF for sharing")

    st.divider()

    # Check if data exists
    if 'categorized_df' not in st.session_state or st.session_state.categorized_df is None:
        st.warning("⚠️ No baked budget found! Please categorize your transactions first.")
        st.page_link("pages/1_🔥_Bake.py", label="← Back to Bake", icon="🔥")
        return

    export_df = st.session_state.categorized_df

    # Show export summary
    st.subheader("📊 Export Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Transactions", len(export_df))

    with col2:
        min_date = export_df['date'].min()
        max_date = export_df['date'].max()
        date_range = f"{min_date.strftime('%m/%d')} - {max_date.strftime('%m/%d/%Y')}"
        st.metric("Date Range", date_range)

    with col3:
        income = export_df.filter(pl.col('type') == 'Income').select(pl.col('amount').sum()).item()
        st.metric("Income", f"${income:,.2f}")

    with col4:
        expenses = export_df.filter(pl.col('type') == 'Expense').select(pl.col('amount').sum()).item()
        st.metric("Expenses", f"${abs(expenses):,.2f}")

    st.divider()

    # Export options
    st.subheader("🎁 Choose Your Format")

    col1, col2 = st.columns(2)

    with col1:
        # CSV Export
        st.markdown("### 📋 Recipe Card (CSV)")
        st.markdown("**Best for:**")
        st.markdown("- Importing into Excel or Google Sheets")
        st.markdown("- Further data analysis")
        st.markdown("- All transaction details with categories")

        csv_bytes = export_to_csv(export_df)
        filename_csv = f"budget_baker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        st.download_button(
            label="📋 Download CSV",
            data=csv_bytes,
            file_name=filename_csv,
            mime="text/csv",
            use_container_width=True
        )

        st.caption(f"✅ Contains all {len(export_df)} transactions")

    with col2:
        # PDF Export
        st.markdown("### 🎂 Bakery Box (PDF)")
        st.markdown("**Best for:**")
        st.markdown("- Beautiful visual summary")
        st.markdown("- Sharing with others")
        st.markdown("- Professional reports")

        # Calculate summary stats
        net = income + expenses

        summary_stats = {
            'income': income,
            'expenses': abs(expenses),
            'net': net,
            'total_transactions': len(export_df)
        }

        # Generate PDF button
        if st.button("🎂 Generate PDF", use_container_width=True, type="primary"):
            with st.spinner("🎁 Packaging your budget in a beautiful box..."):
                # Create charts
                pie_chart = create_expense_pie_chart(export_df)
                bar_chart = create_category_bar_chart(export_df)

                # Generate PDF
                pdf_bytes = export_to_pdf(
                    export_df,
                    summary_stats,
                    pie_chart=pie_chart,
                    bar_chart=bar_chart
                )

                filename_pdf = f"budget_baker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=filename_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )

            st.success("✅ PDF ready to download!")
            st.caption(f"📊 Includes summary, charts, and first 50 transactions")

    st.divider()

    # Data preview
    with st.expander("👀 Preview Export Data"):
        st.markdown("**First 10 transactions to be exported:**")

        preview_df = export_df.head(10).select([
            'date', 'description', 'amount', 'category', 'type', 'confidence'
        ]).with_columns([
            pl.col('date').dt.strftime('%m/%d/%Y').alias('date'),
            pl.col('confidence').map_elements(lambda x: f"{x:.0%}", return_dtype=pl.String).alias('confidence')
        ])

        st.dataframe(
            preview_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": "Date",
                "description": "Description",
                "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                "category": "Category",
                "type": "Type",
                "confidence": "Confidence"
            }
        )

    st.divider()

    # Success message and navigation
    st.success("🎉 **Bon Appétit!** Your budget is perfectly baked and ready to serve!")

    st.markdown("### What's Next?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🥣 Add More Data**")
        st.caption("Upload additional CSV files")
        st.page_link("pages/0_🥣_Home.py", label="Go to Home", icon="🥣")

    with col2:
        st.markdown("**🔥 Re-bake**")
        st.caption("Try different options")
        st.page_link("pages/1_🔥_Bake.py", label="Go to Bake", icon="🔥")

    with col3:
        st.markdown("**🍰 Review Again**")
        st.caption("Check your results")
        st.page_link("pages/2_🍰_Results.py", label="Go to Results", icon="🍰")


main()
