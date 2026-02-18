from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import polars as pl

from modules.csv_parser import parse_csv
from ..models.schemas import UploadResponse, UploadStats, Transaction

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(files: List[UploadFile] = File(...)):
    """Upload one or more CSV files and return parsed transactions."""
    all_dfs = []
    format_name = "Unknown"

    for file in files:
        content = await file.read()
        filename = file.filename or "upload.csv"
        try:
            df, detected_format, errors = parse_csv(content, filename)
            if detected_format:
                format_name = detected_format
            all_dfs.append(df)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing {filename}: {str(e)}")

    if not all_dfs:
        raise HTTPException(status_code=400, detail="No valid CSV files provided")

    # Combine and deduplicate
    if len(all_dfs) > 1:
        combined = pl.concat(all_dfs, how="vertical_relaxed")
        combined = combined.unique(subset=["date", "description", "amount"])
    else:
        combined = all_dfs[0]

    # Add temporary row index for preview purposes (real row_id assigned at categorize time)
    combined = combined.with_row_index("row_id")

    # Compute stats
    expense_total = float(combined.filter(pl.col("amount") < 0)["amount"].sum() or 0)
    income_total = float(combined.filter(pl.col("amount") > 0)["amount"].sum() or 0)
    dates = sorted(combined["date"].cast(pl.Utf8).to_list())
    date_range = f"{dates[0]} to {dates[-1]}" if dates else "N/A"

    stats = UploadStats(
        count=len(combined),
        date_range=date_range,
        income_total=income_total,
        expense_total=expense_total,
        format_name=format_name,
    )

    transactions = []
    for row in combined.to_dicts():
        amt = float(row.get("amount") or 0)
        transactions.append(Transaction(
            row_id=int(row.get("row_id", 0)),
            date=str(row.get("date", "")),
            description=str(row.get("description", "")),
            amount=amt,
            category=str(row.get("original_category") or "Uncategorized"),
            confidence=0.0,
            type="Income" if amt > 0 else "Expense",
            check_number=str(row["check_number"]) if row.get("check_number") else None,
            original_category=str(row["original_category"]) if row.get("original_category") else None,
        ))

    return UploadResponse(transactions=transactions, stats=stats)
