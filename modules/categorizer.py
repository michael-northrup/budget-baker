"""
Categorization Module - Two-tier categorization (keyword + optional AI)
Using Polars for high-performance data processing
"""

import os
import re
import logging
from typing import Dict, Tuple, Optional, List
import polars as pl
import json

logger = logging.getLogger(__name__)


# Category definitions with keyword rules
CATEGORIES = {
    'Groceries': {
        'keywords': [
            'wholefds', 'whole foods', 'trader joe', 'safeway', 'kroger', 'publix',
            'albertsons', 'food lion', 'giant', 'stop & shop', 'wegmans', 'aldi',
            'costco', 'sams club', 'target.*grocery', 'walmart.*grocery',
            'sprouts', 'fresh market', 'grocery', 'supermarket', 'hmart', 'market.*food'
        ],
        'confidence': 0.9
    },
    'Dining/Restaurants': {
        'keywords': [
            'restaurant', 'cafe', 'coffee', 'starbucks', 'dunkin', 'mcdonald',
            'burger king', 'wendys', 'taco bell', 'chipotle', 'subway', 'panera',
            'chick-fil-a', 'pizza', 'dominos', 'papa john', 'doordash', 'ubereats',
            'grubhub', 'dining', 'bar & grill', 'bistro', 'diner', 'eatery',
            'food.*delivery', 'seamless', 'postmates'
        ],
        'confidence': 0.9
    },
    'Gas/Transportation': {
        'keywords': [
            'shell', 'chevron', 'exxon', 'mobil', 'bp ', 'arco', 'conoco',
            'phillips 66', 'valero', 'citgo', 'gas station', 'fuel', '76 gas',
            'uber', 'lyft', 'taxi', 'transit', 'parking', 'metro', 'bus pass',
            'train', 'toll', 'subway card', 'mta', 'septa', 'bart', 'car.*rental',
            'enterprise', 'hertz', 'avis', 'budget rental'
        ],
        'confidence': 0.9
    },
    'Shopping': {
        'keywords': [
            'amazon', 'target', 'walmart', 'best buy', 'home depot', 'lowes',
            'kohls', 'macys', 'nordstrom', 'tj maxx', 'marshalls', 'ross',
            'old navy', 'gap', 'h&m', 'zara', 'ikea', 'bed bath', 'container store',
            'staples', 'office depot', 'cvs', 'walgreens', 'rite aid',
            'apple store', 'microsoft store', 'etsy', 'ebay', 'wayfair'
        ],
        'confidence': 0.85
    },
    'Bills/Utilities': {
        'keywords': [
            'electric', 'power', 'gas company', 'water', 'sewer', 'trash',
            'waste management', 'internet', 'cable', 'phone', 'wireless',
            'at&t', 'verizon', 't-mobile', 'sprint', 'comcast', 'xfinity',
            'spectrum', 'cox', 'century link', 'pge', 'sce', 'utility'
        ],
        'confidence': 0.95
    },
    'Subscriptions': {
        'keywords': [
            'netflix', 'hulu', 'disney+', 'prime video', 'spotify', 'apple music',
            'youtube premium', 'hbo', 'max', 'paramount', 'peacock',
            'adobe', 'microsoft 365', 'office 365', 'dropbox', 'icloud',
            'subscription', 'membership', 'patreon', 'onlyfans'
        ],
        'confidence': 0.95
    },
    'Insurance': {
        'keywords': [
            'insurance', 'state farm', 'geico', 'progressive', 'allstate',
            'farmers insurance', 'liberty mutual', 'usaa', 'aetna', 'blue cross',
            'united healthcare', 'cigna', 'humana', 'kaiser'
        ],
        'confidence': 0.95
    },
    'Rent/Mortgage': {
        'keywords': [
            'rent', 'mortgage', 'lease', 'landlord', 'property mgmt',
            'apartment', 'housing', 'wells fargo home', 'quicken loans',
            'rocket mortgage', 'chase mortgage'
        ],
        'confidence': 0.95
    },
    'Entertainment': {
        'keywords': [
            'movie', 'theater', 'cinema', 'amc', 'regal', 'concert', 'ticketmaster',
            'stubhub', 'steam', 'playstation', 'xbox', 'nintendo', 'gaming',
            'bowling', 'golf', 'gym', 'fitness', 'planetfitness', '24 hour',
            'equinox', 'yoga', 'sports', 'recreation'
        ],
        'confidence': 0.85
    },
    'Healthcare': {
        'keywords': [
            'pharmacy', 'doctor', 'dentist', 'hospital', 'medical', 'health',
            'clinic', 'urgent care', 'walgreens.*rx', 'cvs.*pharmacy',
            'kaiser', 'lab corp', 'quest diagnostics', 'therapy', 'physical therapy'
        ],
        'confidence': 0.9
    },
    'Personal Care': {
        'keywords': [
            'salon', 'barber', 'haircut', 'spa', 'massage', 'nail', 'beauty',
            'cosmetic', 'ulta', 'sephora', 'bath.*body'
        ],
        'confidence': 0.9
    },
    'Pets': {
        'keywords': [
            'pet', 'veterinary', 'vet', 'petsmart', 'petco', 'chewy',
            'dog', 'cat', 'animal hospital'
        ],
        'confidence': 0.95
    },
    'Gifts/Donations': {
        'keywords': [
            'charity', 'donation', 'nonprofit', 'foundation', 'church',
            'temple', 'mosque', 'patreon', 'gofundme', 'kickstarter',
            'red cross', 'salvation army', 'goodwill donation'
        ],
        'confidence': 0.9
    },
    'ATM/Cash': {
        'keywords': [
            'atm', 'cash withdrawal', 'cashback', 'cash advance'
        ],
        'confidence': 0.95
    },
    'Fees': {
        'keywords': [
            'fee', 'overdraft', 'nsf', 'late fee', 'service charge',
            'annual fee', 'maintenance', 'penalty'
        ],
        'confidence': 0.95
    },
    'Checks': {
        'keywords': [
            'check', 'ck ', 'chk', 'check number', 'check #', 'paper check',
            'written check', 'check payment'
        ],
        'confidence': 0.9
    },
    'Home Improvement': {
        'keywords': [
            'home depot', 'lowes', 'ace hardware', 'hardware', 'lumber',
            'paint store', 'building supply', 'hardware store', 'menards',
            'true value', 'repair', 'contractor'
        ],
        'confidence': 0.85
    },
    'Furniture': {
        'keywords': [
            'furniture', 'ikea', 'wayfair', 'ashley', 'rooms to go',
            'west elm', 'crate and barrel', 'pottery barn', 'home goods',
            'tj maxx home', 'home decor'
        ],
        'confidence': 0.9
    },
    'Auto/Car Maintenance': {
        'keywords': [
            'auto', 'car wash', 'oil change', 'tire', 'jiffy lube',
            'midas', 'pep boys', 'autozone', 'napa', 'mechanic',
            'auto repair', 'car repair', 'smog check', 'registration',
            'car service', 'brake', 'muffler'
        ],
        'confidence': 0.9
    },
    'Fast Food': {
        'keywords': [
            'mcdonalds', 'burger king', 'wendys', 'taco bell', 'kfc',
            'popeyes', 'chick-fil-a', 'arbys', 'sonic', 'jack in the box',
            'in-n-out', 'five guys', 'shake shack', 'drive thru', 'drive-thru'
        ],
        'confidence': 0.95
    },
    'Coffee': {
        'keywords': [
            'starbucks', 'dunkin', 'peets', 'coffee bean', 'dutch bros',
            'caribou coffee', 'coffee shop', 'cafe', 'espresso'
        ],
        'confidence': 0.95
    },
    'Alcohol/Bars': {
        'keywords': [
            'bar ', 'pub ', 'brewery', 'wine shop', 'liquor', 'total wine',
            'bevmo', 'beer', 'wine store', 'distillery', 'tavern', 'lounge',
            'nightclub', 'club '
        ],
        'confidence': 0.9
    },
    'Clothing': {
        'keywords': [
            'clothing', 'apparel', 'old navy', 'gap', 'banana republic',
            'h&m', 'zara', 'uniqlo', 'nike', 'adidas', 'foot locker',
            'nordstrom', 'macys', 'kohls', 'tj maxx', 'ross', 'marshalls',
            'fashion', 'shoe', 'footwear'
        ],
        'confidence': 0.85
    },
    'Electronics': {
        'keywords': [
            'best buy', 'apple store', 'microsoft store', 'electronics',
            'computer', 'laptop', 'iphone', 'samsung', 'gaming', 'console',
            'playstation', 'xbox', 'nintendo', 'microcenter', 'newegg',
            'dell', 'hp store', 'tech'
        ],
        'confidence': 0.9
    },
    'Education': {
        'keywords': [
            'tuition', 'school', 'university', 'college', 'student',
            'books', 'textbook', 'course', 'class', 'learning',
            'udemy', 'coursera', 'education', 'academy', 'training'
        ],
        'confidence': 0.95
    },
    'Childcare': {
        'keywords': [
            'daycare', 'childcare', 'babysitter', 'nanny', 'preschool',
            'kids club', 'child care', 'day care', 'after school'
        ],
        'confidence': 0.95
    },
    'Travel': {
        'keywords': [
            'hotel', 'motel', 'airbnb', 'vrbo', 'resort', 'booking.com',
            'expedia', 'hotels.com', 'marriott', 'hilton', 'hyatt',
            'best western', 'inn', 'lodge', 'vacation rental'
        ],
        'confidence': 0.9
    },
    'Airfare': {
        'keywords': [
            'airline', 'flight', 'airways', 'southwest', 'united', 'delta',
            'american airlines', 'jetblue', 'alaska air', 'spirit',
            'frontier', 'allegiant', 'airfare', 'airport'
        ],
        'confidence': 0.95
    },
    'Professional Services': {
        'keywords': [
            'lawyer', 'attorney', 'legal', 'accountant', 'cpa', 'tax prep',
            'consultant', 'consulting', 'professional fee', 'notary',
            'financial advisor', 'financial planning'
        ],
        'confidence': 0.9
    },
    'Business Expenses': {
        'keywords': [
            'business', 'office supply', 'office depot', 'staples',
            'fedex', 'ups store', 'shipping', 'postage', 'supplies',
            'professional', 'corporate'
        ],
        'confidence': 0.8
    },
    'Taxes': {
        'keywords': [
            'tax', 'irs', 'state tax', 'federal tax', 'property tax',
            'sales tax', 'income tax', 'tax payment'
        ],
        'confidence': 0.95
    },
    'Loans': {
        'keywords': [
            'loan payment', 'student loan', 'car loan', 'personal loan',
            'loan', 'lending', 'sofi', 'discover loan', 'nelnet',
            'navient', 'sallie mae', 'great lakes'
        ],
        'confidence': 0.95
    },
    'Credit Card Payment': {
        'keywords': [
            'credit card payment', 'cc payment', 'ccard payment',
            'autopay.*credit', 'payment.*chase', 'payment.*amex',
            'payment.*discover', 'payment.*capital one', 'payment.*citi',
            'payment.*visa', 'payment.*mastercard', 'crdautopay'
        ],
        'confidence': 0.95
    },
    'Pharmacy': {
        'keywords': [
            'pharmacy', 'cvs.*rx', 'walgreens.*rx', 'rite aid.*rx',
            'prescription', 'rx', 'drugstore', 'medicine', 'medication'
        ],
        'confidence': 0.95
    },
    'Fitness': {
        'keywords': [
            'gym', 'fitness', '24 hour', 'planetfitness', 'planet fitness',
            'la fitness', 'equinox', 'orangetheory', 'crossfit',
            'yoga', 'pilates', 'personal trainer', 'sports club'
        ],
        'confidence': 0.9
    },
    'Hobbies': {
        'keywords': [
            'hobby', 'craft', 'michaels', 'joann', 'hobby lobby',
            'art supply', 'music', 'instrument', 'guitar center',
            'sporting goods', 'dicks sporting', 'rei'
        ],
        'confidence': 0.85
    }
}

