import { useState, useEffect, useRef } from 'react'
import { ragApi } from '../api.js'
import { useDropzone } from 'react-dropzone'

export default function PDFRagChatbot() {
  const [status, setStatus] = useState({ available: false, indexed: false, filename: null })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [input, setInput] = useState('')
  const [history, setHistory] = useState([])
  const messagesEndRef = useRef(null)

  useEffect(() => {
    checkStatus()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  async function checkStatus() {
    try {
      const res = await ragApi.status()
      setStatus(res.data)
    } catch (e) {
      console.error(e)
    }
  }

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return
    const file = acceptedFiles[0]
    setLoading(true); setError('')
    try {
      await ragApi.uploadPdf(file)
      setHistory([{ role: 'ai', content: `Success! Indexed ${file.name}. Ask me any question based on its content.`, ts: new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) }])
      checkStatus()
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false
  })

  async function handleAsk() {
    if (!input.trim() || loading || !status.indexed) return
    const text = input.trim()
    const ts = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
    
    setHistory(prev => [...prev, { role: 'user', content: text, ts }])
    setInput('')
    setLoading(true)

    try {
      const res = await ragApi.ask(text)
      const resTs = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
      setHistory(prev => [...prev, { role: 'ai', content: res.data.answer, ts: resTs }])
    } catch (e) {
      const resTs = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
      setHistory(prev => [...prev, { role: 'ai', content: `❌ Error: ${e.response?.data?.detail || e.message}`, ts: resTs }])
    } finally {
      setLoading(false)
    }
  }

  async function handleClear() {
    try {
      await ragApi.clear()
      setHistory([])
      checkStatus()
    } catch(e) { console.error(e) }
  }

  return (
    <div style={{display:'flex', flexDirection:'column', height:'calc(100vh - 4rem)'}}>
      <div className="page-header fade-in" style={{marginBottom:'1.5rem'}}>
        <h1 className="page-title">📄 PDF Knowledge Chatbot</h1>
        <p className="page-subtitle">RAG powered document analysis using FAISS and Llama 3.2</p>
      </div>

      {!status.indexed ? (
        <div className="fade-in" style={{animationDelay:'0.1s'}}>
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            <div className="dropzone-icon">📥</div>
            <div className="dropzone-text">
              {isDragActive ? "Drop your PDF right here..." : "Drag & drop a PDF file here, or click to select"}
            </div>
            <div className="dropzone-sub">
              Upload any energy bill, equipment manual, or tariff document to analyze its content.
            </div>
          </div>
          {loading && <div style={{textAlign:'center', marginTop:'1rem'}}><span className="spinner"/> Creating FAISS vector store...</div>}
          {error && <div className="alert alert-error" style={{marginTop:'1.5rem'}}>{error}</div>}
        </div>
      ) : (
        <>
          <div className="pdf-indexed-card fade-in" style={{animationDelay:'0.1s'}}>
            <div style={{fontSize:'2.5rem'}}>📄</div>
            <div style={{flex:1}}>
              <div className="pdf-filename">{status.filename}</div>
              <div className="pdf-sub">Vector store indexed and ready for queries.</div>
            </div>
            <button className="btn btn-outline" onClick={handleClear}>Replace PDF</button>
          </div>

          <div className="chat-messages fade-in" style={{animationDelay:'0.2s', flex:1}}>
            {history.map((msg, i) => (
              <div key={i} className={`chat-row ${msg.role}`}>
                <div className="chat-avatar">{msg.role === 'user' ? '👤' : '⚡'}</div>
                <div style={{ flex: 1, display:'flex', flexDirection:'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                  <div className="chat-meta">{msg.role === 'user' ? 'You' : 'DocAgent'} · {msg.ts}</div>
                  <div className={`chat-bubble chat-bubble-${msg.role}`}>
                    {msg.content}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-row ai">
                <div className="chat-avatar">⚡</div>
                <div style={{ flex: 1, display:'flex', flexDirection:'column', alignItems: 'flex-start' }}>
                  <div className="chat-bubble chat-bubble-ai"><span className="spinner" style={{width:16, height:16, borderTopColor:'var(--cyan)'}}/></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-row fade-in" style={{animationDelay:'0.3s'}}>
            <input 
              className="input" 
              placeholder={`Ask a question about ${status.filename}…`}
              value={input} 
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAsk()}
              disabled={loading}
            />
            <button className="btn btn-primary" onClick={handleAsk} disabled={loading || !input.trim()}>
              ➤
            </button>
          </div>
        </>
      )}
    </div>
  )
}
