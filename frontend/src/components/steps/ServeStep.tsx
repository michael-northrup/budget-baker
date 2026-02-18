import { useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { exportCSV, exportPDF, downloadBlob } from '../../api/client'

export function ServeStep() {
  const { categorized, setStep } = useAppStore()
  const [loadingCSV, setLoadingCSV] = useState(false)
  const [loadingPDF, setLoadingPDF] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const income = categorized.filter((t) => t.amount > 0).reduce((s, t) => s + t.amount, 0)
  const expenses = categorized
    .filter((t) => t.amount < 0)
    .reduce((s, t) => s + Math.abs(t.amount), 0)
  const summary_stats = {
    income,
    expenses,
    net: income - expenses,
    count: categorized.length,
  }

  async function handleCSV() {
    setLoadingCSV(true)
    setError(null)
    try {
      const blob = await exportCSV(categorized)
      downloadBlob(blob, 'budget_baker_export.csv')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setLoadingCSV(false)
    }
  }

  async function handlePDF() {
    setLoadingPDF(true)
    setError(null)
    try {
      const blob = await exportPDF(categorized, summary_stats)
      downloadBlob(blob, 'budget_baker_report.pdf')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'PDF export failed')
    } finally {
      setLoadingPDF(false)
    }
  }

  return (
    <div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        🧁 Serve Your Report
      </h2>
      <p style={{ color: '#78716C', marginBottom: '1.5rem' }}>
        {categorized.length} categorized transactions ready to export.
      </p>

      {error && (
        <div className="error-banner" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div
        style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}
      >
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📊</div>
          <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>CSV Export</h3>
          <p style={{ fontSize: '0.85rem', color: '#78716C', marginBottom: '1.25rem' }}>
            All transactions with categories, confidence scores, and type labels.
          </p>
          <button
            className="btn btn-primary"
            onClick={handleCSV}
            disabled={loadingCSV}
            style={{ width: '100%' }}
          >
            {loadingCSV ? (
              <>
                <span className="spinner" /> Exporting...
              </>
            ) : (
              '⬇ Download CSV'
            )}
          </button>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📄</div>
          <h3 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>PDF Report</h3>
          <p style={{ fontSize: '0.85rem', color: '#78716C', marginBottom: '1.25rem' }}>
            Summary stats, charts, and transaction details in a professional report.
          </p>
          <button
            className="btn btn-primary"
            onClick={handlePDF}
            disabled={loadingPDF}
            style={{ width: '100%' }}
          >
            {loadingPDF ? (
              <>
                <span className="spinner" /> Generating PDF...
              </>
            ) : (
              '⬇ Download PDF'
            )}
          </button>
        </div>
      </div>

      <div
        className="card"
        style={{ background: '#F0FDF4', border: '1px solid #BBF7D0' }}
      >
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
          <span style={{ fontSize: '1.25rem' }}>🔒</span>
          <div>
            <strong>Privacy reminder</strong>
            <p style={{ fontSize: '0.85rem', color: '#166534', marginTop: '0.25rem' }}>
              No transaction data has been stored on the server. All processing happened in your
              browser session. Refreshing this page will clear your data.
            </p>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <button className="btn btn-secondary" onClick={() => setStep(2)}>
          ← Back to Results
        </button>
      </div>
    </div>
  )
}