# Income and Transfer patterns (not expense categories)
INCOME_KEYWORDS = [
    'payroll', 'payro',  # handle truncated descriptions
    'salary', 'direct deposit', 'deposit.*salary',
    'income', 'payment received', 'refund', 'reimbursement',
    'dividend', 'interest payment', 'bonus', 'commission',
    'state.*payro', 'federal.*payro', 'employer.*dep', 'direct dep',
    'irs.*refund', 'tax refund', 'soc.*sec', 'social security',
    'pension', 'retirement.*dist', 'annuity',
    'unemployment', 'benefit.*payment', 'govt.*payment',
]

TRANSFER_KEYWORDS = [
    'transfer to savings', 'transfer from savings', 'transfer to checking', 'transfer from checking',
    'xfer', 'zelle', 'venmo', 'cashapp', 'cash app', 'paypal',
    'online transfer', 'mobile deposit', 'check deposit',
    'ach transfer', 'internal transfer', 'external transfer',
    'savings transfer', 'wire transfer', 'account transfer',
    'between accounts', 'from.*savings.*to.*checking', 'from.*checking.*to.*savings'
]


def normalize_merchant(description: str) -> str:
    """
    Normalize merchant name for better matching
    Removes numbers, special chars, extra spaces
    """
    # Convert to lowercase
    merchant = description.lower()

    # Remove common prefixes
    merchant = re.sub(r'^(purchase,?|automatic withdrawal,?|automatic deposit,?|payment,?|debit,?)\s*', '', merchant)

    # Remove trailing numbers and special characters
    merchant = re.sub(r'[#\*]\d+.*$', '', merchant)

    # Remove excessive whitespace
    merchant = ' '.join(merchant.split())

    return merchant.strip()


