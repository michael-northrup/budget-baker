import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { Transaction } from '../../types/transactions'

interface Props {
  transactions: Transaction[]
}

export function CategoryBarChart({ transactions }: Props) {
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
        No data to display.
      </p>
    )
  }

  const maxVal = chartData[0]?.value ?? 1

  return (
    <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 36)}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 40 }}>
        <XAxis type="number" tickFormatter={(v: number) => `$${v}`} tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number) => [`$${v.toFixed(2)}`, 'Amount']} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {chartData.map((entry, i) => {
            const ratio = entry.value / maxVal
            // Interpolate from golden (#FCD34D) to amber (#D97706)
            const r = Math.round(252 - ratio * (252 - 217))
            const g = Math.round(211 - ratio * (211 - 119))
            const b = Math.round(77 - ratio * (77 - 6))
            return <Cell key={i} fill={`rgb(${r},${g},${b})`} />
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
