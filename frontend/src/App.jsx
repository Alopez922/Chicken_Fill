import React, { useState, useEffect } from 'react'
import LoginView from './components/LoginView'
import Navbar from './components/Navbar'
import PortalView from './components/PortalView'
import AuditView from './components/AuditView'
import RubricsView from './components/RubricsView'
import ChatbotWidget from './components/ChatbotWidget'

export default function App() {
  const [user, setUser] = useState(null)
  const [activeTab, setActiveTab] = useState('portal')
  const [isChatOpen, setIsChatOpen] = useState(false)

  // Check persisted login
  useEffect(() => {
    const savedUser = localStorage.getItem('cfa_user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {
        localStorage.removeItem('cfa_user')
      }
    }
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    localStorage.setItem('cfa_user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('cfa_user')
  }

  if (!user) {
    return <LoginView onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onLogout={handleLogout}
        onToggleChat={() => setIsChatOpen(prev => !prev)}
      />

      <main className="flex-1">
        {activeTab === 'portal' && <PortalView />}
        {activeTab === 'audit' && <AuditView />}
        {activeTab === 'rubrics' && <RubricsView />}
      </main>

      {/* Copilot IA / Mobile Chatbot Widget */}
      <ChatbotWidget
        isOpen={isChatOpen}
        onOpen={() => setIsChatOpen(true)}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  )
}
