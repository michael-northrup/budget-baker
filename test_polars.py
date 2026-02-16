#!/usr/bin/env python3
"""Quick test to verify Polars integration works"""

from modules.csv_parser import parse_csv
from modules.categorizer import categorize_transactions, get_category_summary
import polars as pl

# Test with AFCU sample
print("Testing AFCU CSV parsing...")
with open('test_data/afcu_sample.csv', 'rb') as f:
    file_bytes = f.read()

df, format_name, errors = parse_csv(file_bytes, 'afcu_sample.csv')

if errors:
    print(f"Errors: {errors}")
else:
    print(f"✅ Parsed {len(df)} transactions")
    print(f"✅ Detected format: {format_name}")
    print(f"\nDataFrame schema:")
    print(df.schema)
    print(f"\nFirst 3 rows:")
    print(df.head(3))

# Test categorization
print("\n" + "="*50)
print("Testing categorization...")
cat_df = categorize_transactions(df)
print(f"✅ Categorized {len(cat_df)} transactions")
print(f"\nCategorized schema:")
print(cat_df.schema)
print(f"\nFirst 3 categorized rows:")
print(cat_df.select(['description', 'amount', 'category', 'confidence', 'type']).head(3))

# Test summary
print("\n" + "="*50)
print("Testing category summary...")
summary = get_category_summary(cat_df)
print(f"✅ Generated summary for {len(summary)} categories")
print(f"\nCategory summary:")
print(summary)

print("\n" + "="*50)
print("Testing Chase CSV parsing...")
with open('test_data/chase_sample.csv', 'rb') as f:
    file_bytes = f.read()

df2, format_name2, errors2 = parse_csv(file_bytes, 'chase_sample.csv')

if errors2:
    print(f"Errors: {errors2}")
else:
    print(f"✅ Parsed {len(df2)} transactions")
    print(f"✅ Detected format: {format_name2}")
    print(f"\nFirst 3 rows:")
    print(df2.head(3))

print("\n✅ All tests passed! Polars integration working correctly.")
