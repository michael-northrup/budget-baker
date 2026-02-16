#!/usr/bin/env python3
"""Test export functionality (CSV and PDF)"""

from modules.csv_parser import parse_csv
from modules.categorizer import categorize_transactions
from modules.export import export_to_csv, export_to_pdf
from modules.visualizations import create_expense_pie_chart, create_category_bar_chart
import polars as pl

print("="*60)
print("Testing Export Functionality")
print("="*60)

# Load and categorize sample data
print("\n1. Loading AFCU sample data...")
with open('test_data/afcu_sample.csv', 'rb') as f:
    file_bytes = f.read()

df, format_name, errors = parse_csv(file_bytes, 'afcu_sample.csv')
print(f"✅ Loaded {len(df)} transactions")

# Categorize
print("\n2. Categorizing transactions...")
cat_df = categorize_transactions(df)
print(f"✅ Categorized {len(cat_df)} transactions")

# Test CSV export
print("\n3. Testing CSV export...")
csv_bytes = export_to_csv(cat_df)
print(f"✅ Generated CSV: {len(csv_bytes)} bytes")

# Save to file for inspection
with open('budget_baker_test.csv', 'wb') as f:
    f.write(csv_bytes)
print(f"✅ Saved to: budget_baker_test.csv")

# Test PDF export
print("\n4. Testing PDF export...")

# Calculate summary stats
income = cat_df.filter(pl.col('type') == 'Income').select(pl.col('amount').sum()).item()
expenses = cat_df.filter(pl.col('type') == 'Expense').select(pl.col('amount').sum()).item()
net = income + expenses

summary_stats = {
    'income': income,
    'expenses': abs(expenses),
    'net': net,
    'total_transactions': len(cat_df)
}

print(f"   Income: ${income:,.2f}")
print(f"   Expenses: ${abs(expenses):,.2f}")
print(f"   Net: ${net:,.2f}")

# Generate charts
print("\n5. Generating charts...")
pie_chart = create_expense_pie_chart(cat_df)
bar_chart = create_category_bar_chart(cat_df)
print("✅ Charts generated")

# Generate PDF
print("\n6. Generating PDF...")
pdf_bytes = export_to_pdf(
    cat_df,
    summary_stats,
    pie_chart=pie_chart,
    bar_chart=bar_chart
)
print(f"✅ Generated PDF: {len(pdf_bytes)} bytes")

# Save to file for inspection
with open('budget_baker_test_report.pdf', 'wb') as f:
    f.write(pdf_bytes)
print(f"✅ Saved to: budget_baker_test_report.pdf")

print("\n" + "="*60)
print("✅ Export test complete!")
print("="*60)
print("\nGenerated files:")
print("  - budget_baker_test.csv")
print("  - budget_baker_test_report.pdf")
print("\nOpen the PDF to verify charts and formatting!")
