import React, { useState } from 'react'
import { AlertCircle, Eye, EyeOff } from 'lucide-react'

export default function LoginView({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setError('Please enter your username and password')
      return
    }
    setLoading(true)
    setError('')

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password: password.trim() })
      })
      const data = await res.json()
      if (res.ok && data.success) {
        onLogin(data)
      } else {
        setError(data.detail || 'Invalid username or password')
      }
    } catch (err) {
      setError('Could not connect to server. Please check your connection.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div 
      className="min-h-screen w-full flex flex-col items-center justify-center p-4 bg-[#E51636] bg-cover bg-center bg-no-repeat relative font-sans"
      style={{ backgroundImage: "url('/cfa_login_bg_clean.png'), url('/chicken fill background.png')" }}
    >
      {/* Top Logo */}
      <div className="mb-6 flex justify-center">
        <img
          src="/cfa_logo_white.png"
          alt="Chick-fil-A"
          className="w-56 max-w-[80vw] object-contain drop-shadow-[0_4px_14px_rgba(0,0,0,0.25)]"
        />
      </div>

      {/* Main Login Card */}
      <div className="w-full max-w-[390px] bg-white rounded-[18px] shadow-[0_20px_45px_rgba(0,0,0,0.28),0_2px_8px_rgba(0,0,0,0.08)] p-7 sm:p-8 relative z-10 animate-scaleUp">
        <h2 className="text-[23px] font-bold text-slate-800 text-center tracking-tight">
          Welcome Back
        </h2>
        <p className="text-[13.5px] text-slate-500 text-center mb-6 mt-0.5 font-medium">
          Please log in to continue
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-red-700 text-xs font-semibold">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username or Email"
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#E51636] focus:ring-2 focus:ring-red-500/20 transition-all font-medium"
              autoCapitalize="none"
              autoCorrect="off"
            />
          </div>

          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full px-3.5 pr-10 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#E51636] focus:ring-2 focus:ring-red-500/20 transition-all font-medium"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 bg-[#E51636] hover:bg-[#c8102e] text-white font-bold text-sm rounded-lg shadow-md shadow-red-600/35 transition-all transform active:scale-[0.98] disabled:opacity-70 cursor-pointer"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
            ) : (
              'Log In'
            )}
          </button>
        </form>

        <div className="mt-4 text-center">
          <a
            href="#"
            onClick={(e) => { e.preventDefault(); setError('Contact your store administrator for password resets.'); }}
            className="text-xs font-semibold text-[#E51636] hover:text-[#9A0017] hover:underline"
          >
            Forgot your password?
          </a>
        </div>
      </div>

      {/* Footer Branding Text */}
      <div className="mt-5 text-center text-xs text-white/90 font-medium drop-shadow-[0_1px_3px_rgba(0,0,0,0.3)]">
        🔒 Chick-fil-A Stafford · Internal HR Intelligence System
      </div>
    </div>
  )
}

