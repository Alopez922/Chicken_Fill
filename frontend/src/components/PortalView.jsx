import React, { useState, useEffect, useMemo } from 'react'
import { Search, RefreshCw, MapPin, Calendar, Phone, Eye, ArrowUpDown, HelpCircle, SlidersHorizontal, ChevronDown } from 'lucide-react'
import EvaluationModal from './EvaluationModal'

export default function PortalView() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [selectedPositions, setSelectedPositions] = useState([])
  const [selectedClasses, setSelectedClasses] = useState([])
  const [sortBy, setSortBy] = useState('priority')
  const [activeCandidate, setActiveCandidate] = useState(null)
  const [showMobileFilters, setShowMobileFilters] = useState(false)

  const positionsList = [
    'Back of House Team Member',
    'Chick-fil-A Delivery Driver',
    'Director of Back of House Operations',
    'Front of House Team Member',
    'Front of the House Director',
    'Shift Leader',
    'Systems Analyst'
  ]

  const classList = ['GOLD', 'Ideal', 'Potential', 'Disqualified']

  const fetchCandidates = async (force = false) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/candidates?force_refresh=${force}`)
      const json = await res.json()
      if (res.ok && json.success) {
        setCandidates(json.candidates || [])
      } else {
        setError(json.detail || 'Error al cargar candidatos')
      }
    } catch (err) {
      setError('Error al conectar con el servidor')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCandidates(false)
  }, [])

  // 1. Filter candidates by Search and Position (the scope for the KPI cards)
  const positionFiltered = useMemo(() => {
    return candidates.filter(c => {
      // Search
      if (search.trim()) {
        const q = search.toLowerCase()
        const matchName = (c.name || c.nombre || '').toLowerCase().includes(q)
        const matchPos = (c.position || c.puesto || '').toLowerCase().includes(q)
        const matchEmail = (c.email || '').toLowerCase().includes(q)
        const matchPhone = (c.phone || c.telefono || '').toLowerCase().includes(q)
        if (!matchName && !matchPos && !matchEmail && !matchPhone) return false
      }
      // Position filter (union of selected positions)
      if (selectedPositions.length > 0) {
        const pos = (c.position || c.puesto || '').toLowerCase()
        const matchesAny = selectedPositions.some(sp => {
          const spLower = sp.toLowerCase()
          return pos.includes(spLower) || spLower.includes(pos)
        })
        if (!matchesAny) return false
      }
      return true
    })
  }, [candidates, search, selectedPositions])

  // 2. Metrics dynamically calculate from the position & search filtered candidates!
  const metrics = useMemo(() => {
    return {
      total: positionFiltered.length,
      gold: positionFiltered.filter(c => (c.classification || '').toUpperCase() === 'GOLD').length,
      ideal: positionFiltered.filter(c => (c.classification || '').toUpperCase() === 'IDEAL').length,
      potential: positionFiltered.filter(c => (c.classification || '').toUpperCase() === 'POTENTIAL').length,
      dq: positionFiltered.filter(c => (c.classification || '').toUpperCase() === 'DISQUALIFIED').length,
    }
  }, [positionFiltered])

  // 3. Final filtered and sorted candidates (including classification filter if any)
  const filteredCandidates = useMemo(() => {
    return positionFiltered.filter(c => {
      // Classification filter
      if (selectedClasses.length > 0) {
        const cls = (c.classification || c.clasificacion || '').toUpperCase()
        const matchesCls = selectedClasses.some(sc => sc.toUpperCase() === cls)
        if (!matchesCls) return false
      }
      return true
    }).sort((a, b) => {
      if (sortBy === 'priority') return (b.overall_score || 0) - (a.overall_score || 0)
      if (sortBy === 'score_desc') return (b.overall_score || 0) - (a.overall_score || 0)
      if (sortBy === 'score_asc') return (a.overall_score || 0) - (b.overall_score || 0)
      if (sortBy === 'distance') return (a.distance_miles || 999) - (b.distance_miles || 999)
      if (sortBy === 'date') return new Date(b.applied_date || 0) - new Date(a.applied_date || 0)
      return 0
    })
  }, [positionFiltered, selectedClasses, sortBy])

  const togglePosition = (pos) => {
    setSelectedPositions(prev =>
      prev.includes(pos) ? prev.filter(p => p !== pos) : [...prev, pos]
    )
  }

  const toggleClass = (cls) => {
    setSelectedClasses(prev =>
      prev.includes(cls) ? prev.filter(c => c !== cls) : [...prev, cls]
    )
  }

  const resetAll = () => {
    setSearch('')
    setSelectedPositions([])
    setSelectedClasses([])
    setSortBy('priority')
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      
      {/* Top Banner (Screenshot 2 style) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#E51636] text-white flex items-center justify-center font-extrabold text-sm tracking-tight shadow-md shadow-red-600/30">
            CFA
          </div>
          <h1 className="text-base font-extrabold text-slate-900 tracking-tight">
            Candidates Portal — <span className="text-[#E51636]">CFA Stafford</span>
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          {/* Search Box */}
          <div className="relative flex-1 md:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, email or position..."
              className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#E51636]"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-semibold px-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Updated: live</span>
          </div>

          <button
            onClick={resetAll}
            className="px-3.5 py-1.5 bg-[#E51636] hover:bg-[#c8102e] text-white text-xs font-bold rounded-lg shadow-sm transition-all flex items-center gap-1 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Strip (Screenshot 2 style - dynamically updates with filters) */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div 
          onClick={() => setSelectedClasses([])}
          className={`p-4 bg-white rounded-2xl border-2 shadow-xs text-left cursor-pointer transition-all ${
            selectedClasses.length === 0 ? 'border-[#E51636] ring-2 ring-red-500/20' : 'border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">TOTAL</div>
          <div className="text-3xl font-black text-slate-900 mt-0.5">{metrics.total}</div>
          <div className="text-[11px] text-slate-400 font-medium">candidates</div>
        </div>

        <div 
          onClick={() => toggleClass('GOLD')}
          className={`p-4 bg-white rounded-2xl border shadow-xs text-left cursor-pointer transition-all ${
            selectedClasses.includes('GOLD') ? 'border-amber-500 ring-2 ring-amber-500/20 bg-amber-50/20' : 'border-slate-200 hover:border-amber-300'
          }`}
        >
          <div className="text-[10px] font-bold text-amber-600 uppercase tracking-wider">GOLD</div>
          <div className="text-3xl font-black text-amber-600 mt-0.5">{metrics.gold}</div>
          <div className="text-[11px] text-slate-400 font-medium">≥ 97%</div>
        </div>

        <div 
          onClick={() => toggleClass('Ideal')}
          className={`p-4 bg-white rounded-2xl border shadow-xs text-left cursor-pointer transition-all ${
            selectedClasses.includes('Ideal') ? 'border-emerald-500 ring-2 ring-emerald-500/20 bg-emerald-50/20' : 'border-slate-200 hover:border-emerald-300'
          }`}
        >
          <div className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">IDEAL</div>
          <div className="text-3xl font-black text-emerald-600 mt-0.5">{metrics.ideal}</div>
          <div className="text-[11px] text-slate-400 font-medium">75% - 96%</div>
        </div>

        <div 
          onClick={() => toggleClass('Potential')}
          className={`p-4 bg-white rounded-2xl border shadow-xs text-left cursor-pointer transition-all ${
            selectedClasses.includes('Potential') ? 'border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/20' : 'border-slate-200 hover:border-blue-300'
          }`}
        >
          <div className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">POTENTIAL</div>
          <div className="text-3xl font-black text-blue-600 mt-0.5">{metrics.potential}</div>
          <div className="text-[11px] text-slate-400 font-medium">50% - 74%</div>
        </div>

        <div 
          onClick={() => toggleClass('Disqualified')}
          className={`p-4 bg-white rounded-2xl border shadow-xs text-left col-span-2 sm:col-span-1 cursor-pointer transition-all ${
            selectedClasses.includes('Disqualified') ? 'border-rose-500 ring-2 ring-rose-500/20 bg-rose-50/20' : 'border-slate-200 hover:border-rose-300'
          }`}
        >
          <div className="text-[10px] font-bold text-rose-600 uppercase tracking-wider">DISQUALIFIED</div>
          <div className="text-3xl font-black text-rose-600 mt-0.5">{metrics.dq}</div>
          <div className="text-[11px] text-slate-400 font-medium">auto-disqualified</div>
        </div>
      </div>

      {/* Mobile Filter Toggle Button */}
      <div className="lg:hidden flex items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-slate-200 shadow-xs">
        <button
          onClick={() => setShowMobileFilters(!showMobileFilters)}
          className="flex-1 flex items-center justify-between px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-[#E51636]" />
            <span>Filtros & Ordenar</span>
            {(selectedPositions.length > 0 || selectedClasses.length > 0) && (
              <span className="w-5 h-5 rounded-full bg-[#E51636] text-white text-[10px] flex items-center justify-center font-black">
                {selectedPositions.length + selectedClasses.length}
              </span>
            )}
          </div>
          <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${showMobileFilters ? 'rotate-180' : ''}`} />
        </button>

        {(selectedPositions.length > 0 || selectedClasses.length > 0 || search) && (
          <button
            onClick={resetAll}
            className="px-3 py-2 text-xs font-bold text-red-600 hover:bg-red-50 rounded-xl cursor-pointer"
          >
            Limpiar
          </button>
        )}
      </div>

      {/* Main Content Layout: Left Filter Sidebar + Right Candidates Grid */}
      <div className="flex flex-col lg:flex-row gap-6 items-start">
        
        {/* Left Filter Sidebar (Collapsible on mobile, persistent on desktop) */}
        <aside className={`w-full lg:w-64 bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-6 shrink-0 transition-all ${
          showMobileFilters ? 'block' : 'hidden lg:block'
        }`}>
          {/* Sort Selector */}
          <div>
            <label className="block text-[11px] font-extrabold text-slate-700 uppercase tracking-wider mb-2">
              SORT BY
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-800 focus:outline-none focus:border-[#E51636]"
            >
              <option value="priority">Priority (best first)</option>
              <option value="score_desc">Score (high to low)</option>
              <option value="score_asc">Score (low to high)</option>
              <option value="distance">Distance (closest first)</option>
              <option value="date">Applied Date</option>
            </select>
          </div>

          {/* Position Filter Checkboxes */}
          <div>
            <label className="block text-[11px] font-extrabold text-slate-700 uppercase tracking-wider mb-2.5">
              POSITION
            </label>
            <div className="space-y-2">
              {positionsList.map(pos => {
                const checked = selectedPositions.includes(pos)
                return (
                  <label key={pos} className="flex items-start gap-2.5 cursor-pointer text-xs font-medium text-slate-700 hover:text-slate-900 select-none">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => togglePosition(pos)}
                      className="mt-0.5 rounded border-slate-300 text-[#E51636] focus:ring-red-500 w-4 h-4 cursor-pointer"
                    />
                    <span className="leading-tight">{pos}</span>
                  </label>
                )
              })}
            </div>
          </div>

          {/* Classification Filter Checkboxes */}
          <div>
            <label className="block text-[11px] font-extrabold text-slate-700 uppercase tracking-wider mb-2.5">
              CLASSIFICATION
            </label>
            <div className="space-y-2">
              {classList.map(cls => {
                const checked = selectedClasses.includes(cls)
                return (
                  <label key={cls} className="flex items-center gap-2.5 cursor-pointer text-xs font-medium text-slate-700 hover:text-slate-900 select-none">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleClass(cls)}
                      className="rounded border-slate-300 text-[#E51636] focus:ring-red-500 w-4 h-4 cursor-pointer"
                    />
                    <span>{cls}</span>
                  </label>
                )
              })}
            </div>
          </div>

          <button
            onClick={resetAll}
            className="w-full py-2 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all"
          >
            Clear filters
          </button>
        </aside>

        {/* Right Candidates Grid */}
        <div className="flex-1 w-full space-y-4">
          <div className="text-xs font-bold text-slate-500">
            Showing all <strong className="text-slate-900">{filteredCandidates.length}</strong> candidates
          </div>

          {loading ? (
            <div className="py-20 bg-white rounded-2xl border border-slate-200 flex flex-col items-center justify-center space-y-3">
              <div className="w-9 h-9 border-3 border-red-500/20 border-t-[#E51636] rounded-full animate-spin" />
              <p className="text-xs font-bold text-slate-600">Loading candidates at 0ms...</p>
            </div>
          ) : filteredCandidates.length === 0 ? (
            <div className="py-16 bg-white rounded-2xl border border-slate-200 text-center space-y-2">
              <p className="text-sm font-bold text-slate-700">No candidates match the selected filters.</p>
              <button onClick={resetAll} className="text-xs font-bold text-[#E51636] hover:underline">
                Clear all filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredCandidates.map((candidate, idx) => {
                const name = candidate.name || candidate.nombre
                const pos = candidate.position || candidate.puesto
                const cls = (candidate.classification || 'GOLD').toUpperCase()
                const score = candidate.overall_score || candidate.score || 0
                const choice = candidate.choice_score ?? 0
                const distScore = candidate.distance_score ?? 10
                const ai = candidate.ai_score ?? 0
                const distMiles = candidate.distance_miles ?? 0
                const addr = candidate.address || candidate.direccion || ''
                const applied = candidate.applied_date || candidate.fecha_aplicacion || ''
                const phone = candidate.phone || candidate.telefono || ''

                const hasCFA = Boolean(candidate.has_cfa_experience)
                const isMulti = Boolean(candidate.is_multi_applicant)
                const appliedPositions = candidate.applied_positions || []

                let cardVisualClasses = "bg-white border-slate-200 shadow-xs hover:shadow-md"
                if (hasCFA) {
                  if (cls === 'GOLD') {
                    cardVisualClasses = "bg-gradient-to-b from-amber-50/60 via-white to-white border-amber-300 ring-2 ring-amber-400/50 shadow-md shadow-amber-200/50 hover:shadow-lg hover:shadow-amber-200/70"
                  } else if (cls === 'IDEAL') {
                    cardVisualClasses = "bg-gradient-to-b from-emerald-50/60 via-white to-white border-emerald-300 ring-2 ring-emerald-400/50 shadow-md shadow-emerald-200/50 hover:shadow-lg hover:shadow-emerald-200/70"
                  } else if (cls === 'POTENTIAL') {
                    cardVisualClasses = "bg-gradient-to-b from-blue-50/60 via-white to-white border-blue-300 ring-2 ring-blue-400/50 shadow-md shadow-blue-200/50 hover:shadow-lg hover:shadow-blue-200/70"
                  } else {
                    cardVisualClasses = "bg-gradient-to-b from-rose-50/30 via-white to-white border-rose-200 shadow-xs hover:shadow-md"
                  }
                }

                return (
                  <div
                    key={candidate.uuid || idx}
                    className={`rounded-2xl border p-5 transition-all flex flex-col justify-between ${cardVisualClasses}`}
                  >
                    <div>
                      {/* Name & Badges Header */}
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-extrabold text-slate-900 text-sm leading-tight">
                          {name}
                        </h3>

                        <div className="flex items-center gap-1.5 shrink-0 flex-wrap justify-end">
                          {hasCFA && (
                            <span 
                              title={candidate.cfa_experience_detail || "Experiencia previa en Chick-fil-A"}
                              className="text-[9px] font-black px-2 py-0.5 rounded-md bg-[#E51636] text-white shadow-xs tracking-tight flex items-center gap-1 cursor-help"
                            >
                              <span>🍗 Ex-Empleado CFA</span>
                            </span>
                          )}
                          {isMulti && (
                            <span 
                              title={`Postulaciones detectadas (${appliedPositions.length}): ${appliedPositions.join(', ')}`}
                              className="text-[9px] font-extrabold px-1.5 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 cursor-help"
                            >
                              📑 {appliedPositions.length} Puestos
                            </span>
                          )}
                          <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded-md border shrink-0 ${
                            cls === 'GOLD' ? 'bg-amber-50 text-amber-700 border-amber-300' :
                            cls === 'IDEAL' ? 'bg-emerald-50 text-emerald-700 border-emerald-300' :
                            cls === 'POTENTIAL' ? 'bg-blue-50 text-blue-700 border-blue-300' :
                            'bg-rose-50 text-rose-700 border-rose-300'
                          }`}>
                            {cls}
                          </span>
                        </div>
                      </div>

                      <p className="text-xs font-semibold text-slate-500 mt-0.5">{pos}</p>

                      {/* Overall Score Bar with Orange Accent Line (Screenshot 2 style) */}
                      <div className="mt-4 pt-2 border-t-2 border-amber-500">
                        <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 mb-2">
                          <span className="uppercase tracking-wider text-[10px] text-slate-500">OVERALL SCORE</span>
                          <span className="text-sm font-extrabold text-slate-900">{score}%</span>
                        </div>

                        {/* 3 Metrics: Choice / Distance / AI Score */}
                        <div className="grid grid-cols-3 gap-2 text-center py-2 bg-slate-50/70 rounded-xl border border-slate-100">
                          <div>
                            <div className="text-base font-extrabold text-slate-900">{choice}</div>
                            <div className="text-[9px] font-bold text-slate-400 uppercase tracking-tight">CHOICE</div>
                          </div>
                          <div>
                            <div className="text-base font-extrabold text-slate-900">{distScore}</div>
                            <div className="text-[9px] font-bold text-slate-400 uppercase tracking-tight">DISTANCE</div>
                          </div>
                          <div>
                            <div className="text-base font-extrabold text-slate-900">{ai}</div>
                            <div className="text-[9px] font-bold text-slate-400 uppercase tracking-tight">AI SCORE</div>
                          </div>
                        </div>
                      </div>

                      {/* Metadata rows */}
                      <div className="mt-3 space-y-1 text-xs text-slate-500">
                        {addr && (
                          <div className="flex items-center gap-1.5 truncate">
                            <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span className="truncate">{distMiles > 0 ? `${distMiles} mi — ` : ''}{addr}</span>
                          </div>
                        )}
                        {applied && (
                          <div className="flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span>Applied: {applied}</span>
                          </div>
                        )}
                        {phone && phone !== '—' && (
                          <div className="flex items-center gap-1.5">
                            <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span>{phone}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* View Evaluation Button (Screenshot 2 style) */}
                    <div className="mt-4 pt-3 border-t border-slate-100 text-center">
                      <button
                        onClick={() => setActiveCandidate(candidate)}
                        className="w-full py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 shadow-2xs"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View Evaluation</span>
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Evaluation Modal Popup */}
      {activeCandidate && (
        <EvaluationModal
          candidate={activeCandidate}
          onClose={() => setActiveCandidate(null)}
        />
      )}
    </div>
  )
}
