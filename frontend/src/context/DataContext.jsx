import { createContext, useContext, useState } from 'react'

const DataContext = createContext(null)

export function DataProvider({ children }) {
  const [dataLoaded, setDataLoaded]       = useState(false)
  const [dataInfo, setDataInfo]           = useState(null)   // {records, days}
  const [predictionsRun, setPredictionsRun] = useState(false)

  return (
    <DataContext.Provider value={{
      dataLoaded, setDataLoaded,
      dataInfo, setDataInfo,
      predictionsRun, setPredictionsRun,
    }}>
      {children}
    </DataContext.Provider>
  )
}

export function useData() {
  return useContext(DataContext)
}
