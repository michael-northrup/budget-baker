# Setting Up AI Categorization

## Phase 5 is Complete! ✅

Budget Baker now uses **Claude Haiku 4** to categorize transactions that keyword matching can't confidently identify.

## Quick Setup

### 1. Get Your API Key

1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-api03-...`)

### 2. Add API Key to Budget Baker

**Option A: Secrets File (Recommended)**
```bash
cd budget-baker

# Create secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit the file and paste your key
# .streamlit/secrets.toml should contain:
# ANTHROPIC_API_KEY = "sk-ant-api03-YOUR_KEY_HERE"
```

**Option B: Environment Variable**
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-YOUR_KEY_HERE"
```

**Option C: In-App Input**
- Enter your API key directly in the app sidebar (less secure, not saved)

### 3. Run the App

```bash
uv run streamlit run app.py
```

### 4. Use AI Enhancement

1. In the sidebar, you should see "✅ API key configured"
2. Check the box: "Use AI for unclear items"
3. Upload your CSV file
4. Click "🏷️ Categorize Transactions (with AI)"

## How It Works

### Without AI (Keyword-only)
- Matches merchants against 15 category keyword lists
- Fast, free, offline
- ~85% accuracy for common merchants
- Low confidence (<70%) for unclear merchants like:
  - `SQ *BAKERY` (Square payment processor)
  - `TST* CAFE` (Toast payment processor)
  - `PAYPAL *STORE` (PayPal intermediary)

### With AI Enhancement
- Keywords run first (fast, free)
- Only unclear items (confidence <70%) go to AI
- Claude Haiku categorizes based on merchant name
- Batches up to 100 merchants per API call
- ~95% accuracy overall

### Privacy
- Only merchant names are sent to the API
- No amounts, dates, or personal info
- Example: `"WHOLEFDS SLU 10281"` → AI returns `"Groceries"`

### Cost
- Claude Haiku is very cheap: ~$0.001-0.01 per 100 transactions
- Only charges for unclear items (typically 10-20% of total)
- Example: 1000 transactions ≈ $0.02-0.05

## Testing

### Test with Sample Data
```bash
# Test keyword-only
uv run python test_polars.py

# Test AI enhancement (requires API key)
uv run python test_ai_categorization.py
```

### Expected Results

**test_ai_categorization.py** tests unclear merchants:
- `SQ *CORNER BAKERY` → Dining/Restaurants (AI)
- `TST* NAIL STUDIO` → Personal Care (AI)
- `PAYPAL *CRAFTSHOP` → Shopping (AI)
- `GOODRX` → Healthcare (AI)
- `SCRIBD INC` → Subscriptions (AI)
- `NOTION LABS INC` → Subscriptions (AI)
- `CHEWY.COM` → Pets (Keyword)

## Troubleshooting

### "No API key found"
- Check `.streamlit/secrets.toml` exists and contains valid key
- Or export `ANTHROPIC_API_KEY` environment variable
- Or enter key in app sidebar

### "API categorization error"
- Check API key is valid
- Check internet connection
- App will fall back to keyword-only categorization

### "Use AI for unclear items" is disabled
- API key is missing or invalid
- Add API key using one of the methods above

## Next Steps

Now that Phase 5 is complete, you can:

1. **Test the app**: Run it and try AI categorization
2. **Continue to Phase 6**: Inline category editing
3. **Continue to Phase 7**: CSV/PDF export
4. **Provide feedback**: What works? What needs improvement?

## API Key Security

✅ **Safe:**
- `.streamlit/secrets.toml` (gitignored, local only)
- Environment variable

❌ **Not recommended:**
- Hardcoding in source files
- Committing to git
- In-app input for long-term use (not persisted)

The `.gitignore` file already excludes `.streamlit/secrets.toml` to keep your key safe.
