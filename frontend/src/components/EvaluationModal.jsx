import React from 'react'
import { X, Award, CheckCircle2, AlertTriangle, XCircle, MapPin, Phone, Mail, Clock, ShieldAlert } from 'lucide-react'

export default function EvaluationModal({ candidate, onClose }) {
  if (!candidate) return null

  const getScoreColor = (score) => {
    if (score >= 97) return 'text-amber-600 bg-amber-50 border-amber-200'
    if (score >= 75) return 'text-emerald-600 bg-emerald-50 border-emerald-200'
    if (score >= 50) return 'text-blue-600 bg-blue-50 border-blue-200'
    return 'text-rose-600 bg-rose-50 border-rose-200'
  }

  const isSA = candidate.position?.toLowerCase().includes('systems analyst')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white w-full max-w-2xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-200 animate-scaleUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#E51636] to-[#B80028] text-white p-5 flex items-start justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-extrabold">{candidate.name || 'Candidato'}</h2>
              <span className="text-xs px-2.5 py-0.5 bg-white/20 rounded-full font-bold">
                {candidate.classification || 'GOLD'}
              </span>
            </div>
            <p className="text-xs text-white/80 font-medium mt-0.5">{candidate.position || 'Position'}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 bg-white/10 hover:bg-white/25 rounded-full text-white transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-5 text-sm">
          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className={`p-3 rounded-xl border ${getScoreColor(candidate.overall_score || candidate.score)} text-center`}>
              <div className="text-[10px] font-bold uppercase tracking-wider">Overall Score</div>
              <div className="text-xl font-extrabold mt-0.5">{candidate.overall_score || candidate.score}%</div>
            </div>
            <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-center">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Choice Points</div>
              <div className="text-xl font-extrabold text-slate-800 mt-0.5">{candidate.choice_score ?? candidate.raw_score ?? '-'}</div>
            </div>
            <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-center">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Distance</div>
              <div className="text-xl font-extrabold text-slate-800 mt-0.5">{candidate.distance_miles ? `${candidate.distance_miles} mi` : candidate.distance_score ?? '-'}</div>
            </div>
            <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-center">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">AI Evaluation</div>
              <div className="text-xl font-extrabold text-slate-800 mt-0.5">{candidate.ai_score ?? '-'}</div>
            </div>
          </div>

          {/* Contact Details */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 text-xs font-medium text-slate-700">
            {candidate.address && (
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
                <span>{candidate.address}</span>
              </div>
            )}
            {candidate.phone && (
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-slate-400 shrink-0" />
                <span>{candidate.phone}</span>
              </div>
            )}
            {candidate.email && (
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-slate-400 shrink-0" />
                <a href={`mailto:${candidate.email}`} className="text-red-600 hover:underline">{candidate.email}</a>
              </div>
            )}
            {candidate.applied_date && (
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-slate-400 shrink-0" />
                <span>Postulado el: {candidate.applied_date}</span>
              </div>
            )}
          </div>

          {/* Systems Analyst Methodology Transparency Note */}
          {isSA && (
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3 text-xs text-amber-800 font-medium">
              <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-amber-900">Nota Metodológica Oficial — Systems Analyst</p>
                <p className="mt-1 text-amber-800/90 leading-relaxed">
                  Evaluación aproximada basada en el cuestionario estándar de Workstream para operadores. Al no contar con rúbrica oficial dedicada para TI en el Sheet de rúbricas, se prioriza educación formal en ciencias computacionales e historial laboral afín.
                </p>
              </div>
            </div>
          )}

          {/* Detailed Q&A Breakdown */}
          {(() => {
            const qList = candidate.details || candidate.qa_breakdown || candidate.parsed_qa || []
            if (qList.length === 0) return null
            return (
              <div>
                <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-3">
                  Desglose de Respuestas & Criterios ({qList.length})
                </h3>
                <div className="space-y-2.5">
                  {qList.map((q, idx) => (
                    <div key={idx} className="p-3 bg-white rounded-xl border border-slate-200 space-y-1.5">
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-bold text-xs text-slate-900">{q.question || q.pregunta || q.question_key || `Pregunta ${idx+1}`}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded font-bold shrink-0 ${
                          (q.score ?? q.points ?? q.puntos ?? 0) > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                        }`}>
                          {q.score ?? q.points ?? q.puntos ?? 0} pts
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded-lg font-mono">
                        {q.answer || q.respuesta || q.answer_option || 'Sin respuesta'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )
          })()}

        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end shrink-0">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold rounded-xl transition-all"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
