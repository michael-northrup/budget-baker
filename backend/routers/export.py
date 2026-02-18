from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import polars as pl

from modules.export import export_to_csv, export_to_pdf
from modules.visualizations import create_expense_pie_chart, create_category_bar_chart
from ..models.schemas import ExportPdfRequest

router = APIRouter()


def _build_df(transactions: list) -> pl.DataFrame:
    """Build a Polars DataFrame from the JSON transaction list, restoring proper types."""
    df = pl.DataFrame(transactions)
    # Dates arrive as strings from JSON — cast back to Date
    if df["date"].dtype == pl.Utf8:
        df = df.with_columns(pl.col("date").str.to_date("%Y-%m-%d"))
    # Ensure optional columns exist
    if "check_number" not in df.columns:
        df = df.with_columns(pl.lit(None).cast(pl.Utf8).alias("check_number"))
    if "original_category" not in df.columns:
        df = df.with_columns(pl.lit(None).cast(pl.Utf8).alias("original_category"))
    return df


@router.post("/export/csv")
async def export_csv(request: dict):
    """Export transactions as a CSV file download."""
    try:
        df = _build_df(request["transactions"])
        csv_bytes = export_to_csv(df)
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=budget_baker_export.csv"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/pdf")
async def export_pdf(request: ExportPdfRequest):
    """Export transactions as a PDF report with charts."""
    try:
        df = _build_df(request.transactions)

        # Generate Plotly charts for embedding in PDF
        pie_chart = create_expense_pie_chart(df)
        bar_chart = create_category_bar_chart(df)

        pdf_bytes = export_to_pdf(df, request.summary_stats, pie_chart, bar_chart)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=budget_baker_report.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
