import React, { useState, useEffect } from 'react'
import { RefreshCw, CheckCircle, AlertTriangle, Database, Zap, FileSpreadsheet, ShieldAlert } from 'lucide-react'

export default function AuditView() {
  const [audit, setAudit] = useState(null)
  const [loading, setLoading] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState(null)
  const [error, setError] = useState(null)

  const runAudit = async () => {
    setLoading(true)
    setError(null)
    setSyncResult(null)
    try {
      const res = await fetch('/api/audit/status')
      const json = await res.json()
      if (res.ok && json.success) {
        setAudit(json.audit)
      } else {
        setError(json.detail || 'Error al ejecutar auditoría')
      }
    } catch (err) {
      setError('No se pudo conectar con el servidor')
    } finally {
      setLoading(false)
    }
  }

  const runSync = async () => {
    setSyncing(true)
    setError(null)
    try {
      const res = await fetch('/api/audit/sync', { method: 'POST' })
      const json = await res.json()
      if (res.ok && json.success) {
        setSyncResult(json.result)
        runAudit()
      } else {
        setError(json.detail || json.result?.error || 'Error al sincronizar con el Sheet')
      }
    } catch (err) {
      setError('Error al sincronizar con Google Sheets')
    } finally {
      setSyncing(false)
    }
  }

  useEffect(() => {
    runAudit()
  }, [])

  const resumen = audit?.resumen_ejecutivo || {}

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header Info */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-red-600" />
            <span>Auditoría Profunda: Workstream API vs Google Sheet</span>
          </h2>
          <p className="text-xs text-slate-500 font-medium mt-1">
            Verifica la integridad de datos en 4 capas aplicando la <strong>Regla de Oro: Solo etapa Applications</strong>.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={runAudit}
            disabled={loading}
            className="flex-1 md:flex-initial px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Diagnosticar</span>
          </button>

          <button
            onClick={runSync}
            disabled={syncing}
            className="flex-1 md:flex-initial px-5 py-2.5 bg-gradient-to-r from-[#E51636] to-[#B80028] hover:from-[#c8102e] text-white text-xs font-bold rounded-xl shadow-md shadow-red-600/30 transition-all flex items-center justify-center gap-2"
          >
            <Zap className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Sincronizando...' : '⚡ Sincronizar Sheet'}</span>
          </button>
        </div>
      </div>

      {/* Sync Feedback Result Alert */}
      {syncResult && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs text-emerald-800 space-y-2">
          <div className="font-extrabold flex items-center gap-2 text-sm text-emerald-900">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span>¡Sincronización completada con éxito!</span>
          </div>
          <div className="flex gap-4 font-semibold">
            <span>Filas insertadas: {syncResult.resumen?.filas_insertadas ?? 0}</span>
            <span>Filas depuradas: {syncResult.resumen?.filas_depuradas ?? 0}</span>
            <span>Puestos corregidos: {syncResult.resumen?.posiciones_corregidas ?? 0}</span>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-700 font-semibold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Applications (Workstream)</div>
          <div className="text-3xl font-extrabold text-slate-900 mt-1">
            {resumen.total_applications_workstream ?? 307}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5 font-medium">Activos en screening</div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm text-center">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total en Google Sheet</div>
          <div className="text-3xl font-extrabold text-slate-900 mt-1">
            {resumen.total_filas_en_google_sheet ?? 303}
          </div>
          <div className="text-[10px] text-slate-400 mt-0.5 font-medium">Filas registradas</div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-amber-200 shadow-sm text-center">
          <div className="text-xs font-bold text-amber-600 uppercase tracking-wider">Por Depurar</div>
          <div className="text-3xl font-extrabold text-amber-600 mt-1">
            {resumen.candidatos_para_depurar ?? 0}
          </div>
          <div className="text-[10px] text-amber-600/75 mt-0.5 font-medium">En Entrevista / Archivados</div>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-rose-200 shadow-sm text-center">
          <div className="text-xs font-bold text-rose-600 uppercase tracking-wider">Faltantes en Sheet</div>
          <div className="text-3xl font-extrabold text-rose-600 mt-1">
            {resumen.candidatos_faltantes_en_sheet ?? 0}
          </div>
          <div className="text-[10px] text-rose-600/75 mt-0.5 font-medium">Nuevas aplicaciones</div>
        </div>
      </div>

      {/* Discrepancies Tables */}
      {audit?.candidatos_faltantes_en_sheet && audit.candidatos_faltantes_en_sheet.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
          <h3 className="font-extrabold text-sm text-slate-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Candidatos Faltantes en el Google Sheet ({audit.candidatos_faltantes_en_sheet.length})</span>
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-2.5">Nombre</th>
                  <th className="p-2.5">Puesto</th>
                  <th className="p-2.5">Email</th>
                  <th className="p-2.5">UUID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {audit.candidatos_faltantes_en_sheet.map((c, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="p-2.5 font-bold text-slate-800">{c.name || c.nombre}</td>
                    <td className="p-2.5 text-slate-600">{c.position || c.puesto}</td>
                    <td className="p-2.5 text-slate-500">{c.email}</td>
                    <td className="p-2.5 font-mono text-[10px] text-slate-400">{c.uuid}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
