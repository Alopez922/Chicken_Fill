import React, { useState, useEffect, useMemo } from 'react'
import { Search, Filter, ArrowUpDown, RefreshCw, Award, Eye, MapPin, Phone, Calendar, AlertCircle } from 'lucide-react'
import EvaluationModal from './EvaluationModal'

export default function PortalView() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [selectedPositions, setSelectedPositions] = useState([])
  const [selectedClasses, setSelectedClasses] = useState([])
  const [sortBy, setSortBy] = useState('priority')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(12)
  const [activeModalCandidate, setActiveModalCandidate] = useState(null)

  const fetchCandidates = async (force = false) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/candidates?force_refresh=${force}`)
      const json = await res.json()
      if (res.ok && json.success) {
        setCandidates(json.candidates || json.data?.candidates || json.data?.candidatos || json.candidatos || [])
      } else {
        setError(json.detail || 'Error al cargar candidatos')
      }
    } catch (err) {
      setError('No se pudo conectar con el servidor')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCandidates(false)
  }, [])

  // Distinct Positions List
  const distinctPositions = useMemo(() => {
    const set = new Set()
    candidates.forEach(c => {
      if (c.position) set.add(c.position)
    })
    return Array.from(set).sort()
  }, [candidates])

  // Filtered and Sorted Candidates
  const filteredCandidates = useMemo(() => {
    return candidates.filter(c => {
      // Search
      if (search.trim()) {
        const q = search.toLowerCase()
        const matchName = (c.name || '').toLowerCase().includes(q)
        const matchPos = (c.position || '').toLowerCase().includes(q)
        const matchEmail = (c.email || '').toLowerCase().includes(q)
        const matchPhone = (c.phone || '').toLowerCase().includes(q)
        if (!matchName && !matchPos && !matchEmail && !matchPhone) return false
      }
      // Position filter
      if (selectedPositions.length > 0) {
        if (!selectedPositions.includes(c.position)) return false
      }
      // Classification filter
      if (selectedClasses.length > 0) {
        if (!selectedClasses.includes(c.classification)) return false
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
  }, [candidates, search, selectedPositions, selectedClasses, sortBy])

  // Summary Metrics
  const metrics = useMemo(() => {
    const total = candidates.length
    const gold = candidates.filter(c => (c.classification || '').toUpperCase() === 'GOLD').length
    const ideal = candidates.filter(c => (c.classification || '').toUpperCase() === 'IDEAL').length
    const potential = candidates.filter(c => (c.classification || '').toUpperCase() === 'POTENTIAL').length
    const dq = candidates.filter(c => (c.classification || '').toUpperCase() === 'DISQUALIFIED').length
    return { total, gold, ideal, potential, dq }
  }, [candidates])

  // Pagination
  const totalPages = Math.ceil(filteredCandidates.length / pageSize) || 1
  const paginatedCandidates = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filteredCandidates.slice(start, start + pageSize)
  }, [filteredCandidates, currentPage, pageSize])

  const togglePosition = (pos) => {
    setSelectedPositions(prev =>
      prev.includes(pos) ? prev.filter(p => p !== pos) : [...prev, pos]
    )
    setCurrentPage(1)
  }

  const toggleClass = (cls) => {
    setSelectedClasses(prev =>
      prev.includes(cls) ? prev.filter(c => c !== cls) : [...prev, cls]
    )
    setCurrentPage(1)
  }

  const clearFilters = () => {
    setSearch('')
    setSelectedPositions([])
    setSelectedClasses([])
    setSortBy('priority')
    setCurrentPage(1)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Banner Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-4 bg-white rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-1">{metrics.total}</div>
          <div className="text-[10px] text-slate-400 font-medium mt-0.5">candidatos en sheet</div>
        </div>
        <div className="p-4 bg-white rounded-2xl border border-amber-200 shadow-sm text-center">
          <div className="text-xs font-bold text-amber-600 uppercase tracking-wider">GOLD</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-amber-600 mt-1">{metrics.gold}</div>
          <div className="text-[10px] text-amber-600/75 font-medium mt-0.5">≥ 97% Score</div>
        </div>
        <div className="p-4 bg-white rounded-2xl border border-emerald-200 shadow-sm text-center">
          <div className="text-xs font-bold text-emerald-600 uppercase tracking-wider">IDEAL</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-600 mt-1">{metrics.ideal}</div>
          <div className="text-[10px] text-emerald-600/75 font-medium mt-0.5">75% – 96%</div>
        </div>
        <div className="p-4 bg-white rounded-2xl border border-blue-200 shadow-sm text-center">
          <div className="text-xs font-bold text-blue-600 uppercase tracking-wider">POTENTIAL</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-blue-600 mt-1">{metrics.potential}</div>
          <div className="text-[10px] text-blue-600/75 font-medium mt-0.5">50% – 74%</div>
        </div>
        <div className="p-4 bg-white rounded-2xl border border-rose-200 shadow-sm text-center col-span-2 sm:col-span-1">
          <div className="text-xs font-bold text-rose-600 uppercase tracking-wider">DISQUALIFIED</div>
          <div className="text-2xl sm:text-3xl font-extrabold text-rose-600 mt-1">{metrics.dq}</div>
          <div className="text-[10px] text-rose-600/75 font-medium mt-0.5">&lt; 50% / Flag</div>
        </div>
      </div>

      {/* Main Search & Controls Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Search Box */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setCurrentPage(1); }}
              placeholder="Buscar por nombre, email, teléfono o puesto..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all"
            />
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-2 w-full md:w-auto shrink-0">
            <ArrowUpDown className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold text-slate-700 focus:outline-none focus:border-red-500 transition-all w-full md:w-auto"
            >
              <option value="priority">Prioridad (Mejores Primero)</option>
              <option value="score_desc">Mayor Score</option>
              <option value="score_asc">Menor Score</option>
              <option value="distance">Distancia (Más Cercanos)</option>
              <option value="date">Fecha de Postulación</option>
            </select>

            <button
              onClick={() => fetchCandidates(true)}
              title="Recargar datos de Google Sheets"
              className="p-2.5 text-slate-500 hover:text-red-600 hover:bg-red-50 border border-slate-200 rounded-xl transition-all shrink-0"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Position Filter Chips */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Filtrar por Puesto:</span>
            {(selectedPositions.length > 0 || selectedClasses.length > 0 || search) && (
              <button
                onClick={clearFilters}
                className="text-[11px] font-bold text-red-600 hover:underline"
              >
                Limpiar Filtros
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {distinctPositions.map(pos => {
              const isSelected = selectedPositions.includes(pos)
              return (
                <button
                  key={pos}
                  onClick={() => togglePosition(pos)}
                  className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                    isSelected
                      ? 'bg-[#E51636] text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {pos}
                </button>
              )
            })}
          </div>
        </div>

        {/* Classification Filter Chips */}
        <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider self-center mr-1">
            Nivel:
          </span>
          {[
            { id: 'GOLD', label: 'GOLD', color: 'bg-amber-50 text-amber-700 border-amber-200' },
            { id: 'IDEAL', label: 'IDEAL', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
            { id: 'POTENTIAL', label: 'POTENTIAL', color: 'bg-blue-50 text-blue-700 border-blue-200' },
            { id: 'DISQUALIFIED', label: 'DISQUALIFIED', color: 'bg-rose-50 text-rose-700 border-rose-200' },
          ].map(c => {
            const isSelected = selectedClasses.includes(c.id)
            return (
              <button
                key={c.id}
                onClick={() => toggleClass(c.id)}
                className={`px-3 py-0.5 rounded-lg text-[11px] font-extrabold border transition-all ${
                  isSelected ? 'bg-slate-900 text-white border-slate-900' : c.color
                }`}
              >
                {c.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Candidates Results Counter */}
      <div className="flex items-center justify-between text-xs font-bold text-slate-500">
        <span>Mostrando {paginatedCandidates.length} de {filteredCandidates.length} candidatos</span>
        <div className="flex items-center gap-1.5">
          <span>Por página:</span>
          {[12, 24, 48].map(size => (
            <button
              key={size}
              onClick={() => { setPageSize(size); setCurrentPage(1); }}
              className={`px-2 py-0.5 rounded font-bold text-xs ${
                pageSize === size ? 'bg-red-600 text-white' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
              }`}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      {/* Candidates Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-center space-y-3">
          <div className="w-10 h-10 border-4 border-red-500/20 border-t-[#E51636] rounded-full animate-spin" />
          <p className="text-sm font-bold text-slate-600">Cargando candidatos a 0ms...</p>
        </div>
      ) : error ? (
        <div className="p-8 bg-red-50 rounded-2xl border border-red-200 text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
          <h3 className="font-extrabold text-red-800 text-base">Error al cargar candidatos</h3>
          <p className="text-xs text-red-600 max-w-md mx-auto">{error}</p>
          <button
            onClick={() => fetchCandidates(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-bold hover:bg-red-700"
          >
            Reintentar
          </button>
        </div>
      ) : paginatedCandidates.length === 0 ? (
        <div className="py-16 bg-white rounded-2xl border border-slate-200 text-center space-y-2">
          <Award className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="font-extrabold text-slate-700 text-sm">No se encontraron candidatos</h3>
          <p className="text-xs text-slate-400">Intenta cambiar los términos de búsqueda o filtros seleccionados.</p>
          <button
            onClick={clearFilters}
            className="mt-2 text-xs font-bold text-red-600 hover:underline"
          >
            Limpiar Filtros
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {paginatedCandidates.map((candidate, idx) => {
            const score = candidate.overall_score || candidate.score || 0
            const cls = (candidate.classification || 'GOLD').toUpperCase()

            const badgeClass =
              cls === 'GOLD' ? 'bg-amber-100 text-amber-800 border-amber-300' :
              cls === 'IDEAL' ? 'bg-emerald-100 text-emerald-800 border-emerald-300' :
              cls === 'POTENTIAL' ? 'bg-blue-100 text-blue-800 border-blue-300' :
              'bg-rose-100 text-rose-800 border-rose-300'

            return (
              <div
                key={candidate.uuid || candidate.id || idx}
                className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Card Header: Name + Classification Badge */}
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="font-extrabold text-slate-900 text-base leading-tight">
                        {candidate.name || 'Sin Nombre'}
                      </h3>
                      <p className="text-xs font-semibold text-slate-500 mt-0.5">
                        {candidate.position || 'Position'}
                      </p>
                    </div>
                    <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border shrink-0 ${badgeClass}`}>
                      {cls}
                    </span>
                  </div>

                  {/* Score Highlight Box */}
                  <div className="mt-4 p-3 bg-slate-50 rounded-xl border border-slate-100 grid grid-cols-3 gap-2 text-center">
                    <div>
                      <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Score Total</div>
                      <div className="text-lg font-extrabold text-slate-900 mt-0.5">{score}%</div>
                    </div>
                    <div>
                      <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Distancia</div>
                      <div className="text-lg font-extrabold text-slate-700 mt-0.5">
                        {candidate.distance_miles ? `${candidate.distance_miles}m` : `${candidate.distance_score ?? 10}p`}
                      </div>
                    </div>
                    <div>
                      <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">AI Score</div>
                      <div className="text-lg font-extrabold text-slate-700 mt-0.5">{candidate.ai_score ?? '-'}</div>
                    </div>
                  </div>

                  {/* Metadata details */}
                  <div className="mt-3 space-y-1 text-xs text-slate-500">
                    {candidate.address && (
                      <div className="flex items-center gap-1.5 truncate" title={candidate.address}>
                        <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate">{candidate.address}</span>
                      </div>
                    )}
                    {candidate.applied_date && (
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span>Postulado: {candidate.applied_date}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Card Action */}
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                  {candidate.phone ? (
                    <a
                      href={`tel:${candidate.phone}`}
                      className="text-xs font-bold text-slate-600 hover:text-slate-900 flex items-center gap-1"
                    >
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>{candidate.phone}</span>
                    </a>
                  ) : <span />}

                  <button
                    onClick={() => setActiveModalCandidate(candidate)}
                    className="px-3.5 py-1.5 bg-slate-900 hover:bg-[#E51636] text-white text-xs font-bold rounded-xl transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Ver Evaluación</span>
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-1.5 pt-4">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
          >
            « Anterior
          </button>
          
          <span className="px-3 py-1.5 text-xs font-bold text-slate-600">
            Página {currentPage} de {totalPages}
          </span>

          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
          >
            Siguiente »
          </button>
        </div>
      )}

      {/* Evaluation Modal */}
      {activeModalCandidate && (
        <EvaluationModal
          candidate={activeModalCandidate}
          onClose={() => setActiveModalCandidate(null)}
        />
      )}
    </div>
  )
}
