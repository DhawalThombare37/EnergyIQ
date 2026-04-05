import { useState, useEffect } from 'react'
import { useData } from '../context/DataContext.jsx'
import { predictApi } from '../api.js'
import EmptyState from '../components/EmptyState.jsx'
import KpiCard from '../components/KpiCard.jsx'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'

export default function PredictionEngine() {
  const { dataLoaded, dataInfo, predictionsRun, setPredictionsRun } = useData()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [preds, setPreds] = useState(null)
  
  const [trainDays, setTrainDays] = useState(150)
  const [predDays, setPredDays] = useState(30)

  useEffect(() => {
    if (predictionsRun && !preds) {
      predictApi.results()
        .then(res => setPreds(res.data))
        .catch(console.error)
    }
  }, [predictionsRun])

  if (!dataLoaded) return <EmptyState />

  const maxTrain = Math.max(1, (dataInfo?.days || 0) - 5)
  const maxPred = Math.max(1, (dataInfo?.days || 0) - trainDays)

  async function handleRun() {
    setLoading(true); setError('')
    try {
      const res = await predictApi.run(trainDays, predDays)
      setPreds(res.data)
      setPredictionsRun(true)
    } catch(e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const chartData = preds?.dates.map((date, i) => ({
    date: new Date(date).toLocaleDateString('en-GB'),
    actual_kwh: preds.h_unit_actual[i],
    pred_kwh: preds.h_unit_pred[i],
    actual_bill: preds.h_bill_actual[i],
    pred_bill: preds.h_bill_pred[i]
  }))

  return (
    <div>
      <div className="page-header fade-in">
        <h1 className="page-title">🔮 Prediction Engine</h1>
        <p className="page-subtitle">XGBoost 4-model forecasting pipeline</p>
      </div>

      <div className="glass-card fade-in" style={{marginBottom:'1.5rem', animationDelay:'0.1s'}}>
        <div className="grid-3" style={{alignItems:'flex-end'}}>
          <div>
            <label className="label">Training Days</label>
            <input type="number" className="input" value={trainDays} onChange={e => setTrainDays(parseInt(e.target.value))} min={10} max={maxTrain} />
          </div>
          <div>
            <label className="label">Prediction Days</label>
            <input type="number" className="input" value={predDays} onChange={e => setPredDays(parseInt(e.target.value))} min={1} max={maxPred} />
          </div>
          <div>
            <button className="btn btn-primary" style={{width:'100%', justifyContent:'center'}} onClick={handleRun} disabled={loading}>
              {loading ? <><span className="spinner" style={{width:14,height:14}}/> Training Models…</> : '🚀 Run Predictions'}
            </button>
          </div>
        </div>
        {error && <div className="alert alert-error" style={{marginTop:'1rem'}}>{error}</div>}
      </div>

      {!predictionsRun && !preds && !loading && (
        <div className="empty-state fade-in" style={{background:'rgba(0,212,255,0.04)', border:'1px solid rgba(0,212,255,0.12)', borderRadius:'14px'}}>
          <div className="empty-icon">🔮</div>
          <div className="empty-title">Ready to Predict</div>
          <div className="empty-sub">Configure parameters above and click Run Predictions. This trains 4 XGBoost models in parallel (takes ~5s).</div>
        </div>
      )}

      {preds && (
        <div className="fade-in">
          <div className="kpi-grid kpi-grid-4">
            <KpiCard title="🏠 kWh MAPE" value={`${preds.h_unit_mape.toFixed(1)}%`} sub="Lower is better" color={preds.h_unit_mape < 10 ? 'var(--green)' : 'var(--amber)'} />
            <KpiCard title="🏠 Bill MAPE" value={`${preds.h_bill_mape.toFixed(1)}%`} sub="Lower is better" color={preds.h_bill_mape < 10 ? 'var(--green)' : 'var(--amber)'} />
            <KpiCard title="🏭 Ind. kWh MAPE" value={`${preds.i_unit_mape.toFixed(1)}%`} sub="Industrial units" color={preds.i_unit_mape < 10 ? 'var(--green)' : 'var(--amber)'} />
            <KpiCard title="🏭 Ind. Bill MAPE" value={`${preds.i_bill_mape.toFixed(1)}%`} sub="Industrial TOU cost" color={preds.i_bill_mape < 10 ? 'var(--green)' : 'var(--amber)'} />
          </div>

          <div className="grid-2">
            <div className="chart-wrapper">
              <div className="chart-title">Household kWh — Actual vs Predicted</div>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={10} minTickGap={20} />
                    <YAxis yAxisId="left" stroke="var(--text-muted)" fontSize={10} width={40} />
                    <Tooltip contentStyle={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:8 }} />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                    <Line yAxisId="left" type="step" dataKey="actual_kwh" name="Actual kWh" stroke="rgba(255,255,255,0.4)" strokeWidth={2} dot={false} />
                    <Line yAxisId="left" type="monotone" dataKey="pred_kwh" name="Predicted kWh" stroke="var(--cyan)" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="chart-wrapper">
              <div className="chart-title">Household Slab Bill — Actual vs Predicted</div>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={10} minTickGap={20} />
                    <YAxis yAxisId="left" stroke="var(--text-muted)" fontSize={10} width={40} tickFormatter={v => `₹${v}`} />
                    <Tooltip contentStyle={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:8 }} />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                    <Line yAxisId="left" type="step" dataKey="actual_bill" name="Actual Bill ₹" stroke="rgba(255,255,255,0.4)" strokeWidth={2} dot={false} />
                    <Line yAxisId="left" type="monotone" dataKey="pred_bill" name="Predicted Bill ₹" stroke="var(--amber)" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="chart-wrapper" style={{ marginTop: '1.5rem' }}>
              <div className="chart-title">Industrial kWh & TOU Cost</div>
              <div style={{ width: '100%', height: 300 }}>
                <ResponsiveContainer>
                  <LineChart data={preds?.dates.map((date, i) => ({
                    date: new Date(date).toLocaleDateString('en-GB'),
                    act_ind_kwh: preds.i_unit_actual[i],
                    pred_ind_kwh: preds.i_unit_pred[i],
                    act_ind_bill: preds.i_bill_actual[i],
                    pred_ind_bill: preds.i_bill_pred[i],
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={10} minTickGap={20} />
                    <YAxis yAxisId="left" stroke="var(--text-muted)" fontSize={10} width={40} />
                    <YAxis yAxisId="right" orientation="right" stroke="var(--text-muted)" fontSize={10} width={40} tickFormatter={v => `₹${v}`} />
                    <Tooltip contentStyle={{ background:'var(--bg-surface)', border:'1px solid var(--border)', borderRadius:8 }} />
                    <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                    <Line yAxisId="left" type="step" dataKey="act_ind_kwh" name="Act Ind kWh" stroke="rgba(255,255,255,0.4)" strokeWidth={2} dot={false} />
                    <Line yAxisId="left" type="monotone" dataKey="pred_ind_kwh" name="Pred Ind kWh" stroke="var(--cyan)" strokeWidth={2.5} dot={false} />
                    <Line yAxisId="right" type="step" dataKey="act_ind_bill" name="Act Ind Bill ₹" stroke="rgba(255,255,255,0.2)" strokeWidth={2} dot={false} />
                    <Line yAxisId="right" type="monotone" dataKey="pred_ind_bill" name="Pred Ind Bill ₹" stroke="var(--purple)" strokeWidth={2.5} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
