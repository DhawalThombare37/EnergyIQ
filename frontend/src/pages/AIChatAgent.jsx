import { useState, useEffect, useRef } from 'react'
import { chatApi } from '../api.js'

export default function AIChatAgent() {
  const [online, setOnline] = useState(false)
  const [history, setHistory] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const messagesEndRef = useRef(null)

  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    chatApi.status().then(res => setOnline(res.data.available)).catch(() => setOnline(false))
    chatApi.quickSuggestions().then(res => setSuggestions(res.data)).catch(console.error)
  }, [])

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [history, isOpen])

  async function handleSubmit(queryText) {
    const text = typeof queryText === 'string' ? queryText : input.trim()
    if (!text) return

    const time = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
    setHistory(prev => [...prev, { role: 'user', content: text, ts: time }])
    setInput('')
    setLoading(true)

    try {
      const res = await chatApi.send(text)
      const resTime = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
      setHistory(prev => [...prev, { role: 'ai', content: res.data.response, ts: resTime }])
    } catch (e) {
      const resTime = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})
      setHistory(prev => [...prev, { role: 'ai', content: `❌ Error: ${e.response?.data?.detail || e.message}`, ts: resTime }])
    } finally {
      setLoading(false)
    }
  }

  function formatContent(text) {
    return text.split('\n').map((line, i) => (
      <span key={i}>
        {line.replace(/\*\*/g, '')}
        <br/>
      </span>
    ))
  }

  return (
    <>
      <button className="chat-fab" onClick={() => setIsOpen(!isOpen)} title="NexusAI Assistant">
        {isOpen ? '✕' : '✨'}
      </button>

      {isOpen && (
        <div className="floating-chat-window">
          <div style={{display:'flex', flexDirection:'column', height:'100%', padding: '1rem', background: 'rgba(6,11,20,0.4)'}}>
            <div className="fade-in" style={{marginBottom:'0.75rem'}}>
              <h3 style={{fontSize: '1.2rem', fontWeight: 800, color: 'var(--cyan)', marginBottom:'0.2rem'}}>✨ NexusAI Assistant</h3>
              <div className={`ollama-badge ${online ? 'online' : 'offline'}`} style={{marginBottom: 0}}>
                <div className="ollama-dot"/>
                {online ? 'Online' : 'Offline'}
              </div>
            </div>
            
            {suggestions.length > 0 && history.length === 0 && (
              <div className="quick-queries fade-in">
                {suggestions.slice(0,6).map((q, i) => (
                  <button key={i} className="quick-query-btn" onClick={() => handleSubmit(q)}>⚡ {q.substring(0,35)}…</button>
                ))}
              </div>
            )}

            <div className="chat-messages fade-in" style={{animationDelay:'0.2s', flex: 1}}>
              {history.length === 0 ? (
                <div className="empty-state" style={{padding: '2rem 1rem'}}>
                   <div className="empty-icon">💬</div>
                   <div className="empty-title" style={{fontSize: '1rem'}}>Ask me anything!</div>
                   <div className="empty-sub" style={{fontSize: '0.8rem'}}>e.g. "Why is my bill high?"</div>
                </div>
              ) : (
                history.map((msg, i) => (
                  <div key={i} className={`chat-row ${msg.role}`}>
                    <div className="chat-avatar">{msg.role === 'user' ? '👤' : '⚡'}</div>
                    <div style={{ flex: 1, display:'flex', flexDirection:'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                      <div className="chat-meta">{msg.role === 'user' ? 'You' : 'NexusAI'} · {msg.ts}</div>
                      <div className={`chat-bubble chat-bubble-${msg.role}`}>
                        {formatContent(msg.content)}
                      </div>
                    </div>
                  </div>
                ))
              )}
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
                placeholder="Ask NexusAI..." 
                value={input} 
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                disabled={loading}
              />
              <button className="btn btn-primary" onClick={handleSubmit} disabled={loading || !input.trim()} style={{padding: '0.6rem 0.8rem'}}>
                ➤
              </button>
              {history.length > 0 && (
                <button className="btn btn-outline" style={{padding:'0.6rem'}} onClick={() => setHistory([])} title="Clear Chat">🗑️</button>
              )}
            </div>

          </div>
        </div>
      )}
    </>
  )
}