def categorize_by_keywords(description: str, amount: float) -> Tuple[str, float]:
    """
    Categorize transaction using keyword matching

    Returns:
        - Category name
        - Confidence score (0.0 to 1.0)
    """
    merchant = normalize_merchant(description)

    # Check if it's income — positive amounts are always income
    # Use 0.8 default (well above AI threshold of 0.7) so positive-amount
    # transactions never leak to the AI categorizer
    if amount > 0:
        for keyword in INCOME_KEYWORDS:
            if re.search(keyword, merchant):
                return 'Income', 0.95
        return 'Income', 0.8  # Default for positive amounts

    # Check if it's a transfer
    for keyword in TRANSFER_KEYWORDS:
        if re.search(keyword, merchant):
            return 'Transfers', 0.9

    # Check expense categories
    best_category = 'Uncategorized'
    best_confidence = 0.0

    for category, rules in CATEGORIES.items():
        for keyword in rules['keywords']:
            # Use word boundary matching for better accuracy
            pattern = r'\b' + keyword.replace('*', r'.*') + r'\b'
            if re.search(pattern, merchant):
                confidence = rules['confidence']
                if confidence > best_confidence:
                    best_category = category
                    best_confidence = confidence
                    # If we find a high-confidence match, stop searching
                    if confidence >= 0.95:
                        return best_category, best_confidence

    return best_category, best_confidence


