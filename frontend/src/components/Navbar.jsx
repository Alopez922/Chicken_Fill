import React from 'react'
import { LayoutGrid, RefreshCw, FileText, LogOut, MessageSquare, Sparkles } from 'lucide-react'

export default function Navbar({ activeTab, setActiveTab, user, onLogout, onToggleChat, unreadChat }) {
  const tabs = [
    { id: 'portal', label: 'Portal de Candidatos', icon: LayoutGrid },
    { id: 'audit', label: 'Auditoría en Vivo', icon: RefreshCw },
    { id: 'rubrics', label: 'Rúbricas Oficiales', icon: FileText },
  ]

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Store Title */}
          <div className="flex items-center gap-3">
            <img src="/cfa_logo_red.png" alt="Chick-fil-A" className="h-8 object-contain" />
            <div className="hidden sm:block">
              <div className="text-xs font-extrabold text-slate-900 tracking-tight flex items-center gap-1.5">
                <span>CFA Stafford</span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="text-[10px] font-bold text-emerald-600 uppercase">Live 0ms</span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">Candidate Talent Portal</p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="flex items-center gap-1 sm:gap-2">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                    isActive
                      ? 'bg-red-50 text-[#E51636] shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#E51636]' : 'text-slate-400'}`} />
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              )
            })}
          </nav>

          {/* User & Actions */}
          <div className="flex items-center gap-2">
            {/* Desktop Copilot Button */}
            <button
              onClick={onToggleChat}
              className="hidden md:flex items-center gap-2 px-3.5 py-2 rounded-xl bg-gradient-to-r from-[#E51636] to-[#B80028] text-white text-xs font-bold shadow-md shadow-red-600/20 hover:shadow-red-600/30 hover:scale-[1.02] transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Headhunter IA</span>
            </button>

            {/* User Badge */}
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-xl text-xs font-semibold text-slate-700">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>{user?.displayName || user?.username || 'Operator'}</span>
            </div>

            {/* Logout */}
            <button
              onClick={onLogout}
              title="Cerrar Sesión"
              className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
