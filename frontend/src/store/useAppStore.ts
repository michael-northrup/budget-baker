import { create } from 'zustand'
import type { Transaction, UploadStats, AppStep } from '../types/transactions'

interface AppState {
  step: AppStep
  transactions: Transaction[]
  categorized: Transaction[]
  stats: UploadStats | null
  useAI: boolean
  isLoading: boolean
  error: string | null

  setStep: (s: AppStep) => void
  setTransactions: (t: Transaction[], stats: UploadStats) => void
  setCategorized: (t: Transaction[]) => void
  editCategory: (row_id: number, category: string) => void
  setUseAI: (v: boolean) => void
  setLoading: (v: boolean) => void
  setError: (e: string | null) => void
  reset: () => void
}

export const useAppStore = create<AppState>((set) => ({
  step: 0,
  transactions: [],
  categorized: [],
  stats: null,
  useAI: false,
  isLoading: false,
  error: null,

  setStep: (step) => set({ step }),
  setTransactions: (transactions, stats) => set({ transactions, stats }),
  setCategorized: (categorized) => set({ categorized }),
  editCategory: (row_id, category) =>
    set((state) => ({
      categorized: state.categorized.map((t) =>
        t.row_id === row_id ? { ...t, category } : t,
      ),
    })),
  setUseAI: (useAI) => set({ useAI }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      step: 0,
      transactions: [],
      categorized: [],
      stats: null,
      useAI: false,
      isLoading: false,
      error: null,
    }),
}))
