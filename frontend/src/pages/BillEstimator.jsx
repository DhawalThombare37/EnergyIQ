import { useState, useEffect } from 'react'
import { useData } from '../context/DataContext.jsx'
import { billingApi } from '../api.js'
import EmptyState from '../components/EmptyState.jsx'
import KpiCard from '../components/KpiCard.jsx'
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar, Cell } from 'recharts'

export default function BillEstimator() {
  const { dataLoaded } = useData()
  const [proj, setProj] = useState(null)
  const [bd, setBd] = useState([])
  const [loading, setLoading] = useState(false)
  
  // Savings calc
  const [shiftKwh, setShiftKwh] = useState(0)
  const [shiftPct, setShiftPct] = useState(20)
  const [savingResult, setSavingResult] = useState(null)

  useEffect(() => {
    if (!dataLoaded) return
    setLoading(true)
    Promise.all([
      billingApi.projection(),
      billingApi.breakdown()
    ])
    .then(([pRes, bRes]) => {
      setProj(pRes.data)
      setBd(bRes.data)
      setShiftKwh(pRes.data.total_kwh)
      calculateSavings(pRes.data.total_kwh, shiftPct)
    })
    .finally(() => setLoading(false))
  }, [dataLoaded])

  function calculateSavings(kwh, pct) {
    billingApi.savings(kwh, pct).then(res => setSavingResult(res.data)).catch(console.error)
  }

  function handleShiftChange(e) {
    const p = parseInt(e.target.value)
    setShiftPct(p)
    calculateSavings(shiftKwh, p)
  }

  if (!dataLoaded) return <EmptyState />
  if (loading || !proj || typeof proj.slab_bill_total === 'undefined') return <div style={{padding:'2rem'}}>Loading... <span className="spinner"/></div>

  const diff = (proj.slab_bill_total || 0) - (proj.tou_bill_total || 0)
  const saveLabel = diff < 0 ? 'TOU Saves' : 'Slab Saves'
  const saveColor = Math.abs(diff) > 0 ? 'var(--green)' : 'var(--text-muted)'

  const barData = (proj.dates || []).map((d, i) => ({
    date: new Date(d).toLocaleDateString('en-GB'),
    kwh: proj.kwh_series?.[i] || 0,
    bill: proj.bill_series?.[i] || 0
  }))

  return (
    <div>
      <div className="page-header fade-in">
        <h1 className="page-title">💰 Bill Estimator</h1>
        <p className="page-subtitle">TOU vs Slab comparison and 30-day projections</p>
      </div>

      <div className="kpi-grid kpi-grid-4 fade-in" style={{animationDelay:'0.1s'}}>
        <KpiCard title="Projected kWh" value={`${(proj.total_kwh || 0).toFixed(1)}`} sub="30 days" icon="⚡" />
        <KpiCard title="Slab Bill (30d)" value={`₹${Math.round(proj.slab_bill_total || 0)}`} sub="Estimated" icon="🧮" color="var(--purple)" />
        <KpiCard title="TOU Bill (30d)" value={`₹${Math.round(proj.tou_bill_total || 0)}`} sub="Estimated" icon="🕐" color="var(--amber)" />
        <KpiCard title={saveLabel} value={`₹${Math.round(Math.abs(diff))}`} sub="Over 30 days" icon="💡" color={saveColor} />
      </div>

      <div className="grid-2 fade-in" style={{animationDelay:'0.2s', marginBottom:'1.5rem'}}>
        {bd.length > 0 && (
          <div className="chart-wrapper" style={{marginBottom:0}}>
            <div className="chart-title">Cost Breakdown by Tariff Slot (Historical TOU)</div>
            <div style={{ width:'100%', height:250 }}>
              <ResponsiveContainer>
                <BarChart data={bd} layout="vertical" margin={{ left:60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                  <XAxis type="number" stroke="var(--text-muted)" fontSize={11} tickFormatter={v => `₹${v}`} />
                  <YAxis type="category" dataKey="slot" stroke="var(--text-muted)" fontSize={11} width={100} />
                  <Tooltip cursor={{fill:'rgba(255,255,255,0.05)'}} contentStyle={{background:'var(--bg-surface)', border:'1px solid var(--border)'}} />
                  <Bar dataKey="cost" radius={[0,4,4,0]}>
                    {bd.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={['var(--cyan)','var(--amber)','var(--green)','var(--red)'][index % 4]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="glass-card">
          <div className="section-title">🧮 Off-Peak Shift Savings Calculator</div>
          <div style={{marginBottom:'1rem'}}>
            <label className="label">Monthly Usage (kWh)</label>
            <input type="number" className="input" value={shiftKwh} onChange={e => {
              const v = parseFloat(e.target.value); setShiftKwh(v); calculateSavings(v, shiftPct);
            }} />
          </div>
          <div style={{marginBottom:'1.5rem'}}>
            <label className="label">Shift {shiftPct}% to Night Off-Peak (10PM–6AM)</label>
            <input type="range" min={5} max={50} value={shiftPct} onChange={handleShiftChange} style={{width:'100%'}} />
          </div>

          {savingResult && (
            <div style={{background:'rgba(16,185,129,0.05)', border:'1px solid rgba(16,185,129,0.2)', borderRadius:'8px', padding:'1rem'}}>
              <div className="stat-row"><span className="stat-label">Energy Shifted</span><span className="stat-value">{savingResult.shifted_kwh} kWh</span></div>
              <div className="stat-row"><span className="stat-label">Cost at Peak (₹6.50)</span><span className="stat-value">₹{savingResult.cost_at_peak}</span></div>
              <div className="stat-row"><span className="stat-label">Cost at Off-Peak (₹3.75)</span><span className="stat-value">₹{savingResult.cost_at_off_peak}</span></div>
              <div className="stat-row"><span className="stat-label">Monthly Saving</span><span className="stat-value" style={{color:'var(--green)', fontSize:'1.2rem'}}>₹{savingResult.monthly_saving}</span></div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
