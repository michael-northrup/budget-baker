import { useState } from 'react'
import type { Transaction } from '../../types/transactions'

interface Props {
  transactions: Transaction[]
  editable?: boolean
  categories?: string[]
  onEdit?: (row_id: number, category: string) => void
  maxRows?: number
}

function fmtAmount(amount: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(Math.abs(amount))
}

export function TransactionTable({ transactions, editable, categories, onEdit, maxRows }: Props) {
  const [page, setPage] = useState(0)
  const pageSize = maxRows ?? 20
  const total = transactions.length
  const paged = transactions.slice(page * pageSize, (page + 1) * pageSize)

  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th style={{ textAlign: 'right' }}>Amount</th>
              <th>Category</th>
              <th>Type</th>
              {!editable && <th>Confidence</th>}
            </tr>
          </thead>
          <tbody>
            {paged.map((t) => (
              <tr key={t.row_id}>
                <td style={{ whiteSpace: 'nowrap' }}>{t.date}</td>
                <td
                  style={{
                    maxWidth: 260,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {t.description}
                </td>
                <td
                  style={{
                    textAlign: 'right',
                    fontWeight: 600,
                    color: t.amount > 0 ? '#16A34A' : '#292524',
                  }}
                >
                  {t.amount > 0 ? '+' : '-'}
                  {fmtAmount(t.amount)}
                </td>
                <td>
                  {editable && categories && onEdit ? (
                    <select
                      value={t.category}
                      onChange={(e) => onEdit(t.row_id, e.target.value)}
                    >
                      {categories.map((c) => (
                        <option key={c}>{c}</option>
                      ))}
                    </select>
                  ) : (
                    t.category
                  )}
                </td>
                <td>
                  <span className={`badge badge-${t.type.toLowerCase()}`}>{t.type}</span>
                </td>
                {!editable && (
                  <td
                    style={{
                      color: t.confidence < 0.7 ? '#D97706' : '#78716C',
                      fontSize: '0.8rem',
                    }}
                  >
                    {(t.confidence * 100).toFixed(0)}%
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > pageSize && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '0.5rem',
            marginTop: '1rem',
          }}
        >
          <button
            className="btn btn-secondary"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Prev
          </button>
          <span style={{ padding: '0.6rem', fontSize: '0.85rem', color: '#78716C' }}>
            {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}
          </span>
          <button
            className="btn btn-secondary"
            disabled={(page + 1) * pageSize >= total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
