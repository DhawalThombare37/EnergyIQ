import { useState, useEffect } from 'react'
import { useData } from '../context/DataContext.jsx'
import { auditApi } from '../api.js'
import EmptyState from '../components/EmptyState.jsx'

export default function EnergyAudit() {
  const { dataLoaded } = useData()
  const [audit, setAudit] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!dataLoaded) return
    setLoading(true)
    auditApi.results()
      .then(res => setAudit(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [dataLoaded])

  if (!dataLoaded) return <EmptyState />
  if (loading || !audit) return <div style={{padding:'2rem'}}>Running Audit... <span className="spinner"/></div>

  const effColor = audit.efficiency_score >= 70 ? 'var(--green)' : audit.efficiency_score >= 50 ? 'var(--amber)' : 'var(--red)'

  return (
    <div>
      <div className="page-header fade-in">
        <h1 className="page-title">🔍 Energy Audit Report</h1>
        <p className="page-subtitle">Comprehensive energy efficiency analysis</p>
      </div>

      <div className="grid-1-2 fade-in" style={{animationDelay:'0.1s', marginBottom:'1.5rem'}}>
        <div className="glass-card" style={{display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center'}}>
          <div style={{fontSize:'1rem', fontWeight:700, color:'var(--text-muted)', marginBottom:'1rem', textTransform:'uppercase', letterSpacing:'0.1em'}}>Efficiency Score</div>
          <div style={{
            width:160, height:160, borderRadius:'50%', border:`12px solid ${effColor}`,
            display:'flex', alignItems:'center', justifyContent:'center',
            fontSize:'3.5rem', fontWeight:800, color: effColor, 
            boxShadow: `0 0 40px ${effColor}30`, marginBottom:'1rem'
          }}>
            {audit.efficiency_score}
          </div>
          <div style={{fontSize:'0.8rem', color:'var(--text-muted)'}}>/ 100</div>
        </div>

        <div className="glass-card">
          <div className="section-title">Audit Summary</div>
          <div className="grid-2">
            <div>
              <div className="stat-row"><span className="stat-label">Total kWh</span><span className="stat-value">{audit.total_kwh.toFixed(1)} kWh</span></div>
              <div className="stat-row"><span className="stat-label">Avg Daily kWh</span><span className="stat-value">{audit.avg_daily_kwh.toFixed(2)} kWh</span></div>
              <div className="stat-row"><span className="stat-label">Peak Day kWh</span><span className="stat-value">{audit.max_daily_kwh.toFixed(2)} kWh</span></div>
              <div className="stat-row"><span className="stat-label">Total Bill</span><span className="stat-value">₹{Math.round(audit.total_bill_slab)}</span></div>
            </div>
            <div>
              <div className="stat-row"><span className="stat-label">Std Dev</span><span className="stat-value">{audit.std_daily_kwh.toFixed(2)} kWh</span></div>
              <div className="stat-row"><span className="stat-label">Avg Daily Bill</span><span className="stat-value">₹{Math.round(audit.avg_daily_bill)}</span></div>
              <div className="stat-row"><span className="stat-label">High-Usage Days</span><span className="stat-value">{audit.high_consumption_days} (&gt;P95)</span></div>
              <div className="stat-row"><span className="stat-label">Days Analysed</span><span className="stat-value">{audit.total_days_analyzed}</span></div>
            </div>
          </div>
        </div>
      </div>

      <div className="fade-in" style={{animationDelay:'0.2s'}}>
        <h3 style={{fontSize:'1.1rem', marginBottom:'1rem'}}>🔎 Audit Findings</h3>
        {audit.findings.map((f, i) => (
          <div key={i} className={`rec-card ${f.severity}`}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
              <div className="rec-title" style={{marginBottom:0}}>
                {f.severity === 'HIGH' ? '🔴' : f.severity === 'MEDIUM' ? '🟡' : '🟢'} {f.text}
              </div>
              <span className={`badge badge-${f.severity}`}>{f.severity}</span>
            </div>
          </div>
        ))}
      </div>
      
      {audit.sub_metering_totals && Object.keys(audit.sub_metering_totals).length > 0 && (
        <div className="glass-card fade-in" style={{animationDelay:'0.3s', marginTop:'1.5rem'}}>
          <div className="section-title">🔌 Sub-Meter Breakdown (Wh)</div>
          <div className="grid-3">
             {Object.entries(audit.sub_metering_totals).map(([sub, val]) => (
               <div key={sub} style={{padding:'1rem', background:'var(--bg-glass-hover)', borderRadius:'8px'}}>
                 <div style={{fontSize:'0.8rem', color:'var(--text-muted)', marginBottom:'0.5rem'}}>{sub}</div>
                 <div style={{fontSize:'1.5rem', fontWeight:800, fontFamily:'JetBrains Mono, monospace'}}>{Math.round(val).toLocaleString()}</div>
               </div>
             ))}
          </div>
        </div>
      )}
    </div>
  )
}
