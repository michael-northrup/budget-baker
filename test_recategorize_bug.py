#!/usr/bin/env python3
"""
Test for the data corruption bug: recategorizing a single transaction
should NOT affect other transactions with the same description.

This test reproduces the exact scenario that caused the reported bug:
- Multiple transactions share the same description
- One is "Uncategorized", others have established categories
- Recategorizing the uncategorized one should only change THAT row
"""

import polars as pl
from modules.categorizer import categorize_transactions


def build_test_df():
    """Build a test DataFrame that mimics the reported scenario.
    
    Includes duplicate descriptions to trigger the original bug.
    """
    return pl.DataFrame({
        'date': [
            '2026-01-15', '2026-01-20', '2026-01-25',
            '2026-02-01', '2026-02-05', '2026-02-10',
            '2026-02-12',
        ],
        'description': [
            'CHASE CREDIT CRD AUTOPAY',    # row 0: credit card payment (expense)
            'CHASE CREDIT CRD AUTOPAY',    # row 1: same desc, different date
            'CHASE CREDIT CRD AUTOPAY',    # row 2: same desc again
            'ACME CORP PAYROLL',           # row 3: income
            'WHOLEFDS SLU 10281',          # row 4: groceries (expense)
            'TRANSFER TO SAVINGS',         # row 5: transfer
            'MYSTERIOUS MERCHANT XYZ',     # row 6: uncategorized (expense)
        ],
        'amount': [
            -1500.00, -1500.00, -1500.00,  # 3 identical credit card payments
            3500.00,                        # payroll deposit
            -45.23,                         # groceries
            -200.00,                        # transfer
            -127.50,                        # uncategorized expense
        ],
        'check_number': [''] * 7,
        'original_category': [''] * 7,
    }).with_columns(pl.col('date').str.to_date('%Y-%m-%d'))

    
def simulate_apply_edits_OLD(categorized_df, pending_edits):
    """Reproduce the OLD buggy behavior: match by description, global type reassignment."""
    updated_df = categorized_df.clone()
    
    for description, new_category in pending_edits.items():
        updated_df = updated_df.with_columns(
            pl.when(pl.col('description') == description)
              .then(pl.lit(new_category))
              .otherwise(pl.col('category'))
              .alias('category')
        )
    
    # Global type reassignment (the bug amplifier)
    updated_df = updated_df.with_columns([
        pl.when(pl.col('amount') > 0)
          .then(pl.lit('Income'))
          .when(pl.col('category') == 'Transfers')
          .then(pl.lit('Transfer'))
          .otherwise(pl.lit('Expense'))
          .alias('type')
    ])
    
    return updated_df


def simulate_apply_edits_NEW(categorized_df, pending_edits):
    """Reproduce the NEW fixed behavior: match by row_id, targeted type reassignment."""
    updated_df = categorized_df.clone()
    
    edited_ids = list(pending_edits.keys())
    edited_cats = [pending_edits[rid] for rid in edited_ids]
    edit_map_df = pl.DataFrame({
        'row_id': [int(rid) for rid in edited_ids],
        'new_category': edited_cats,
    }).cast({'row_id': pl.UInt32})

    updated_df = updated_df.join(edit_map_df, on='row_id', how='left')
    updated_df = updated_df.with_columns(
        pl.when(pl.col('new_category').is_not_null())
          .then(pl.col('new_category'))
          .otherwise(pl.col('category'))
          .alias('category')
    ).drop('new_category')

    # Update type ONLY for edited rows
    updated_df = updated_df.with_columns(
        pl.when(pl.col('row_id').is_in([int(rid) for rid in edited_ids]))
          .then(
              pl.when(pl.col('amount') > 0)
                .then(pl.lit('Income'))
                .when(pl.col('category') == 'Transfers')
                .then(pl.lit('Transfer'))
                .otherwise(pl.lit('Expense'))
          )
          .otherwise(pl.col('type'))
          .alias('type')
    )
    
    return updated_df


def compute_totals(df):
    """Compute income, expense, and net totals like the Results page does."""
    income = df.filter(pl.col('type') == 'Income').select(pl.col('amount').sum()).item()
    expenses_raw = df.filter(pl.col('type') == 'Expense').select(pl.col('amount').sum()).item()
    expenses = abs(expenses_raw)
    net = income + expenses_raw
    transfer = df.filter(pl.col('type') == 'Transfer').select(pl.col('amount').sum()).item()
    return {
        'income': income,
        'expenses': expenses,
        'net': net,
        'transfer': abs(transfer) if transfer else 0,
    }


