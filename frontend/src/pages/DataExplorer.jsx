import { useState, useEffect } from 'react'
import { useData } from '../context/DataContext.jsx'
import { dataApi } from '../api.js'
import EmptyState from '../components/EmptyState.jsx'

export default function DataExplorer() {
  const { dataLoaded } = useData()
  const [activeTab, setActiveTab] = useState('raw')
  const [data, setData] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!dataLoaded) return
    setLoading(true)
    
    if (activeTab === 'raw') {
      dataApi.raw(100).then(res => setData(res.data)).finally(() => setLoading(false))
    } else if (activeTab === 'daily') {
      dataApi.daily(100).then(res => setData(res.data)).finally(() => setLoading(false))
    } else if (activeTab === 'stats') {
      dataApi.stats().then(res => setStats(res.data)).finally(() => setLoading(false))
    }
  }, [dataLoaded, activeTab])

  if (!dataLoaded) return <EmptyState />

  return (
    <div>
      <div className="page-header fade-in">
        <h1 className="page-title">📤 Data Explorer</h1>
        <p className="page-subtitle">Inspect and understand your energy dataset</p>
      </div>

      <div className="tabs fade-in">
        <button className={`tab ${activeTab==='raw'?'active':''}`} onClick={() => setActiveTab('raw')}>📋 Raw Data</button>
        <button className={`tab ${activeTab==='daily'?'active':''}`} onClick={() => setActiveTab('daily')}>📅 Daily Aggregated</button>
        <button className={`tab ${activeTab==='stats'?'active':''}`} onClick={() => setActiveTab('stats')}>📈 Statistics</button>
      </div>

      <div className="fade-in" style={{animationDelay:'0.1s'}}>
        {loading && <div style={{padding:'2rem'}}>Loading... <span className="spinner"/></div>}
        
        {!loading && (activeTab === 'raw' || activeTab === 'daily') && data.length > 0 && (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  {Object.keys(data[0]).map(k => <th key={k}>{k}</th>)}
                </tr>
              </thead>
              <tbody>
                {data.map((row, i) => (
                  <tr key={i}>
                    {Object.values(row).map((val, j) => (
                      <td key={j}>{typeof val === 'number' ? val.toFixed(3) : String(val)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && activeTab === 'stats' && stats && (
          <div className="grid-2">
            <div className="glass-card">
              <div className="section-title">Raw Data Statistics</div>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Stat</th>
                      {Object.keys(stats.raw_stats).map(k => <th key={k}>{k}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max'].map(statProp => (
                      <tr key={statProp}>
                        <td><strong>{statProp}</strong></td>
                        {Object.keys(stats.raw_stats).map(k => (
                          <td key={`${k}-${statProp}`}>
                            {stats.raw_stats[k][statProp] != null ? stats.raw_stats[k][statProp].toFixed(3) : '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="glass-card">
              <div className="section-title">Missing Values</div>
              {Object.keys(stats.missing).length === 0 ? (
                <div className="alert alert-success">✅ No missing values in the dataset!</div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr><th>Column</th><th>Missing Count</th><th>Missing %</th></tr>
                    </thead>
                    <tbody>
                      {Object.entries(stats.missing).map(([k, v]) => (
                        <tr key={k}>
                          <td>{k}</td>
                          <td>{v.missing_count}</td>
                          <td>{v.missing_pct}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
