"""
CSV Parser Module - Handles multiple bank CSV formats with intelligent detection
Using Polars for high-performance data processing
"""

import polars as pl
import chardet
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re
import io


# Known bank format profiles
KNOWN_FORMATS = {
    "afcu": {
        "date_columns": ["Date"],
        "description_columns": ["Description"],
        "amount_mode": "split",  # separate debit/credit
        "debit_column": "Debit",
        "credit_column": "Credit",
        "check_column": "No."
    },
    "chase": {
        "date_columns": ["Transaction Date", "Post Date"],
        "description_columns": ["Description"],
        "amount_mode": "single",
        "amount_column": "Amount",
        "category_column": "Category"  # Will be overridden
    }
}


def detect_encoding(file_bytes: bytes) -> str:
    """Detect file encoding using chardet"""
    result = chardet.detect(file_bytes)
    encoding = result['encoding']

    # Common bank exports use these encodings
    if encoding in ['ascii', 'ISO-8859-1', 'Windows-1252']:
        return 'Windows-1252'

    return encoding or 'utf-8'


def find_header_row(lines: List[str], max_rows: int = 10) -> int:
    """
    Find the header row by looking for rows with typical column names
    Returns the index of the header row
    """
    common_headers = [
        'date', 'description', 'amount', 'debit', 'credit',
        'transaction', 'post', 'memo', 'category', 'type'
    ]

    for idx in range(min(max_rows, len(lines))):
        line = lines[idx].lower()
        # Check for common headers
        matches = sum(1 for h in common_headers if h in line)
        if matches >= 2:
            return idx

    return 0


def normalize_amount(value: str, is_debit: bool = False) -> float:
    """
    Normalize amount strings to float
    Handles: $, commas, parentheses (negative), redundant minus signs
    """
    if value is None or value == '':
        return 0.0

    # Convert to string and strip whitespace
    value = str(value).strip()

    # Remove currency symbols and commas
    value = value.replace('$', '').replace(',', '')

    # Handle parenthetical negatives: (123.45) -> -123.45
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]

    try:
        amount = float(value)

        # For AFCU-style: Debit column already has negative sign
        # We want debits to be negative, credits to be positive
        if is_debit and amount > 0:
            amount = -amount

        return amount
    except (ValueError, AttributeError):
        return 0.0


def clean_description(description: str) -> str:
    """Remove bank-specific annotations like (R), (S), etc."""
    if description is None or description == '':
        return ""

    # Remove trailing annotations like (R), (S), (P), etc.
    description = re.sub(r'\s*\([A-Z]\)\s*$', '', str(description))

    # Clean up excessive whitespace
    description = ' '.join(description.split())

    return description.strip()


def match_format_profile(columns: List[str]) -> Optional[str]:
    """
    Match CSV columns against known format profiles
    Returns format name if confident match found
    """
    columns_lower = [col.lower().strip() for col in columns]

    for format_name, profile in KNOWN_FORMATS.items():
        matches = 0
        total_checks = 0

        # Check date columns
        for date_col in profile.get('date_columns', []):
            total_checks += 1
            if date_col.lower() in columns_lower:
                matches += 1

        # Check description columns
        for desc_col in profile.get('description_columns', []):
            total_checks += 1
            if desc_col.lower() in columns_lower:
                matches += 1

        # Check amount columns
        if profile['amount_mode'] == 'split':
            total_checks += 2
            if profile.get('debit_column', '').lower() in columns_lower:
                matches += 1
            if profile.get('credit_column', '').lower() in columns_lower:
                matches += 1
        else:
            total_checks += 1
            if profile.get('amount_column', '').lower() in columns_lower:
                matches += 1

        # If most columns match, use this profile
        if matches >= total_checks * 0.7:  # 70% match threshold
            return format_name

    return None


