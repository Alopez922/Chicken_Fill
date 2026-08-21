import React from 'react'
import { X, MapPin, Phone, Briefcase, GraduationCap, Award, Lightbulb, CheckCircle2 } from 'lucide-react'

export default function EvaluationModal({ candidate, onClose }) {
  if (!candidate) return null

  const isSA = (candidate.position || candidate.puesto || '').toLowerCase().includes('system')
  const sa = candidate.competency_profile || candidate.sa_details?.competency_profile || {}
  const openItems = candidate.open_text_items || []
  const choiceItems = candidate.choice_items || []

  const overallScore = candidate.overall_score || candidate.score || 0
  const choiceScore = candidate.choice_score ?? candidate.puntaje_choice ?? 0
  const aiScore = candidate.ai_score ?? candidate.puntaje_ia ?? 0
  const distanceMiles = candidate.distance_miles ?? candidate.distancia_millas ?? 0
  const distanceScore = candidate.distance_score ?? candidate.puntaje_distancia ?? 10
  const totalPts = candidate.total_points ?? candidate.puntaje_total ?? 0
  const maxPts = candidate.max_points ?? candidate.maximo_posible ?? 100

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white w-full max-w-3xl max-h-[92vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-200">
        
        {/* Header */}
        <div className="p-6 pb-4 border-b border-slate-100 flex items-start justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-extrabold text-slate-900">
                {candidate.name || candidate.nombre}
              </h2>
              <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                candidate.classification === 'GOLD' ? 'bg-amber-50 text-amber-700 border-amber-300' :
                candidate.classification === 'IDEAL' ? 'bg-emerald-50 text-emerald-700 border-emerald-300' :
                candidate.classification === 'POTENTIAL' ? 'bg-blue-50 text-blue-700 border-blue-300' :
                'bg-rose-50 text-rose-700 border-rose-300'
              }`}>
                {candidate.classification}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-500 mt-1.5">
              <span>{candidate.position || candidate.puesto}</span>
              {distanceMiles > 0 && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-red-500" />
                  {distanceMiles} mi
                </span>
              )}
              {candidate.phone && candidate.phone !== '—' && (
                <span className="flex items-center gap-1">
                  <Phone className="w-3.5 h-3.5 text-slate-400" />
                  {candidate.phone}
                </span>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs">
          
          {/* 4 KPI Metrics Header */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl border border-amber-200 bg-white text-center shadow-xs">
              <div className="text-2xl font-extrabold text-[#E51636]">{overallScore}%</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">FINAL SCORE</div>
              <div className="text-[10px] text-slate-400 font-medium">{totalPts} / {maxPts} pts</div>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-white text-center shadow-xs">
              <div className="text-2xl font-extrabold text-slate-800">{choiceScore}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">CHOICE SCORE</div>
              <div className="text-[10px] text-slate-400 font-medium">multiple choice</div>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-white text-center shadow-xs">
              <div className="text-2xl font-extrabold text-slate-800">{aiScore}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">AI SCORE</div>
              <div className="text-[10px] text-slate-400 font-medium">open-text eval</div>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200 bg-white text-center shadow-xs">
              <div className="text-2xl font-extrabold text-slate-800">{distanceScore}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">DISTANCE</div>
              <div className="text-[10px] text-slate-400 font-medium">{distanceMiles} mi</div>
            </div>
          </div>

          {/* CFA Alumni Experience Banner */}
          {candidate.has_cfa_experience && (
            <div className="p-4 bg-gradient-to-r from-red-50 via-amber-50/50 to-red-50 border-2 border-red-300 rounded-2xl flex items-start gap-3 shadow-xs">
              <div className="w-8 h-8 rounded-full bg-[#E51636] text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-sm">
                🍗
              </div>
              <div>
                <h4 className="font-extrabold text-red-950 text-xs uppercase tracking-wider">
                  Experiencia Previa en Chick-fil-A (CFA Alumni)
                </h4>
                <p className="text-xs text-red-900 font-medium mt-1 leading-relaxed">
                  {candidate.cfa_experience_detail || 'Candidato con historial laboral comprobado en restaurantes Chick-fil-A.'}
                </p>
              </div>
            </div>
          )}

          {/* Multi-Applications Alert Banner */}
          {candidate.is_multi_applicant && (
            <div className="p-3.5 bg-indigo-50 border border-indigo-200 rounded-2xl flex items-start gap-3 text-xs text-indigo-900 font-medium">
              <span className="text-base shrink-0">📑</span>
              <div>
                <strong className="text-indigo-950 block">Aviso de Multi-Postulación ({candidate.applied_positions?.length} puestos detectados):</strong>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {candidate.applied_positions?.map((p, i) => (
                    <span key={i} className="px-2.5 py-1 bg-white border border-indigo-200 rounded-lg text-[11px] font-bold text-indigo-700 shadow-2xs">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Systems Analyst Competency Box (Screenshot 3 style) */}
          {isSA && (
            <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-extrabold text-amber-900 text-xs uppercase tracking-wider">
                  <span>💼 SYSTEMS ANALYST COMPETENCY PROFILE</span>
                </div>
                <span className="text-[11px] font-extrabold px-2.5 py-0.5 bg-emerald-100 text-emerald-800 rounded-full border border-emerald-200">
                  {overallScore}/100 pts
                </span>
              </div>

              <div className="space-y-2 text-xs text-slate-700">
                <div className="flex items-start gap-2">
                  <span className="font-bold text-slate-800 shrink-0 w-28">💼 IT Experience:</span>
                  <span className="font-medium text-slate-700">
                    {sa.it_experience || sa.it_experience_years || '17+ años en soporte TI y administración de sistemas'}
                  </span>
                </div>

                <div className="flex items-start gap-2">
                  <span className="font-bold text-slate-800 shrink-0 w-28">🎓 Field of Study:</span>
                  <span className="font-medium text-slate-700">
                    {sa.field_of_study || "Bachelor's of Science - Computer Information Systems; Master's Business Administration"}
                  </span>
                </div>

                <div className="flex items-start gap-2">
                  <span className="font-bold text-slate-800 shrink-0 w-28">📜 Certifications:</span>
                  <span className="font-medium text-slate-700">
                    {sa.certifications || 'Ninguna detectada'}
                  </span>
                </div>

                <div className="p-3 bg-white/80 rounded-xl border border-amber-200/80 mt-2 flex items-start gap-2.5">
                  <Lightbulb className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <p className="text-[11px] text-slate-700 font-medium leading-relaxed">
                    <strong className="text-slate-900">AI Analysis:</strong> {sa.ai_analysis || candidate.summary || 'Especialista sénior con amplia experiencia técnica calificada para el perfil de Systems Analyst.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Open Text Questions Section (Screenshot 4 & 5 style) */}
          {openItems.length > 0 && (
            <div className="space-y-4">
              <h3 className="font-extrabold text-xs text-slate-700 uppercase tracking-wider">
                💬 RESPUESTAS A PREGUNTAS ABIERTAS ({openItems.length})
              </h3>

              <div className="space-y-4">
                {openItems.map((q, idx) => (
                  <div key={idx} className="space-y-1.5">
                    <div className="font-bold text-xs text-slate-900">
                      {q.question}
                    </div>

                    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 font-normal leading-relaxed">
                      "{q.answer}"
                    </div>

                    {q.score !== null && q.score !== undefined && (
                      <div className="text-[11px] text-slate-500 font-medium pl-1">
                        Evaluación: {q.reason ? `${q.reason}: ` : ''}
                        <strong className="text-slate-800">{q.score}/{q.max_score ?? 10.0} pts</strong>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Multiple Choice Section */}
          {choiceItems.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-slate-100">
              <h3 className="font-extrabold text-xs text-slate-700 uppercase tracking-wider">
                📋 PREGUNTAS DE OPCIÓN MÚLTIPLE ({choiceItems.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {choiceItems.map((c, i) => (
                  <div key={i} className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between gap-2">
                    <div className="truncate">
                      <p className="font-bold text-slate-800 truncate text-[11px]">{c.question}</p>
                      <p className="text-[10px] text-slate-500 truncate">{c.answer}</p>
                    </div>
                    <span className="text-[10px] font-extrabold px-2 py-0.5 bg-white border border-slate-200 rounded-lg shrink-0">
                      {c.score} pts
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition-all"
          >
            Cerrar
          </button>
        </div>

      </div>
    </div>
  )
}