SYSTEM_PROMPT = """You are an expert at categorizing financial transactions. You will receive merchant names and must assign each to exactly one category.

CRITICAL RULES:
- NEVER use "Groceries" as a default or fallback for unknown merchants. Groceries is ONLY for actual grocery stores (Whole Foods, Trader Joe's, Safeway, Kroger, Walmart Grocery, etc.).
- If you are unsure of a merchant's category, use "Uncategorized" — do NOT guess.
- Payroll, deposits, salary, and direct deposits from employers are "Income".
- Government payments (state/federal payroll, tax refunds, benefits) are "Income".

IMPORTANT CONTEXT:
Many merchants appear through payment processors. Look past the processor to identify the actual business:
- "SQ *" = Square (payment processor - look at what follows)
- "TST*" = Toast (restaurant POS - usually dining)
- "Nyx*" = Payment processor (look at business name/type)
- "PAYPAL *" = PayPal (look at merchant after asterisk)
- Numbers after merchant = location/transaction ID (ignore these)

Valid Categories:

Food & Drink:
- Groceries: Supermarkets, grocery stores, food markets (Whole Foods, Trader Joe's, Safeway, etc.)
- Dining/Restaurants: Sit-down restaurants, cafes, food delivery (NOT fast food)
- Fast Food: Quick service, drive-thru (McDonald's, Taco Bell, Chipotle, etc.)
- Coffee: Coffee shops, cafes (Starbucks, Dunkin, Peet's, etc.)
- Alcohol/Bars: Bars, breweries, liquor stores, wine shops

Transportation:
- Gas/Transportation: Gas stations, EV charging (Shell, Chevron, Electrify America, ChargePoint, EVgo), rideshare, parking, tolls
- Auto/Car Maintenance: Oil changes, repairs, car washes, auto parts
- Airfare: Airlines, flights, airport services

Shopping:
- Shopping: General retail, department stores, online shopping
- Clothing: Apparel, shoes, fashion retailers
- Electronics: Tech stores, computers, phones, gaming
- Furniture: Home furnishing, decor stores

Home:
- Rent/Mortgage: Housing payments, property management
- Home Improvement: Hardware stores, building supplies, contractors
- Bills/Utilities: Electric, water, internet, phone, cable, gas company

Services:
- Subscriptions: Streaming, software, memberships (Netflix, Spotify, Adobe)
- Insurance: Auto, health, life, property insurance
- Professional Services: Lawyers, accountants, consultants
- Business Expenses: Office supplies, shipping, professional fees

Personal:
- Healthcare: Doctors, dentists, hospitals, clinics
- Pharmacy: Prescriptions, drugstores, medications
- Personal Care: Salon, barber, spa, beauty products
- Fitness: Gyms, yoga studios, sports clubs, trainers
- Entertainment: Movies, theaters, concerts, recreation

Family:
- Childcare: Daycare, babysitters, preschool
- Education: Tuition, schools, courses, books, training
- Pets: Pet supplies, veterinary, pet stores

Travel:
- Travel: Hotels, accommodations, vacation rentals
- Hobbies: Craft stores, hobby supplies, sporting goods

Financial:
- Fees: Bank fees, late fees, service charges
- Loans: Student loans, car loans, personal loans
- Credit Card Payment: Payments to credit cards, autopay to cards
- Taxes: Tax payments, IRS, state/federal tax
- Checks: Check payments, written checks
- ATM/Cash: ATM withdrawals, cash advances

Other:
- Gifts/Donations: Charitable donations, gifts, nonprofits, fundraising
- Income: Salary, wages, refunds, reimbursements
- Transfers: Between accounts, Venmo, Zelle, PayPal transfers
- Uncategorized: Only if truly unclear

Reasoning approach:
1. Strip payment processor prefix (SQ*, TST*, Nyx*, PAYPAL*)
2. Ignore trailing numbers/IDs
3. Identify core business name
4. Categorize based on business type
5. Use context clues (ELECTRIFY = EV charging, TST = restaurants, etc.)

Respond with ONLY a JSON object mapping each merchant to its category. No explanations or extra text."""