def parse_csv(file_bytes: bytes, file_name: str) -> Tuple[pl.DataFrame, Optional[str], Optional[List[str]]]:
    """
    Parse CSV file and return standardized Polars DataFrame

    Returns:
        - Polars DataFrame with columns: date, description, amount, check_number, original_category
        - Format name (if detected) or None
        - Error message list (if any) or None
    """
    errors = []

    # Detect encoding
    encoding = detect_encoding(file_bytes)

    try:
        # Decode bytes to string
        csv_string = file_bytes.decode(encoding)
        lines = csv_string.split('\n')

        # Find header row
        header_idx = find_header_row(lines)

        # Read CSV with Polars, skipping to header row
        df = pl.read_csv(
            io.StringIO(csv_string),
            skip_rows=header_idx,
            ignore_errors=True,
            null_values=['', 'NA', 'N/A', 'null']
        )

        # Remove completely empty rows
        df = df.filter(~pl.all_horizontal(pl.all().is_null()))

        # Try to match format profile
        format_name = match_format_profile(df.columns)

        if format_name:
            # Use known format profile
            profile = KNOWN_FORMATS[format_name]
            standardized_df = _parse_with_profile(df, profile)
        else:
            # Use heuristic detection
            standardized_df = _parse_with_heuristics(df)

        return standardized_df, format_name, None

    except Exception as e:
        errors.append(f"Error parsing CSV: {str(e)}")
        return pl.DataFrame(), None, errors


def _parse_with_profile(df: pl.DataFrame, profile: Dict) -> pl.DataFrame:
    """Parse DataFrame using a known format profile"""

    # Extract date column
    date_col = profile['date_columns'][0]

    # Extract description column
    desc_col = profile['description_columns'][0]

    # Build the result DataFrame
    if profile['amount_mode'] == 'split':
        # Handle split debit/credit columns
        debit_col = profile['debit_column']
        credit_col = profile['credit_column']

        result_df = df.select([
            pl.col(date_col).alias('date_str'),
            pl.col(desc_col).alias('description_raw'),
            pl.col(debit_col).fill_null('').alias('debit_raw'),
            pl.col(credit_col).fill_null('').alias('credit_raw'),
            pl.col(profile.get('check_column', desc_col)).fill_null('').alias('check_number') if profile.get('check_column') in df.columns else pl.lit('').alias('check_number'),
            pl.lit('').alias('original_category')
        ])

        # Process amounts using map_elements for custom logic
        result_df = result_df.with_columns([
            pl.col('debit_raw').map_elements(lambda x: normalize_amount(x, is_debit=True), return_dtype=pl.Float64).alias('debit'),
            pl.col('credit_raw').map_elements(lambda x: normalize_amount(x, is_debit=False), return_dtype=pl.Float64).alias('credit')
        ])

        # Combine debit and credit into single amount column
        result_df = result_df.with_columns([
            pl.when(pl.col('credit') != 0.0)
              .then(pl.col('credit'))
              .otherwise(pl.col('debit'))
              .alias('amount')
        ])

        # Drop temporary columns
        result_df = result_df.drop(['debit_raw', 'credit_raw', 'debit', 'credit'])

    else:
        # Handle single amount column
        amount_col = profile['amount_column']

        result_df = df.select([
            pl.col(date_col).alias('date_str'),
            pl.col(desc_col).alias('description_raw'),
            pl.col(amount_col).fill_null('').alias('amount_raw'),
            pl.lit('').alias('check_number'),
            pl.col(profile.get('category_column', desc_col)).fill_null('').alias('original_category') if profile.get('category_column') in df.columns else pl.lit('').alias('original_category')
        ])

        # Process amount
        result_df = result_df.with_columns([
            pl.col('amount_raw').map_elements(lambda x: normalize_amount(x), return_dtype=pl.Float64).alias('amount')
        ])

        result_df = result_df.drop('amount_raw')

    # Clean description
    result_df = result_df.with_columns([
        pl.col('description_raw').map_elements(clean_description, return_dtype=pl.String).alias('description')
    ])

    result_df = result_df.drop('description_raw')

    # Parse dates - try multiple formats
    result_df = result_df.with_columns([
        pl.col('date_str').str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias('date')
    ])

    # If parsing failed, try other common formats
    if result_df['date'].null_count() > 0:
        result_df = result_df.with_columns([
            pl.when(pl.col('date').is_null())
              .then(pl.col('date_str').str.strptime(pl.Date, "%m/%d/%y", strict=False))
              .otherwise(pl.col('date'))
              .alias('date')
        ])

    result_df = result_df.drop('date_str')

    # Filter out invalid rows
    result_df = result_df.filter(
        pl.col('date').is_not_null() & (pl.col('amount') != 0.0)
    )

    # Reorder columns
    result_df = result_df.select(['date', 'description', 'amount', 'check_number', 'original_category'])

    return result_df