def test_row_id_exists():
    """Test that categorize_transactions adds a row_id column."""
    df = build_test_df()
    cat_df = categorize_transactions(df)
    
    assert 'row_id' in cat_df.columns, "row_id column should exist after categorization"
    assert cat_df['row_id'].n_unique() == len(cat_df), "row_id should be unique per row"
    print("PASS: row_id column exists and is unique")


def test_old_code_has_bug():
    """Demonstrate that the OLD code corrupts data when descriptions collide."""
    df = build_test_df()
    cat_df = categorize_transactions(df)
    
    # Find the uncategorized row
    uncat_rows = cat_df.filter(pl.col('category') == 'Uncategorized')
    assert len(uncat_rows) >= 1, "Should have at least 1 uncategorized transaction"
    
    before = compute_totals(cat_df)
    print(f"  Before: Income=${before['income']:,.2f}, Expenses=${before['expenses']:,.2f}, Net=${before['net']:,.2f}")
    
    # Simulate the OLD buggy edit: recategorize by description
    # Find a description that appears multiple times
    desc_counts = cat_df.group_by('description').agg(pl.count().alias('n')).filter(pl.col('n') > 1)
    
    if len(desc_counts) > 0:
        dup_desc = desc_counts['description'][0]
        # OLD code: key by description
        old_pending = {dup_desc: 'Transfers'}
        old_result = simulate_apply_edits_OLD(cat_df, old_pending)
        after_old = compute_totals(old_result)
        
        print(f"  After (OLD, desc-based, recategorize '{dup_desc}' to Transfers):")
        print(f"    Income=${after_old['income']:,.2f}, Expenses=${after_old['expenses']:,.2f}, Net=${after_old['net']:,.2f}")
        
        # Count how many rows changed
        changed = (old_result['category'] != cat_df['category']).sum()
        print(f"    Rows changed: {changed} (should be 1, but is more due to bug)")
        
        if changed > 1:
            print("  CONFIRMED: Old code modifies multiple rows for a single edit")
            return True
        else:
            print("  NOTE: No duplicate descriptions in test data triggered the bug")
            return False
    else:
        print("  NOTE: No duplicate descriptions found")
        return False


def test_new_code_fixes_bug():
    """Verify that the NEW code only modifies the intended row."""
    df = build_test_df()
    cat_df = categorize_transactions(df)
    
    before = compute_totals(cat_df)
    print(f"  Before: Income=${before['income']:,.2f}, Expenses=${before['expenses']:,.2f}, Net=${before['net']:,.2f}")
    
    # Pick one specific row to edit (the first CHASE CREDIT CRD AUTOPAY)
    chase_rows = cat_df.filter(pl.col('description') == 'CHASE CREDIT CRD AUTOPAY')
    assert len(chase_rows) == 3, f"Expected 3 CHASE rows, got {len(chase_rows)}"
    
    target_row_id = int(chase_rows['row_id'][0])
    original_category = chase_rows['category'][0]
    
    print(f"  Editing row_id={target_row_id} ('{chase_rows['description'][0]}') from '{original_category}' to 'Transfers'")
    
    # NEW code: key by row_id
    new_pending = {target_row_id: 'Transfers'}
    new_result = simulate_apply_edits_NEW(cat_df, new_pending)
    after_new = compute_totals(new_result)
    
    print(f"  After (NEW, row_id-based):")
    print(f"    Income=${after_new['income']:,.2f}, Expenses=${after_new['expenses']:,.2f}, Net=${after_new['net']:,.2f}")
    
    # Count how many rows changed category
    changed_cat = (new_result['category'] != cat_df['category']).sum()
    changed_type = (new_result['type'] != cat_df['type']).sum()
    print(f"    Categories changed: {changed_cat}")
    print(f"    Types changed: {changed_type}")
    
    assert changed_cat == 1, f"Expected exactly 1 category change, got {changed_cat}"
    assert changed_type <= 1, f"Expected at most 1 type change, got {changed_type}"
    
    # Verify the other CHASE rows are untouched
    other_chase = new_result.filter(
        (pl.col('description') == 'CHASE CREDIT CRD AUTOPAY') & 
        (pl.col('row_id') != target_row_id)
    )
    for row in other_chase.iter_rows(named=True):
        orig_row = cat_df.filter(pl.col('row_id') == row['row_id']).row(0, named=True)
        assert row['category'] == orig_row['category'], \
            f"Row {row['row_id']} category changed from '{orig_row['category']}' to '{row['category']}'"
        assert row['type'] == orig_row['type'], \
            f"Row {row['row_id']} type changed from '{orig_row['type']}' to '{row['type']}'"
    
    print("  PASS: Only the targeted row was modified")


