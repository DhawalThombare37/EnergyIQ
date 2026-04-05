import axios from 'axios'

let baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
// If it's a raw service name (like 'energyiq-backend'), turn it into a full Render URL
if (baseURL && !baseURL.startsWith('http') && !baseURL.startsWith('/')) {
  baseURL = `https://${baseURL}.onrender.com/api`
}
const api = axios.create({ baseURL })

export default api

// ── Data ──────────────────────────────────────────────────────
export const dataApi = {
  status:      () => api.get('/data/status'),
  loadDefault: () => api.post('/data/load-default'),
  uploadCsv:   (file) => {
    const fd = new FormData(); fd.append('file', file)
    return api.post('/data/upload', fd)
  },
  summary:       () => api.get('/data/summary'),
  daily:         (limit=500) => api.get(`/data/daily?limit=${limit}`),
  raw:           (limit=200) => api.get(`/data/raw?limit=${limit}`),
  stats:         () => api.get('/data/stats'),
  hourlyProfile: () => api.get('/data/hourly-profile'),
}

// ── Predictions ────────────────────────────────────────────────
export const predictApi = {
  status:  () => api.get('/predictions/status'),
  run:     (train_days, pred_days) => api.post('/predictions/run', { train_days, pred_days }),
  results: () => api.get('/predictions/results'),
}

// ── Billing ────────────────────────────────────────────────────
export const billingApi = {
  projection:  () => api.get('/billing/projection'),
  breakdown:   () => api.get('/billing/breakdown'),
  savings:     (monthly_kwh, shift_pct) => api.post('/billing/savings-calculator', { monthly_kwh, shift_pct }),
}

// ── Audit ──────────────────────────────────────────────────────
export const auditApi = {
  run:             () => api.post('/audit/run'),
  results:         () => api.get('/audit/results'),
  peakHours:       () => api.get('/audit/peak-hours'),
  efficiencyScore: () => api.get('/audit/efficiency-score'),
}

// ── Advisor ────────────────────────────────────────────────────
export const advisorApi = {
  recommendations: () => api.get('/advisor/recommendations'),
}

// ── Chat ───────────────────────────────────────────────────────
export const chatApi = {
  status:          () => api.get('/chat/status'),
  quickSuggestions:() => api.get('/chat/quick-suggestions'),
  send:            (message, model='llama-3.1-8b-instant') => api.post('/chat/send', { message, model }),
}

// ── RAG ────────────────────────────────────────────────────────
export const ragApi = {
  status:    () => api.get('/rag/status'),
  uploadPdf: (file) => {
    const fd = new FormData(); fd.append('file', file)
    return api.post('/rag/upload', fd)
  },
  ask:   (question, model='llama-3.1-8b-instant') => api.post('/rag/ask', { question, model }),
  clear: () => api.delete('/rag/clear'),
}
