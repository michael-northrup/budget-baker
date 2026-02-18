import { useAppStore } from '../../store/useAppStore'
import { categorize as categorizeAPI } from '../../api/client'

export function BakeStep() {
  const {
    transactions,
    setCategorized,
    setStep,
    useAI,
    setUseAI,
    isLoading,
    setLoading,
    error,
    setError,
  } = useAppStore()

  async function handleBake() {
    setError(null)
    setLoading(true)
    try {
      const result = await categorizeAPI(transactions, useAI)
      setCategorized(result.transactions)
      setStep(2)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Categorization failed')
    } finally {
      setLoading(false)
    }
  }

  const uncategorizedCount = transactions.filter(
    (t) => !t.category || t.category === 'Uncategorized',
  ).length

  return (
    <div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        🔥 Bake Your Transactions
      </h2>
      <p style={{ color: '#78716C', marginBottom: '1.5rem' }}>
        {transactions.length} transactions loaded.{' '}
        {uncategorizedCount > 0 && `${uncategorizedCount} may benefit from AI enhancement.`}
      </p>

      {error && (
        <div className="error-banner" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      <div className="card">
        <h3 style={{ fontWeight: 600, marginBottom: '1rem' }}>Categorization Options</h3>

        <label
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
            cursor: 'pointer',
            padding: '1rem',
            borderRadius: '8px',
            border: '1px solid',
            borderColor: useAI ? '#D97706' : '#E8D5B0',
            background: useAI ? '#FFFBF0' : 'white',
            marginBottom: useAI ? '1rem' : '0',
          }}
        >
          <input
            type="checkbox"
            checked={useAI}
            onChange={(e) => setUseAI(e.target.checked)}
            style={{ marginTop: 3 }}
          />
          <div>
            <div style={{ fontWeight: 600 }}>AI Enhancement (Databricks)</div>
            <div style={{ fontSize: '0.85rem', color: '#78716C', marginTop: '0.25rem' }}>
              Categorizes ambiguous transactions (confidence &lt; 70%). Only merchant names are
              sent — amounts stay private.
            </div>
          </div>
        </label>

      </div>

      <div
        style={{ display: 'flex', gap: '0.75rem', justifyContent: 'space-between', marginTop: '1rem' }}
      >
        <button className="btn btn-secondary" onClick={() => setStep(0)}>
          ← Back
        </button>
        <button className="btn btn-primary" onClick={handleBake} disabled={isLoading}>
          {isLoading ? (
            <>
              <span className="spinner" /> Baking...
            </>
          ) : (
            '🔥 Bake It!'
          )}
        </button>
      </div>
    </div>
  )
}
