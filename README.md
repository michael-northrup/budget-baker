# Budget Baker - Transaction Categorization Web App

A privacy-first web application for analyzing bank and credit union transaction CSVs, providing spending breakdowns by category with optional AI enhancement.

## Features

- **Multi-Bank Support**: Handles CSV exports from AFCU, Chase, and other financial institutions
- **Privacy-First**: All processing happens locally in your browser session - no data is saved to disk
- **Smart Categorization**: Keyword-based categorization (free, offline) with optional AI enhancement
- **Visual Analytics**: Interactive charts showing spending patterns by category
- **Export Options**: Download categorized data as CSV or PDF report
- **Inline Editing**: Manually adjust categories for any transaction

## Setup

### 1. Create Virtual Environment

```bash
cd budget-baker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Configure AI Categorization

For AI-enhanced categorization of ambiguous transactions:

```bash
# Copy the example secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit .streamlit/secrets.toml and add your Anthropic API key
# Get your API key from: https://console.anthropic.com/settings/keys
```

Your `.streamlit/secrets.toml` should look like:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

**Alternative:** You can also enter your API key directly in the app sidebar (not recommended for security).

**Note:** The app works fully offline without an API key using keyword-based categorization.

## Usage

### Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Using the App

1. **Upload CSV**: Drag and drop or browse for your bank's CSV export
2. **Review Parsing**: Check the preview to ensure columns were detected correctly
3. **(Optional) Enable AI**: Toggle "Use AI for unclear items" in sidebar if you have an API key
4. **Categorize**: Click the categorize button to assign categories to transactions
5. **Review & Edit**: Browse transactions by category and edit any miscategorized items
6. **Export**: Download your categorized data as CSV or PDF report

### AI Enhancement

When enabled, Budget Baker uses Claude Haiku to categorize transactions that keyword matching couldn't confidently identify (confidence < 70%):

- **Privacy**: Only sends merchant names (e.g., "WHOLEFDS SLU"), not full transaction details
- **Cost**: ~$0.001-0.01 per 100 transactions (Haiku pricing)
- **Performance**: Batches up to 100 merchants per API call
- **Fallback**: Works without AI using keyword-only categorization

## Privacy & Security

- **No Data Persistence**: Uploaded files are never saved to disk
- **Local Processing**: All categorization happens in your browser session
- **Optional AI**: AI categorization only sends merchant names (not full transaction details)
- **Session Only**: All data is cleared when you refresh the page

## Supported CSV Formats

The app automatically detects and handles multiple CSV formats:

- **AFCU**: Separate Debit/Credit columns with redundant negative signs
- **Chase**: Single Amount column with dual dates
- **Generic**: Automatic column detection with manual mapping fallback

## Categories (36 Total)

**Food & Drink:**
- Groceries
- Dining/Restaurants
- Fast Food
- Coffee
- Alcohol/Bars

**Transportation:**
- Gas/Transportation
- Auto/Car Maintenance
- Airfare

**Shopping:**
- Shopping
- Clothing
- Electronics
- Furniture

**Home:**
- Rent/Mortgage
- Home Improvement
- Bills/Utilities

**Services:**
- Subscriptions
- Insurance
- Professional Services
- Business Expenses

**Personal:**
- Healthcare
- Pharmacy
- Personal Care
- Fitness
- Entertainment

**Family:**
- Childcare
- Education
- Pets

**Travel:**
- Travel
- Hobbies

**Financial:**
- Fees
- Loans
- Credit Card Payment
- Taxes
- ATM/Cash
- Checks

**Other:**
- Gifts/Donations
- Income
- Transfers

## Development

### Run Tests

```bash
pytest tests/
```

### Project Structure

```
budget-baker/
├── app.py                 # Main Streamlit application
├── modules/
│   ├── csv_parser.py     # CSV parsing with format detection
│   ├── categorizer.py    # Keyword + AI categorization
│   ├── processor.py      # Data processing
│   ├── visualizations.py # Plotly charts
│   └── export.py         # CSV and PDF export
├── test_data/            # Sample CSV files
└── tests/                # Unit tests
```

## License

MIT

## Contributing

This is a personal project, but suggestions and bug reports are welcome via GitHub issues.
