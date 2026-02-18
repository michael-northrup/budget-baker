import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import type { Transaction } from '../../types/transactions'

interface Props {
  transactions: Transaction[]
}

export function MonthlyTrendChart({ transactions }: Props) {
  const monthly: Record<string, { income: number; expenses: number }> = {}
  transactions.forEach((t) => {
    const month = t.date.substring(0, 7)
    if (!monthly[month]) monthly[month] = { income: 0, expenses: 0 }
    if (t.amount > 0) monthly[month].income += t.amount
    else monthly[month].expenses += Math.abs(t.amount)
  })

  const chartData = Object.entries(monthly)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, vals]) => ({
      month,
      Income: parseFloat(vals.income.toFixed(2)),
      Expenses: parseFloat(vals.expenses.toFixed(2)),
    }))

  if (chartData.length < 2) {
    return (
      <p style={{ textAlign: 'center', color: '#78716C', padding: '2rem' }}>
        Need at least 2 months of data for a trend chart.
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
        <defs>
          <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#16A34A" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#16A34A" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="expenseGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#D97706" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#D97706" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#E8D5B0" />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} />
        <YAxis tickFormatter={(v: number) => `$${v}`} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number) => `$${v.toFixed(2)}`} />
        <Legend />
        <Area
          type="monotone"
          dataKey="Income"
          stroke="#16A34A"
          fill="url(#incomeGrad)"
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="Expenses"
          stroke="#D97706"
          fill="url(#expenseGrad)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
