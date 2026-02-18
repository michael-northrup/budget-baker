import { useRef, useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { uploadCSV } from '../../api/client'
import { TransactionTable } from '../common/TransactionTable'

export function UploadStep() {
  const { setTransactions, setStep, setLoading, setError, isLoading, error, transactions, stats } =
    useAppStore()
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  async function handleFiles(files: File[]) {
    const csvs = files.filter((f) => f.name.endsWith('.csv'))
    if (!csvs.length) {
      setError('Please upload CSV files only.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const result = await uploadCSV(csvs)
      setTransactions(result.transactions, result.stats)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        🥣 Upload Your Transactions
      </h2>
      <p style={{ color: '#78716C', marginBottom: '1.5rem' }}>
        Upload one or more bank/credit union CSV files. Supported: AFCU, Chase, and generic formats.
      </p>

      {error && (
        <div className="error-banner" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div
        className="card"
        style={{
          border: `2px dashed ${dragOver ? '#D97706' : '#E8D5B0'}`,
          background: dragOver ? '#FFFBF0' : 'white',
          textAlign: 'center',
          cursor: 'pointer',
          padding: '3rem',
          transition: 'all 0.2s',
        }}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          handleFiles(Array.from(e.dataTransfer.files))
        }}
      >
        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📂</div>
        <p style={{ fontWeight: 600, color: '#292524' }}>Drop CSV files here or click to browse</p>
        <p style={{ fontSize: '0.85rem', color: '#78716C', marginTop: '0.4rem' }}>
          Max 10 MB per file · Multiple files supported
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          multiple
          style={{ display: 'none' }}
          onChange={(e) => handleFiles(Array.from(e.target.files ?? []))}
        />
      </div>

      {isLoading && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div className="spinner" style={{ width: 32, height: 32, margin: '0 auto 0.75rem' }} />
          <p style={{ color: '#78716C' }}>Parsing your transactions...</p>
        </div>
      )}

      {stats && (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-label">Transactions</div>
              <div className="stat-value">{stats.count}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Income</div>
              <div className="stat-value" style={{ color: '#16A34A' }}>
                +${stats.income_total.toFixed(2)}
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Expenses</div>
              <div className="stat-value">-${Math.abs(stats.expense_total).toFixed(2)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Date Range</div>
              <div className="stat-value" style={{ fontSize: '0.9rem' }}>
                {stats.date_range}
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Format</div>
              <div className="stat-value" style={{ fontSize: '1rem' }}>
                {stats.format_name}
              </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>
              Preview (first {Math.min(10, transactions.length)} transactions)
            </h3>
            <TransactionTable transactions={transactions.slice(0, 10)} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
            <button className="btn btn-primary" onClick={() => setStep(1)}>
              Start Baking →
            </button>
          </div>
        </>
      )}
    </div>
  )
}
