import { useCallback } from 'react'
import { useAppStore } from './store/useAppStore'
import { ProgressSteps } from './components/common/ProgressSteps'
import { UploadStep } from './components/steps/UploadStep'
import { BakeStep } from './components/steps/BakeStep'
import { ResultsStep } from './components/steps/ResultsStep'
import { ServeStep } from './components/steps/ServeStep'
import type { AppStep } from './types/transactions'

function App() {
  const { step, setStep, categorized, transactions } = useAppStore()

  const maxReached: AppStep = (() => {
    if (categorized.length > 0) return 3
    if (transactions.length > 0) return 1
    return 0
  })()

  const navigate = useCallback(
    (s: AppStep) => {
      if (s <= maxReached) setStep(s)
    },
    [maxReached, setStep],
  )

  return (
    <div className="app-container">
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#D97706' }}>🍞 Budget Baker</h1>
        <p style={{ color: '#78716C', fontSize: '0.9rem' }}>
          Privacy-first transaction analysis · No data stored
        </p>
      </header>

      <ProgressSteps current={step} maxReached={maxReached} onNavigate={navigate} />

      <main>
        {step === 0 && <UploadStep />}
        {step === 1 && <BakeStep />}
        {step === 2 && <ResultsStep />}
        {step === 3 && <ServeStep />}
      </main>
    </div>
  )
}

export default App
