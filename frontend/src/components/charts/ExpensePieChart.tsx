import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { Transaction } from '../../types/transactions'

const COLORS = [
  '#D97706', '#EA580C', '#DC2626', '#CA8A04', '#92400E',
  '#B45309', '#F59E0B', '#FBBF24', '#F97316', '#EF4444',
  '#A16207', '#78350F',
]

interface Props {
  transactions: Transaction[]
}

export function ExpensePieChart({ transactions }: Props) {
  const data: Record<string, number> = {}
  transactions
    .filter((t) => t.type === 'Expense')
    .forEach((t) => {
      data[t.category] = (data[t.category] ?? 0) + Math.abs(t.amount)
    })

  const chartData = Object.entries(data)
    .sort(([, a], [, b]) => b - a)
    .map(([name, value]) => ({ name, value: parseFloat(value.toFixed(2)) }))

  if (chartData.length === 0) {
    return (
      <p style={{ textAlign: 'center', color: '#78716C', padding: '2rem' }}>
        No expense data to display.
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={320}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={70}
          outerRadius={130}
          paddingAngle={2}
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(v: number) => `$${v.toFixed(2)}`} />
        <Legend layout="vertical" align="right" verticalAlign="middle" iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  )
}