def _parse_with_heuristics(df: pl.DataFrame) -> pl.DataFrame:
    """Parse DataFrame using heuristic column detection"""

    # Find columns by keyword matching
    date_col = _find_column(df.columns, ['date', 'trans', 'posted'])
    desc_col = _find_column(df.columns, ['description', 'desc', 'merchant', 'memo'])
    amount_col = _find_column(df.columns, ['amount', 'total'])
    debit_col = _find_column(df.columns, ['debit', 'withdrawal', 'payment'])
    credit_col = _find_column(df.columns, ['credit', 'deposit'])

    if not date_col or not desc_col:
        raise ValueError("Could not detect date or description columns")

    # Build result similar to profile-based parsing
    if amount_col:
        result_df = df.select([
            pl.col(date_col).alias('date_str'),
            pl.col(desc_col).alias('description_raw'),
            pl.col(amount_col).fill_null('').alias('amount_raw'),
            pl.lit('').alias('check_number'),
            pl.lit('').alias('original_category')
        ])

        result_df = result_df.with_columns([
            pl.col('amount_raw').map_elements(lambda x: normalize_amount(x), return_dtype=pl.Float64).alias('amount')
        ]).drop('amount_raw')

    elif debit_col and credit_col:
        result_df = df.select([
            pl.col(date_col).alias('date_str'),
            pl.col(desc_col).alias('description_raw'),
            pl.col(debit_col).fill_null('').alias('debit_raw'),
            pl.col(credit_col).fill_null('').alias('credit_raw'),
            pl.lit('').alias('check_number'),
            pl.lit('').alias('original_category')
        ])

        result_df = result_df.with_columns([
            pl.col('debit_raw').map_elements(lambda x: normalize_amount(x, is_debit=True), return_dtype=pl.Float64).alias('debit'),
            pl.col('credit_raw').map_elements(lambda x: normalize_amount(x, is_debit=False), return_dtype=pl.Float64).alias('credit')
        ])

        result_df = result_df.with_columns([
            pl.when(pl.col('credit') != 0.0)
              .then(pl.col('credit'))
              .otherwise(pl.col('debit'))
              .alias('amount')
        ]).drop(['debit_raw', 'credit_raw', 'debit', 'credit'])
    else:
        raise ValueError("Could not detect amount columns")

    # Clean description
    result_df = result_df.with_columns([
        pl.col('description_raw').map_elements(clean_description, return_dtype=pl.String).alias('description')
    ]).drop('description_raw')

    # Parse dates
    result_df = result_df.with_columns([
        pl.col('date_str').str.strptime(pl.Date, "%m/%d/%Y", strict=False).alias('date')
    ])

    if result_df['date'].null_count() > 0:
        result_df = result_df.with_columns([
            pl.when(pl.col('date').is_null())
              .then(pl.col('date_str').str.strptime(pl.Date, "%m/%d/%y", strict=False))
              .otherwise(pl.col('date'))
              .alias('date')
        ])

    result_df = result_df.drop('date_str')

    # Filter invalid rows
    result_df = result_df.filter(
        pl.col('date').is_not_null() & (pl.col('amount') != 0.0)
    )

    # Reorder columns
    result_df = result_df.select(['date', 'description', 'amount', 'check_number', 'original_category'])

    return result_df


def _find_column(columns: List[str], keywords: List[str]) -> Optional[str]:
    """Find column name matching any of the keywords"""
    columns_lower = {col.lower(): col for col in columns}

    for keyword in keywords:
        for col_lower, col_original in columns_lower.items():
            if keyword in col_lower:
                return col_original

    return None
