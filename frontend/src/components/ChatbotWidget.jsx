import React, { useState, useEffect, useRef } from 'react'
import { MessageSquare, X, Send, Sparkles, Trash2, Bot, User, ArrowRight } from 'lucide-react'

export default function ChatbotWidget({ isOpen, onClose, onOpen }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '¡Hola! Soy tu **Headhunter IA de Chick-fil-A** 🍗\n\nPuedo responder cualquier consulta sobre todos los candidatos en el pipeline de selección, comparar perfiles o recomendarte a los mejores según el framework oficial y antecedentes laborales.\n\nPrueba preguntarme:\n- *¿Quién es el mejor para Front of House según el puntaje oficial?*\n- *¿Quién es el mejor para Back of House y qué opinas de su perfil?*\n- *¿Cuáles candidatos califican para Systems Analyst?*\n- *Audita el Google Sheet contra Workstream API*'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [hintVisible, setHintVisible] = useState(true)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) scrollToBottom()
  }, [messages, isOpen])

  // Auto-hide hint on initial load after 7 seconds
  useEffect(() => {
    const t = setTimeout(() => setHintVisible(false), 7000)
    return () => clearTimeout(t)
  }, [])

  const quickQuestions = [
    { label: '🍳 Mejor para Cocina (BOH)', text: '¿Cuál es el mejor candidato para Back of House Team Member (Cocina) y por qué?' },
    { label: '💻 Top Systems Analyst', text: '¿Cuáles son los mejores candidatos para Systems Analyst que cumplen con educación en TI y 2+ años de experiencia?' },
    { label: '🛎️ Top 3 Front of House', text: 'Dame el top 3 de mejores candidatos para Front of House Team Member según el framework oficial.' },
    { label: '🏆 Mejor por Puesto', text: '¿Cuál es el mejor candidato para cada uno de los 7 puestos de la tienda aplicando el framework oficial?' },
    { label: '🔍 Auditar Sheet', text: 'Audita el Google Sheet contra la API de Workstream en tiempo real y dime si hay inconsistencias.' },
  ]

  const handleSend = async (textToSend) => {
    const q = (textToSend || input).trim()
    if (!q || loading) return

    setInput('')
    setHintVisible(false)

    const newHistory = [...messages, { role: 'user', content: q }]
    setMessages(newHistory)
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q, history: messages })
      })
      const data = await res.json()
      if (res.ok && data.success) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.reply }])
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `❌ Error: ${data.detail || 'No se pudo procesar la consulta'}` }])
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error de conexión al consultar el Headhunter IA.' }])
    } finally {
      setLoading(false)
    }
  }

  const formatMarkdown = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br/>')
  }

  return (
    <>
      {/* Floating Action Button (Visible on mobile and whenever chat is closed) */}
      {!isOpen && (
        <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-2 pointer-events-none">
          {hintVisible && (
            <div 
              onClick={() => { onOpen(); setHintVisible(false); }}
              className="bg-white text-slate-800 text-xs font-bold px-3.5 py-2.5 rounded-2xl rounded-br-sm shadow-xl border border-red-100 pointer-events-auto cursor-pointer animate-bounceIn max-w-[210px] leading-snug"
            >
              ¿Tienes preguntas sobre los candidatos? 🍗 ¡Pregúntame!
            </div>
          )}

          <button
            onClick={() => { onOpen(); setHintVisible(false); }}
            aria-label="Abrir Headhunter IA"
            className="w-14 h-14 rounded-full bg-gradient-to-tr from-[#E51636] to-[#B80028] text-white shadow-2xl shadow-red-600/50 flex items-center justify-center pointer-events-auto hover:scale-105 active:scale-95 transition-all"
          >
            <img src="/cfa_logo_white.png" alt="CFA" className="w-8 h-8 object-contain" />
          </button>
        </div>
      )}

      {/* Chat Window: Full-Screen on Mobile, Drawer on Desktop */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:inset-auto md:bottom-5 md:right-5 md:w-[420px] md:h-[620px] bg-white flex flex-col md:rounded-2xl md:shadow-2xl md:border md:border-slate-200 overflow-hidden animate-scaleUp">
          {/* Header */}
          <div className="bg-gradient-to-r from-[#E51636] to-[#B80028] text-white p-4 flex items-center justify-between shrink-0 shadow-md">
            <div className="flex items-center gap-3">
              <img src="/cfa_logo_white.png" alt="CFA" className="w-7 h-7 object-contain" />
              <div>
                <h3 className="font-extrabold text-sm flex items-center gap-1.5">
                  <span>Headhunter IA</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                </h3>
                <p className="text-[11px] text-white/80 font-medium">CFA Stafford · Online</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setMessages([{ role: 'assistant', content: 'Conversación reiniciada. ¿Qué deseas consultar hoy sobre los candidatos?' }])}
                title="Limpiar Conversación"
                className="p-1.5 bg-white/10 hover:bg-white/20 rounded-full text-white transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={onClose}
                className="p-1.5 bg-white/10 hover:bg-white/20 rounded-full text-white transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Quick Questions Horizontal Scroll */}
          <div className="p-2 bg-slate-100 border-b border-slate-200 overflow-x-auto flex gap-1.5 shrink-0 scrollbar-none">
            {quickQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(q.text)}
                disabled={loading}
                className="whitespace-nowrap px-2.5 py-1 bg-white hover:bg-red-50 hover:text-red-700 hover:border-red-200 text-slate-700 text-[11px] font-bold rounded-lg border border-slate-200 transition-all shrink-0 shadow-2xs"
              >
                {q.label}
              </button>
            ))}
          </div>

          {/* Messages Area */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3.5 bg-slate-50 text-xs">
            {messages.map((msg, idx) => {
              const isUser = msg.role === 'user'
              return (
                <div key={idx} className={`flex gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'} items-end`}>
                  {!isUser && (
                    <div className="w-7 h-7 rounded-full bg-[#E51636] flex items-center justify-center shrink-0 shadow-xs">
                      <img src="/cfa_logo_white.png" alt="AI" className="w-4 h-4 object-contain" />
                    </div>
                  )}

                  <div
                    className={`max-w-[82%] p-3.5 rounded-2xl leading-relaxed ${
                      isUser
                        ? 'bg-[#E51636] text-white rounded-br-xs shadow-md shadow-red-600/20'
                        : 'bg-white text-slate-800 rounded-bl-xs border border-slate-200 shadow-xs'
                    }`}
                    dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
                  />
                </div>
              )
            })}

            {loading && (
              <div className="flex gap-2 items-end">
                <div className="w-7 h-7 rounded-full bg-[#E51636] flex items-center justify-center shrink-0">
                  <img src="/cfa_logo_white.png" alt="AI" className="w-4 h-4 object-contain" />
                </div>
                <div className="bg-white p-3 rounded-2xl rounded-bl-xs border border-slate-200 shadow-xs flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" />
                  <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0.2s]" />
                  <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:0.4s]" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSend(); }} 
            className="p-3 bg-white border-t border-slate-200 flex items-center gap-2 shrink-0"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Escribe una pregunta al Headhunter..."
              className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-full text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-10 h-10 rounded-full bg-[#E51636] hover:bg-[#c8102e] disabled:opacity-50 text-white flex items-center justify-center shrink-0 shadow-md shadow-red-600/30 transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </>
  )
}
