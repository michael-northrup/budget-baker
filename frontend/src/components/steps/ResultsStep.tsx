import { useState, useEffect, useMemo } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { getCategories } from '../../api/client'
import { ExpensePieChart } from '../charts/ExpensePieChart'
import { CategoryBarChart } from '../charts/CategoryBarChart'
import { MonthlyTrendChart } from '../charts/MonthlyTrendChart'
import { TransactionTable } from '../common/TransactionTable'
import type { Transaction } from '../../types/transactions'

export function ResultsStep() {
  const { categorized, editCategory, setStep } = useAppStore()
  const [categories, setCategories] = useState<string[]>([])
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [activeTab, setActiveTab] = useState<'charts' | 'table'>('charts')

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {})
  }, [])

  const filtered = useMemo<Transaction[]>(() => {
    return categorized.filter((t) => {
      if (startDate && t.date < startDate) return false
      if (endDate && t.date > endDate) return false
      return true
    })
  }, [categorized, startDate, endDate])

  const income = filtered.filter((t) => t.amount > 0).reduce((s, t) => s + t.amount, 0)
  const expenses = filtered.filter((t) => t.amount < 0).reduce((s, t) => s + Math.abs(t.amount), 0)
  const net = income - expenses
  const uncategorized = filtered.filter((t) => t.category === 'Uncategorized').length

  return (
    <div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>
        🍰 Review Your Results
      </h2>

      {/* Date filter */}
      <div
        className="card"
        style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}
      >
        <div>
          <label className="label">Start Date</label>
          <input
            className="input"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{ width: 160 }}
          />
        </div>
        <div>
          <label className="label">End Date</label>
          <input
            className="input"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{ width: 160 }}
          />
        </div>
        {(startDate || endDate) && (
          <button
            className="btn btn-secondary"
            onClick={() => {
              setStartDate('')
              setEndDate('')
            }}
          >
            Clear Filter
          </button>
        )}
      </div>

      {/* Summary stats */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Income</div>
          <div className="stat-value" style={{ color: '#16A34A' }}>
            +${income.toFixed(2)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Expenses</div>
          <div className="stat-value">-${expenses.toFixed(2)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Net</div>
          <div
            className="stat-value"
            style={{ color: net >= 0 ? '#16A34A' : '#DC2626' }}
          >
            {net >= 0 ? '+' : '-'}${Math.abs(net).toFixed(2)}
          </div>
        </div>
        {uncategorized > 0 && (
          <div className="stat-card" style={{ borderLeft: '3px solid #D97706' }}>
            <div className="stat-label">Uncategorized</div>
            <div className="stat-value" style={{ color: '#D97706' }}>
              {uncategorized}
            </div>
          </div>
        )}
      </div>

      {/* Tab toggle */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button
          className={`btn ${activeTab === 'charts' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('charts')}
        >
          Charts
        </button>
        <button
          className={`btn ${activeTab === 'table' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('table')}
        >
          Transactions
        </button>
      </div>

      {activeTab === 'charts' && (
        <>
          <div className="card">
            <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Spending by Category</h3>
            <ExpensePieChart transactions={filtered} />
          </div>
          <div className="card">
            <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Category Totals</h3>
            <CategoryBarChart transactions={filtered} />
          </div>
          <div className="card">
            <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Monthly Trend</h3>
            <MonthlyTrendChart transactions={filtered} />
          </div>
        </>
      )}

      {activeTab === 'table' && (
        <div className="card">
          <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>
            Transactions ({filtered.length})
          </h3>
          <TransactionTable
            transactions={filtered}
            editable
            categories={categories}
            onEdit={editCategory}
          />
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
        <button className="btn btn-secondary" onClick={() => setStep(1)}>
          ← Back
        </button>
        <button className="btn btn-primary" onClick={() => setStep(3)}>
          Download & Export →
        </button>
      </div>
    </div>
  )
}
