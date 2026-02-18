import { useState, useEffect, useCallback } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { categorize as categorizeAPI, getCategories } from '../../api/client'
import type { Transaction } from '../../types/transactions'

const BAKING_EMOJIS = ['🍪', '🧁', '🎂', '🍰', '🥐', '🥧', '🍩', '🧆']

const PARTICLES = Array.from({ length: 35 }, (_, i) => ({
  id: i,
  emoji: BAKING_EMOJIS[i % BAKING_EMOJIS.length],
  left: (i * 2.9 + Math.sin(i) * 15 + 50) % 100,
  delay: (i * 0.08) % 1.8,
  duration: 1.6 + (i % 5) * 0.28,
  size: 1.1 + (i % 4) * 0.25,
}))

function BakingCelebration({ onDone }: { onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2800)
    return () => clearTimeout(t)
  }, [onDone])

  return (
    <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 999, overflow: 'hidden' }}>
      {PARTICLES.map((p) => (
        <span
          key={p.id}
          style={{
            position: 'absolute',
            left: `${p.left}%`,
            top: '-60px',
            fontSize: `${p.size}rem`,
            animation: `bakeFall ${p.duration}s ${p.delay}s ease-in forwards`,
            display: 'inline-block',
          }}
        >
          {p.emoji}
        </span>
      ))}
    </div>
  )
}

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

  const [showCelebration, setShowCelebration] = useState(false)
  const [reviewItems, setReviewItems] = useState<Transaction[] | null>(null)
  const [allCategorized, setAllCategorized] = useState<Transaction[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [manualCategories, setManualCategories] = useState<Record<number, string>>({})

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {})
  }, [])

  async function handleBake() {
    setError(null)
    setLoading(true)
    try {
      const result = await categorizeAPI(transactions, useAI)
      setAllCategorized(result.transactions)
      setShowCelebration(true)

      const uncategorized = result.transactions.filter((t) => t.category === 'Uncategorized')
      if (uncategorized.length > 0) {
        const initial: Record<number, string> = {}
        uncategorized.forEach((t) => { initial[t.row_id] = 'Uncategorized' })
        setManualCategories(initial)
        setReviewItems(uncategorized)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Categorization failed')
    } finally {
      setLoading(false)
    }
  }

  const handleCelebrationDone = useCallback(() => {
    setShowCelebration(false)
    // If no uncategorized items, proceed directly
    if (!reviewItems || reviewItems.length === 0) {
      setCategorized(allCategorized)
      setStep(2)
    }
  }, [reviewItems, allCategorized, setCategorized, setStep])

  function handleManualCategoryChange(row_id: number, category: string) {
    setManualCategories((prev) => ({ ...prev, [row_id]: category }))
  }

  function handleReviewDone() {
    const updated = allCategorized.map((t) =>
      manualCategories[t.row_id] !== undefined
        ? { ...t, category: manualCategories[t.row_id], confidence: 1.0 }
        : t
    )
    setCategorized(updated)
    setStep(2)
  }

  // Review panel: shown after celebration if uncategorized items exist
  if (reviewItems && !showCelebration) {
    return (
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          🤔 A Few Need Your Help
        </h2>
        <p style={{ color: '#78716C', marginBottom: '1.5rem' }}>
          {reviewItems.length} transaction{reviewItems.length !== 1 ? 's' : ''} couldn't be
          categorized automatically. Assign a category or leave as Uncategorized.
        </p>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th style={{ textAlign: 'right' }}>Amount</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              {reviewItems.map((t) => (
                <tr key={t.row_id}>
                  <td style={{ whiteSpace: 'nowrap' }}>{t.date}</td>
                  <td
                    style={{
                      maxWidth: 280,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={t.description}
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
                    {t.amount > 0 ? '+' : '-'}${Math.abs(t.amount).toFixed(2)}
                  </td>
                  <td>
                    <select
                      value={manualCategories[t.row_id] ?? 'Uncategorized'}
                      onChange={(e) => handleManualCategoryChange(t.row_id, e.target.value)}
                    >
                      {categories.map((c) => (
                        <option key={c}>{c}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button className="btn btn-primary" onClick={handleReviewDone}>
            Looks Good! →
          </button>
        </div>
      </div>
    )
  }

  const uncategorizedCount = transactions.filter(
    (t) => !t.category || t.category === 'Uncategorized',
  ).length

  return (
    <div>
      {showCelebration && <BakingCelebration onDone={handleCelebrationDone} />}

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
