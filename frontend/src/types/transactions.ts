export interface Transaction {
  row_id: number
  date: string
  description: string
  amount: number
  category: string
  confidence: number
  type: 'Income' | 'Expense' | 'Transfer'
  check_number?: string
  original_category?: string
}

export interface UploadStats {
  count: number
  date_range: string
  income_total: number
  expense_total: number
  format_name: string
}

export interface UploadResponse {
  transactions: Transaction[]
  stats: UploadStats
}

export interface CategorizeResponse {
  transactions: Transaction[]
  summary: Array<{ category: string; count: number; total: number; average: number }>
}

export type AppStep = 0 | 1 | 2 | 3

export const STEP_LABELS = ['Upload', 'Bake', 'Results', 'Serve']
export const STEP_ICONS = ['🥣', '🔥', '🍰', '🧁']