def test_recategorize_uncategorized_to_expense():
    """Recategorizing an uncategorized expense to Groceries should keep it as Expense."""
    df = build_test_df()
    cat_df = categorize_transactions(df)
    
    # Find uncategorized rows
    uncat = cat_df.filter(pl.col('category') == 'Uncategorized')
    if len(uncat) == 0:
        print("  SKIP: No uncategorized rows in test data")
        return
    
    target_id = int(uncat['row_id'][0])
    target_amount = uncat['amount'][0]
    
    print(f"  Recategorizing row_id={target_id} (amount=${target_amount}) from Uncategorized to Groceries")
    
    new_pending = {target_id: 'Groceries'}
    result = simulate_apply_edits_NEW(cat_df, new_pending)
    
    edited_row = result.filter(pl.col('row_id') == target_id).row(0, named=True)
    
    assert edited_row['category'] == 'Groceries', f"Category should be Groceries, got {edited_row['category']}"
    
    if target_amount < 0:
        assert edited_row['type'] == 'Expense', f"Negative amount should stay Expense, got {edited_row['type']}"
    else:
        assert edited_row['type'] == 'Income', f"Positive amount should be Income, got {edited_row['type']}"
    
    print(f"  PASS: category='{edited_row['category']}', type='{edited_row['type']}'")


def test_recategorize_to_transfers():
    """Recategorizing a single expense to Transfers should make it Transfer type."""
    df = build_test_df()
    cat_df = categorize_transactions(df)
    
    # Pick a known expense row
    expenses = cat_df.filter(pl.col('type') == 'Expense')
    target_id = int(expenses['row_id'][0])
    
    before = compute_totals(cat_df)
    target_amount = abs(float(expenses.filter(pl.col('row_id') == target_id)['amount'][0]))
    
    print(f"  Recategorizing row_id={target_id} (amount=${target_amount:,.2f}) to Transfers")
    
    new_pending = {target_id: 'Transfers'}
    result = simulate_apply_edits_NEW(cat_df, new_pending)
    after = compute_totals(result)
    
    edited_row = result.filter(pl.col('row_id') == target_id).row(0, named=True)
    assert edited_row['type'] == 'Transfer', f"Should be Transfer, got {edited_row['type']}"
    
    expense_diff = before['expenses'] - after['expenses']
    print(f"  Expense change: ${expense_diff:,.2f} (should be ~${target_amount:,.2f})")
    assert abs(expense_diff - target_amount) < 0.01, \
        f"Expenses should decrease by exactly ${target_amount:,.2f}, but decreased by ${expense_diff:,.2f}"
    
    print(f"  PASS: Expenses correctly reduced by ${expense_diff:,.2f}")


def test_totals_stable_after_noop_recategorize():
    """Recategorizing to the SAME category should not change any totals."""
    df = build_test_df()
    cat_df = categorize_transactions(df)
    
    before = compute_totals(cat_df)
    
    # Pick any row and "recategorize" it to its current category
    target_id = int(cat_df['row_id'][0])
    current_cat = cat_df.filter(pl.col('row_id') == target_id)['category'][0]
    
    new_pending = {target_id: current_cat}
    result = simulate_apply_edits_NEW(cat_df, new_pending)
    after = compute_totals(result)
    
    assert before == after, f"Totals should not change for no-op recategorization: before={before}, after={after}"
    print(f"  PASS: Totals unchanged after no-op recategorization")


if __name__ == '__main__':
    print("=" * 60)
    print("Test: row_id exists in categorized DataFrame")
    print("=" * 60)
    test_row_id_exists()
    
    print()
    print("=" * 60)
    print("Test: OLD code demonstrates the data corruption bug")
    print("=" * 60)
    test_old_code_has_bug()
    
    print()
    print("=" * 60)
    print("Test: NEW code fixes the bug (only modifies targeted row)")
    print("=" * 60)
    test_new_code_fixes_bug()
    
    print()
    print("=" * 60)
    print("Test: Recategorize uncategorized expense to Groceries")
    print("=" * 60)
    test_recategorize_uncategorized_to_expense()
    
    print()
    print("=" * 60)
    print("Test: Recategorize to Transfers changes type correctly")
    print("=" * 60)
    test_recategorize_to_transfers()
    
    print()
    print("=" * 60)
    print("Test: No-op recategorization preserves totals")
    print("=" * 60)
    test_totals_stable_after_noop_recategorize()
    
    print()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
