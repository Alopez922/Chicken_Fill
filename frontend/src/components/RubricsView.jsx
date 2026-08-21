import React, { useState, useEffect } from 'react'
import { FileText, Award, Layers } from 'lucide-react'

export default function RubricsView() {
  const [positions, setPositions] = useState([])
  const [selectedPos, setSelectedPos] = useState('')
  const [criteria, setCriteria] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch('/api/rubrics')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.positions?.length > 0) {
          setPositions(data.positions)
          setSelectedPos(data.positions[0])
        }
      })
      .catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedPos) return
    setLoading(true)
    fetch(`/api/rubrics/${encodeURIComponent(selectedPos)}`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setCriteria(data.criteria || [])
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedPos])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
          <FileText className="w-5 h-5 text-red-600" />
          <span>Framework Oficial de Puntuación (Candidate Screening Matrix)</span>
        </h2>
        <p className="text-xs text-slate-500 font-medium mt-1">
          Consulta los pesos, respuestas ideales y descalificaciones directas por cada posición oficial de Chick-fil-A.
        </p>

        {/* Position Selector Tabs */}
        <div className="mt-4 flex flex-wrap gap-2">
          {positions.map((pos) => (
            <button
              key={pos}
              onClick={() => setSelectedPos(pos)}
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all ${
                selectedPos === pos
                  ? 'bg-gradient-to-r from-[#E51636] to-[#B80028] text-white shadow-md shadow-red-600/20'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
              }`}
            >
              {pos}
            </button>
          ))}
        </div>
      </div>

      {/* Criteria Table */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
        <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-400" />
          <span>Rúbrica de Evaluación: {selectedPos} ({criteria.length} Criterios)</span>
        </h3>

        {loading ? (
          <div className="py-12 text-center text-xs font-bold text-slate-500">
            Cargando criterios de la matriz...
          </div>
        ) : criteria.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No se encontraron criterios para este puesto.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                <tr>
                  {Object.keys(criteria[0] || {}).map((col, idx) => (
                    <th key={idx} className="p-3 uppercase tracking-wider text-[11px]">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {criteria.map((row, rowIdx) => (
                  <tr key={rowIdx} className="hover:bg-slate-50">
                    {Object.values(row).map((val, cellIdx) => (
                      <td key={cellIdx} className="p-3 text-slate-700 font-medium">
                        {String(val ?? '-')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
