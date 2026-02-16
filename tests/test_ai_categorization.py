#!/usr/bin/env python3
"""Test AI categorization with sample unclear merchants"""

import os
import polars as pl
from modules.categorizer import categorize_transactions, categorize_with_ai

# Check for API key
api_key = os.environ.get('ANTHROPIC_API_KEY')
if not api_key:
    try:
        import streamlit as st
        if 'ANTHROPIC_API_KEY' in st.secrets:
            api_key = st.secrets['ANTHROPIC_API_KEY']
    except:
        pass

if not api_key:
    print("❌ No API key found. Set ANTHROPIC_API_KEY environment variable or add to .streamlit/secrets.toml")
    print("\nYou can test without AI by running: uv run python test_polars.py")
    exit(1)

print("✅ API key found")
print("\n" + "="*60)
print("Testing AI Categorization")
print("="*60)

# Create test data with deliberately unclear merchants
test_data = pl.DataFrame({
    'date': pl.Series([
        '2026-02-15',
        '2026-02-14',
        '2026-02-13',
        '2026-02-12',
        '2026-02-11',
        '2026-02-10',
        '2026-02-09',
    ]).str.strptime(pl.Date, "%Y-%m-%d"),
    'description': [
        'SQ *CORNER BAKERY',           # Square payment - unclear
        'TST* NAIL STUDIO',            # Toast payment - unclear
        'PAYPAL *CRAFTSHOP',           # PayPal - unclear
        'GOODRX',                      # Pharmacy discount - unclear
        'SCRIBD INC',                  # Subscription - unclear
        'NOTION LABS INC',             # Subscription - unclear
        'CHEWY.COM',                   # Pet supplies - should be caught by keywords
    ],
    'amount': [-12.50, -45.00, -28.75, -15.99, -11.99, -10.00, -67.23],
    'check_number': ['', '', '', '', '', '', ''],
    'original_category': ['', '', '', '', '', '', '']
})

print("\nTest transactions:")
print(test_data.select(['description', 'amount']))

print("\n" + "="*60)
print("Step 1: Keyword-only categorization")
print("="*60)

# Categorize without AI
result_no_ai = categorize_transactions(test_data, use_ai=False)
print(result_no_ai.select(['description', 'category', 'confidence']))

low_conf = result_no_ai.filter(pl.col('confidence') < 0.7)
print(f"\n⚠️  {len(low_conf)} transactions with low confidence (<70%)")

print("\n" + "="*60)
print("Step 2: AI-enhanced categorization")
print("="*60)

# Categorize with AI
result_with_ai = categorize_transactions(test_data, use_ai=True, api_key=api_key)
print(result_with_ai.select(['description', 'category', 'confidence']))

# Compare results
print("\n" + "="*60)
print("Comparison: Keyword vs AI")
print("="*60)

comparison = pl.DataFrame({
    'description': result_no_ai['description'],
    'keyword_category': result_no_ai['category'],
    'keyword_conf': result_no_ai['confidence'],
    'ai_category': result_with_ai['category'],
    'ai_conf': result_with_ai['confidence']
})

print(comparison)

# Count improvements
improved = comparison.filter(
    (pl.col('keyword_conf') < 0.7) & (pl.col('ai_conf') >= 0.7)
)

print(f"\n✅ AI improved categorization for {len(improved)} transactions")

if len(improved) > 0:
    print("\nImproved transactions:")
    print(improved.select(['description', 'keyword_category', 'ai_category']))

print("\n" + "="*60)
print("✅ AI categorization test complete!")
print("="*60)
