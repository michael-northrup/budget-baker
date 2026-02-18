import type { AppStep } from '../../types/transactions'
import { STEP_LABELS, STEP_ICONS } from '../../types/transactions'

interface Props {
  current: AppStep
  maxReached: AppStep
  onNavigate: (s: AppStep) => void
}

export function ProgressSteps({ current, maxReached, onNavigate }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem' }}>
      {STEP_LABELS.map((label, i) => {
        const step = i as AppStep
        const isComplete = i < current
        const isCurrent = i === current
        const isAccessible = i <= maxReached
        return (
          <div key={i} style={{ display: 'flex', alignItems: 'center', flex: i < 3 ? 1 : 'none' }}>
            <button
              onClick={() => isAccessible && onNavigate(step)}
              disabled={!isAccessible}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                background: 'none',
                border: 'none',
                cursor: isAccessible ? 'pointer' : 'default',
                padding: '0.5rem',
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  background: isComplete || isCurrent ? '#D97706' : '#E8D5B0',
                  color: isComplete || isCurrent ? 'white' : '#92867A',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.1rem',
                  fontWeight: 700,
                  border: isCurrent ? '3px solid #B45309' : '3px solid transparent',
                  transition: 'all 0.2s',
                }}
              >
                {isComplete ? '✓' : STEP_ICONS[i]}
              </div>
              <span
                style={{
                  fontSize: '0.78rem',
                  marginTop: '0.3rem',
                  fontWeight: isCurrent ? 700 : 400,
                  color: isCurrent ? '#D97706' : '#78716C',
                }}
              >
                {label}
              </span>
            </button>
            {i < 3 && (
              <div
                style={{
                  flex: 1,
                  height: 2,
                  background: i < current ? '#D97706' : '#E8D5B0',
                  margin: '0 0.25rem',
                  marginBottom: '1.4rem',
                }}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
