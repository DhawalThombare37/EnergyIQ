import { useState, useEffect } from 'react'
import { useData } from '../context/DataContext.jsx'
import { advisorApi } from '../api.js'
import EmptyState from '../components/EmptyState.jsx'
import KpiCard from '../components/KpiCard.jsx'

export default function OptimizationAdvisor() {
  const { dataLoaded } = useData()
  const [recs, setRecs] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState(['HIGH', 'MEDIUM', 'LOW'])

  useEffect(() => {
    if (!dataLoaded) return
    setLoading(true)
    advisorApi.recommendations()
      .then(res => setRecs(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [dataLoaded])

  if (!dataLoaded) return <EmptyState />
  if (loading || recs.length === 0) return <div style={{padding:'2rem'}}>Generating recommendations... <span className="spinner"/></div>

  const n_h = recs.filter(r => r.priority === 'HIGH').length
  const n_m = recs.filter(r => r.priority === 'MEDIUM').length
  const n_l = recs.filter(r => r.priority === 'LOW').length

  function toggleFilter(lvl) {
    if (filter.includes(lvl)) setFilter(filter.filter(f => f !== lvl))
    else setFilter([...filter, lvl])
  }

  return (
    <div>
      <div className="page-header fade-in">
        <h1 className="page-title">💡 Optimization Advisor</h1>
        <p className="page-subtitle">Actionable recommendations to cut your energy bills</p>
      </div>

      <div className="kpi-grid kpi-grid-4 fade-in" style={{animationDelay:'0.1s'}}>
        <KpiCard title="Total Tips" value={recs.length} sub="" icon="💡" />
        <KpiCard title="High Priority" value={n_h} sub="Act now" icon="🔴" color="var(--red)" />
        <KpiCard title="Med Priority" value={n_m} sub="Plan soon" icon="🟡" color="var(--amber)" />
        <KpiCard title="Low Priority" value={n_l} sub="Long term" icon="🟢" color="var(--green)" />
      </div>

      <div className="filter-chips fade-in" style={{animationDelay:'0.2s'}}>
        <button className={`filter-chip ${filter.includes('HIGH') ? 'selected-HIGH' : ''}`} onClick={() => toggleFilter('HIGH')}>HIGH Priority</button>
        <button className={`filter-chip ${filter.includes('MEDIUM') ? 'selected-MEDIUM' : ''}`} onClick={() => toggleFilter('MEDIUM')}>MEDIUM Priority</button>
        <button className={`filter-chip ${filter.includes('LOW') ? 'selected-LOW' : ''}`} onClick={() => toggleFilter('LOW')}>LOW Priority</button>
      </div>

      <div className="fade-in" style={{animationDelay:'0.3s'}}>
        {recs.filter(r => filter.includes(r.priority)).map((rec, i) => (
          <div key={i} className={`rec-card ${rec.priority}`}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'0.5rem'}}>
              <div className="rec-title" style={{marginBottom:0}}>{rec.icon} {rec.title}</div>
              <span className={`badge badge-${rec.priority}`}>{rec.priority}</span>
            </div>
            <div className="rec-detail">{rec.detail}</div>
            <div style={{marginTop:'0.75rem', fontSize:'0.75rem', color:'var(--text-muted)'}}>
              <span title="Estimated Savings">💰 Est. Savings: </span>
              <strong style={{
                color: rec.priority==='HIGH' ? '#fca5a5' : rec.priority==='MEDIUM' ? '#fcd34d' : '#6ee7b7'
              }}>{rec.saving_est}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
