import { useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import Dashboard from './pages/Dashboard.jsx'
import DataExplorer from './pages/DataExplorer.jsx'
import PredictionEngine from './pages/PredictionEngine.jsx'
import BillEstimator from './pages/BillEstimator.jsx'
import EnergyAudit from './pages/EnergyAudit.jsx'
import OptimizationAdvisor from './pages/OptimizationAdvisor.jsx'
import AIChatAgent from './pages/AIChatAgent.jsx'
import PDFRagChatbot from './pages/PDFRagChatbot.jsx'
import { DataProvider } from './context/DataContext.jsx'

const PAGES = {
  dashboard:    <Dashboard />,
  explorer:     <DataExplorer />,
  predictions:  <PredictionEngine />,
  billing:      <BillEstimator />,
  audit:        <EnergyAudit />,
  advisor:      <OptimizationAdvisor />,
  rag:          <PDFRagChatbot />,
}

export default function App() {
  const [page, setPage] = useState('dashboard')

  return (
    <DataProvider>
      <div className="app-shell">
        <Sidebar activePage={page} onNavigate={setPage} />
        <main className="main-content fade-in" key={page}>
          {PAGES[page]}
        </main>
        <AIChatAgent />
      </div>
    </DataProvider>
  )
}
