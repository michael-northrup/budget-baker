from pydantic import BaseModel
from typing import Optional


class Transaction(BaseModel):
    row_id: int
    date: str
    description: str
    amount: float
    category: str = "Uncategorized"
    confidence: float = 0.0
    type: str = "Expense"
    check_number: Optional[str] = None
    original_category: Optional[str] = None


class UploadStats(BaseModel):
    count: int
    date_range: str
    income_total: float
    expense_total: float
    format_name: str


class UploadResponse(BaseModel):
    transactions: list[Transaction]
    stats: UploadStats


class CategorizeRequest(BaseModel):
    transactions: list[dict]
    use_ai: bool = False


class CategorizeResponse(BaseModel):
    transactions: list[Transaction]
    summary: list[dict]  # [{category, count, total, average}, ...]


class ExportPdfRequest(BaseModel):
    transactions: list[dict]
    summary_stats: dict  # {income, expenses, net, count}
