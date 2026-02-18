import type { Transaction, UploadResponse, CategorizeResponse } from '../types/transactions'

const BASE = '/api'

export async function uploadCSV(files: File[]): Promise<UploadResponse> {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail: string }).detail ?? 'Upload failed')
  }
  return res.json() as Promise<UploadResponse>
}

export async function categorize(
  transactions: Transaction[],
  use_ai: boolean,
): Promise<CategorizeResponse> {
  const res = await fetch(`${BASE}/categorize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transactions, use_ai }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail: string }).detail ?? 'Categorization failed')
  }
  return res.json() as Promise<CategorizeResponse>
}

export async function getCategories(): Promise<string[]> {
  const res = await fetch(`${BASE}/categories`)
  const data = (await res.json()) as { categories: string[] }
  return data.categories
}

export async function exportCSV(transactions: Transaction[]): Promise<Blob> {
  const res = await fetch(`${BASE}/export/csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transactions }),
  })
  if (!res.ok) throw new Error('CSV export failed')
  return res.blob()
}

export async function exportPDF(
  transactions: Transaction[],
  summary_stats: Record<string, number>,
): Promise<Blob> {
  const res = await fetch(`${BASE}/export/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transactions, summary_stats }),
  })
  if (!res.ok) throw new Error('PDF export failed')
  return res.blob()
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
