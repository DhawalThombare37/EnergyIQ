import { useState, useEffect } from 'react'
import { useData } from '../context/DataContext.jsx'
import { dataApi, auditApi } from '../api.js'
import EmptyState from '../components/EmptyState.jsx'
import KpiCard from '../components/KpiCard.jsx'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function Dashboard() {
  const { dataLoaded } = useData()
  const [summary, setSummary] = useState(null)
  const [dailyData, setDailyData] = useState([])
  const [effScore, setEffScore] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (dataLoaded) {
      setLoading(true)
      Promise.all([
        dataApi.summary(),
        dataApi.daily(30),
        auditApi.efficiencyScore()
      ])
      .then(([sumRes, dailyRes, effRes]) => {
        setSummary(sumRes.data)
        // Ensure dates are string formatting
        const formattedDaily = dailyRes.data.map(d => ({
          ...d,
          date: new Date(d.date).toLocaleDateString('en-GB')
        }))
        setDailyData(formattedDaily)
        setEffScore(effRes.data.score)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
    }
  }, [dataLoaded])

  if (!dataLoaded) return <EmptyState />
  if (loading || !summary) return <div style={{padding:'2rem'}}>Loading dashboard... <span className="spinner"/></div>

  const effColor = effScore >= 70 ? 'var(--green)' : effScore >= 50 ? 'var(--amber)' : 'var(--red)'

  return (
    <div>
      <div className="page-header fade-in">
        <h1 className="page-title">⚡ EnergyIQ Dashboard</h1>
        <p className="page-subtitle">AI-Powered Energy Intelligence Platform</p>
      </div>

      <div className="kpi-grid kpi-grid-4 fade-in" style={{animationDelay:'0.1s'}}>
        <KpiCard title="Total Energy" value={`${Math.round(summary.total_kwh)} kWh`} sub="Total consumed" icon="⚡" />
        <KpiCard title="Avg Daily Usage" value={`${summary.avg_daily_kwh.toFixed(2)} kWh`} sub="per day" icon="📊" color="var(--purple)" />
        <KpiCard title="Avg Daily Bill" value={`₹${Math.round(summary.avg_daily_bill_slab)}`} sub="Slab billing" icon="💰" color="var(--amber)" />
        <KpiCard title="Efficiency Score" value={effScore} sub="/ 100" icon="🏆" color={effColor} />
      </div>

      <div className="grid-2-1 fade-in" style={{animationDelay:'0.2s'}}>
        <div className="chart-wrapper">
          <div className="chart-title">Daily Energy Consumption Trend (Last 30 Days)</div>
          <div style={{ width: '100%', height: 320 }}>
            <ResponsiveContainer>
              <LineChart data={dailyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickMargin={10} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickFormatter={v => `${v} kWh`} width={60} />
                <Tooltip 
                  contentStyle={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:8 }}
                  itemStyle={{ color:'var(--cyan)', fontWeight:600 }}
                  labelStyle={{ color:'var(--text-muted)', marginBottom:4 }}
                />
                <Line type="monotone" dataKey="daily_energy_kwh" stroke="var(--cyan)" strokeWidth={3} dot={{r: 2, fill:'var(--bg-base)'}} activeDot={{r: 6, fill:'var(--cyan)'}} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card">
          <div className="section-title">QUICK STATS</div>
          <div className="stat-row">
            <span className="stat-label">Date Range</span>
            <span className="stat-value">{summary.date_start} → {summary.date_end}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total Days</span>
            <span className="stat-value">{summary.total_days}</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Peak Day</span>
            <span className="stat-value">{summary.max_daily_kwh.toFixed(2)} kWh</span>
          </div>
          <div className="stat-row">
            <span className="stat-label">Total Bill</span>
            <span className="stat-value">₹{Math.round(summary.total_bill_slab)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