# Retry on transient errors with exponential backoff: 1s, 2s, 4s
def _call_serving_endpoint(gateway_url: str, token: str, endpoint_name: str, merchants: List[str]) -> str:
    """Make a single API call to the serving endpoint."""
    import requests as _requests

    user_content = (
        "Categorize these merchants:\n"
        f"{json.dumps(merchants)}\n\n"
        "Examples:\n"
        '- "SQ *CORNER BAKERY" -> Dining/Restaurants\n'
        '- "TST* PIZZA PLACE" -> Dining/Restaurants\n'
        '- "Nyx*8336322778 ELECTRIFY" -> Gas/Transportation\n'
        '- "wholefds slu 10281" -> Groceries\n'
        '- "shell oil 57432658901" -> Gas/Transportation\n'
        '- "AUTOPAY CHASE CREDIT" -> Credit Card Payment\n'
        '- "starbucks #8901" -> Coffee\n'
        '- "netflix.com" -> Subscriptions\n'
        '- "STATE OF UTAH PAYROLL" -> Income\n'
        '- "AUTOMATIC DEPOSIT EMPLOYER" -> Income\n'
        '- "UNKNOWN MERCHANT 12345" -> Uncategorized (not Groceries)'
    )

    url = f"{gateway_url}/{endpoint_name}/invocations"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 4096,
        "temperature": 0,
    }

    resp = _requests.post(url, headers=headers, json=payload, timeout=60)

    if not resp.ok:
        raise ValueError(f"Model error {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def categorize_with_ai(merchants: List[str]) -> Dict[str, str]:
    """
    Use Databricks-hosted model to categorize merchants that keyword matching missed.

    Uses DatabricksOpenAI client which automatically picks up credentials
    from the Databricks App service principal (DATABRICKS_CLIENT_ID /
    DATABRICKS_CLIENT_SECRET injected by the platform).

    Args:
        merchants: List of normalized merchant names

    Returns:
        Dictionary mapping merchant -> category
    """
    if not merchants:
        return {}

    # Get list of all valid categories
    valid_categories = list(CATEGORIES.keys()) + ['Income', 'Transfers', 'Uncategorized']

    try:
        endpoint_name = os.environ["DATABRICKS_ENDPOINT_NAME"]
        gateway_url = os.environ["DATABRICKS_GATEWAY_URL"]
        token = os.environ["DATABRICKS_TOKEN"]

        response_text = _call_serving_endpoint(gateway_url, token, endpoint_name, merchants)

        # Strip markdown code blocks that Llama often wraps around JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        categorization = json.loads(response_text)

        # Validate categories
        validated = {}
        for merchant, category in categorization.items():
            if category in valid_categories:
                validated[merchant] = category
            else:
                logger.warning(f"AI returned invalid category '{category}' for '{merchant}', defaulting to Uncategorized")
                validated[merchant] = 'Uncategorized'

        return validated

    except json.JSONDecodeError as e:
        logger.error(f"AI returned invalid JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"AI categorization error: {e}")
        raise


def categorize_transactions(df: pl.DataFrame, use_ai: bool = False) -> pl.DataFrame:
    """
    Categorize all transactions in the Polars DataFrame

    Phase 3: Keyword-based only
    Phase 5: AI enhancement for low-confidence items

    Args:
        df: Polars DataFrame with columns [date, description, amount, check_number, original_category]
        use_ai: Whether to use AI for low-confidence items

    Returns:
        Polars DataFrame with added columns [category, confidence, type]
    """
    # Apply keyword categorization using map_elements
    result_df = df.with_columns([
        pl.struct(['description', 'amount'])
          .map_elements(lambda x: categorize_by_keywords(x['description'], x['amount'])[0], return_dtype=pl.String)
          .alias('category'),
        pl.struct(['description', 'amount'])
          .map_elements(lambda x: categorize_by_keywords(x['description'], x['amount'])[1], return_dtype=pl.Float64)
          .alias('confidence')
    ])

    # Determine transaction type
    result_df = result_df.with_columns([
        pl.when(pl.col('amount') > 0)
          .then(pl.lit('Income'))
          .when(pl.col('category') == 'Transfers')
          .then(pl.lit('Transfer'))
          .otherwise(pl.lit('Expense'))
          .alias('type')
    ])

    # Phase 5: AI enhancement for low-confidence items
    if use_ai:
        # Find low-confidence expense transactions (exclude Income/Transfers)
        # Hard guard: amount must be negative — never send income (positive) to AI
        low_confidence = result_df.filter(
            (pl.col('confidence') < 0.7) &
            (pl.col('type') == 'Expense') &
            (pl.col('amount') < 0)
        )

        if len(low_confidence) > 0:
            # Get unique merchants to minimize API calls
            unique_merchants = low_confidence.select([
                pl.col('description').map_elements(normalize_merchant, return_dtype=pl.String).alias('merchant')
            ]).unique().to_series().to_list()

            # Batch merchants (max 100 per API call)
            batch_size = 100
            all_categorizations = {}

            for i in range(0, len(unique_merchants), batch_size):
                batch = unique_merchants[i:i+batch_size]
                batch_results = categorize_with_ai(batch)
                all_categorizations.update(batch_results)

            # Apply AI categorizations back to the dataframe
            if all_categorizations:
                # Create mapping dataframe
                merchant_to_category = pl.DataFrame({
                    'merchant': list(all_categorizations.keys()),
                    'ai_category': list(all_categorizations.values())
                })

                # Add merchant column to result_df for joining
                result_df = result_df.with_columns([
                    pl.col('description').map_elements(normalize_merchant, return_dtype=pl.String).alias('merchant')
                ])

                # Join with AI categorizations
                result_df = result_df.join(merchant_to_category, on='merchant', how='left')

                # Update category and confidence for low-confidence items
                # Hard guard: only update negative-amount (expense) transactions
                result_df = result_df.with_columns([
                    pl.when((pl.col('confidence') < 0.7) & (pl.col('type') == 'Expense') & (pl.col('amount') < 0) & pl.col('ai_category').is_not_null())
                      .then(pl.col('ai_category'))
                      .otherwise(pl.col('category'))
                      .alias('category'),
                    pl.when((pl.col('confidence') < 0.7) & (pl.col('type') == 'Expense') & (pl.col('amount') < 0) & pl.col('ai_category').is_not_null())
                      .then(pl.lit(0.85))  # AI confidence score
                      .otherwise(pl.col('confidence'))
                      .alias('confidence')
                ])

                # Drop temporary columns
                result_df = result_df.drop(['merchant', 'ai_category'])

    # Enforce category/type consistency — AI may have overwritten category after type was set
    result_df = result_df.with_columns([
        pl.when(pl.col('type') == 'Income')
          .then(pl.lit('Income'))
          .when(pl.col('type') == 'Transfer')
          .then(pl.lit('Transfers'))
          .otherwise(pl.col('category'))
          .alias('category')
    ])

    # Add a unique row identifier so edits can target specific transactions
    # (descriptions are not unique -- multiple transactions can share the same one)
    result_df = result_df.with_row_index('row_id')

    return result_df


def get_unique_merchants(df: pl.DataFrame) -> List[str]:
    """
    Get list of unique merchant names from descriptions
    Useful for AI batch categorization in Phase 5
    """
    merchants = df.select([
        pl.col('description').map_elements(normalize_merchant, return_dtype=pl.String)
    ]).unique().to_series().to_list()

    return sorted(merchants)


def get_category_summary(df: pl.DataFrame) -> pl.DataFrame:
    """
    Get summary of spending by category

    Returns:
        Polars DataFrame with columns [category, count, total, average]
    """
    # Filter to expenses only
    expenses = df.filter(pl.col('type') == 'Expense')

    if len(expenses) == 0:
        return pl.DataFrame({
            'category': [],
            'count': [],
            'total': [],
            'average': []
        })

    # Group by category and aggregate
    summary = expenses.group_by('category').agg([
        pl.count().alias('count'),
        pl.col('amount').sum().abs().alias('total'),
        pl.col('amount').mean().abs().alias('average')
    ])

    # Sort by total descending
    summary = summary.sort('total', descending=True)

    # Round to 2 decimal places
    summary = summary.with_columns([
        pl.col('total').round(2),
        pl.col('average').round(2)
    ])

    return summary
