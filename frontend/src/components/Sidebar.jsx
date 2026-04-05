import { useState } from 'react'
import { dataApi } from '../api.js'
import { useData } from '../context/DataContext.jsx'

const NAV_ITEMS = [
  { id: 'dashboard',   icon: '🏠', label: 'Dashboard' },
  { id: 'explorer',    icon: '📤', label: 'Data Explorer' },
  { id: 'predictions', icon: '🔮', label: 'Prediction Engine' },
  { id: 'billing',     icon: '💰', label: 'Bill Estimator' },
  { id: 'audit',       icon: '🔍', label: 'Energy Audit' },
  { id: 'advisor',     icon: '💡', label: 'Optimization Advisor' },
  { id: 'rag',         icon: '📄', label: 'PDF RAG Chatbot' },
]

export default function Sidebar({ activePage, onNavigate }) {
  const { dataLoaded, setDataLoaded, setDataInfo, dataInfo } = useData()
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const [success, setSuccess]   = useState('')
  const [useDefault, setUseDefault] = useState(true)
  const [file, setFile]         = useState(null)

  async function handleLoad() {
    setLoading(true); setError(''); setSuccess('')
    try {
      let res
      if (useDefault) {
        res = await dataApi.loadDefault()
      } else {
        if (!file) { setError('Select a CSV file first.'); setLoading(false); return }
        res = await dataApi.uploadCsv(file)
      }
      setDataLoaded(true)
      setDataInfo({ records: res.data.records, days: res.data.days })
      setSuccess(`✓ ${res.data.records.toLocaleString()} records · ${res.data.days} days loaded`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <span className="logo-icon">✨</span>
        <span className="logo-name">NexusAI</span>
        <span className="logo-sub">Multi-purpose Intelligence Engine</span>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {NAV_ITEMS.map(item => (
          <div
            key={item.id}
            className={`nav-item${activePage === item.id ? ' active' : ''}${item.isNew ? ' new-badge' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </div>
        ))}
      </nav>

      {/* Data Source */}
      <div className="sidebar-data">
        <div className="nav-section-label" style={{ paddingBottom:'0.5rem' }}>📁 Data Source</div>

        <label style={{ display:'flex', alignItems:'center', gap:'0.5rem', fontSize:'0.8rem',
          color:'var(--text-secondary)', cursor:'pointer', marginBottom:'0.6rem' }}>
          <input
            type="checkbox"
            checked={useDefault}
            onChange={e => setUseDefault(e.target.checked)}
            style={{ accentColor:'var(--cyan)' }}
          />
          Use bundled dataset
        </label>

        {!useDefault && (
          <input
            type="file" accept=".csv"
            onChange={e => setFile(e.target.files[0])}
            style={{ fontSize:'0.75rem', color:'var(--text-muted)', marginBottom:'0.6rem', width:'100%' }}
          />
        )}

        <button
          className="btn btn-primary"
          style={{ width:'100%', justifyContent:'center', marginBottom:'0.5rem' }}
          onClick={handleLoad}
          disabled={loading}
        >
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Loading…</> : '⚡ Load & Process Data'}
        </button>

        {error   && <div className="alert alert-error"   style={{padding:'0.5rem 0.7rem',fontSize:'0.72rem'}}>{error}</div>}
        {success && <div className="alert alert-success" style={{padding:'0.5rem 0.7rem',fontSize:'0.72rem'}}>{success}</div>}

        {dataLoaded && dataInfo && (
          <div className="data-status-card" style={{ marginTop:'0.5rem' }}>
            <span className="label">Dataset Loaded</span>
            <span className="value">{dataInfo.records?.toLocaleString()} records · {dataInfo.days} days</span>
          </div>
        )}
      </div>
    </aside>
  )
}
