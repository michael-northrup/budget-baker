from fastapi import APIRouter, HTTPException
import polars as pl

from modules.categorizer import categorize_transactions, get_category_summary, CATEGORIES
from ..models.schemas import CategorizeRequest, CategorizeResponse, Transaction

router = APIRouter()


@router.post("/categorize", response_model=CategorizeResponse)
async def categorize(request: CategorizeRequest):
    """Categorize transactions using keyword matching and optional AI."""
    try:
        # Drop the temporary row_id from upload before re-categorizing
        # (categorize_transactions will assign a fresh one via with_row_index)
        rows = request.transactions
        if rows and "row_id" in rows[0]:
            rows = [{k: v for k, v in r.items() if k != "row_id"} for r in rows]

        df = pl.DataFrame(rows)

        categorized_df = categorize_transactions(
            df,
            use_ai=request.use_ai,
        )

        summary_df = get_category_summary(categorized_df)
        summary = summary_df.to_dicts()

        transactions = []
        for row in categorized_df.to_dicts():
            transactions.append(Transaction(
                row_id=int(row.get("row_id", 0)),
                date=str(row.get("date", "")),
                description=str(row.get("description", "")),
                amount=float(row.get("amount") or 0),
                category=str(row.get("category", "Uncategorized")),
                confidence=float(row.get("confidence") or 0),
                type=str(row.get("type", "Expense")),
                check_number=str(row["check_number"]) if row.get("check_number") else None,
                original_category=str(row["original_category"]) if row.get("original_category") else None,
            ))

        return CategorizeResponse(transactions=transactions, summary=summary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """Return the list of valid category names."""
    return {"categories": list(CATEGORIES.keys()) + ['Income', 'Transfers', 'Uncategorized']}
