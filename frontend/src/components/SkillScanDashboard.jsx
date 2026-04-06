import React, { useState, useEffect } from 'react'
import { ShieldCheck, ShieldAlert, ShieldX, ShieldQuestion, ScanSearch, RefreshCw, AlertTriangle, Package } from 'lucide-react'
import { useStore } from '../store'
import { skillsApi } from '../api/client'

const STATUS_CONFIG = {
  passed: { icon: ShieldCheck, color: 'text-green-400', bg: 'bg-green-900/30', label: 'Passed' },
  failed: { icon: ShieldX, color: 'text-red-400', bg: 'bg-red-900/30', label: 'Failed' },
  unscanned: { icon: ShieldQuestion, color: 'text-gray-500', bg: 'bg-gray-800', label: 'Unscanned' },
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.unscanned
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded ${cfg.bg} ${cfg.color}`}>
      <Icon className="w-3 h-3" /> {cfg.label}
    </span>
  )
}

function CountCard({ label, count, icon: Icon, color, total }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500">{label}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`text-2xl font-bold ${color}`}>{count}</span>
        <span className="text-xs text-gray-600">/ {total} ({pct}%)</span>
      </div>
    </div>
  )
}

export default function SkillScanDashboard() {
  const [summary, setSummary] = useState(null)
  const [quarantined, setQuarantined] = useState([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const addNotification = useStore((s) => s.addNotification)

  const loadData = async () => {
    try {
      const [summaryRes, quarantineRes] = await Promise.all([
        skillsApi.scanSummary(),
        skillsApi.listQuarantined(),
      ])
      setSummary(summaryRes.data)
      setQuarantined(quarantineRes.data.quarantined || [])
    } catch (err) {
      addNotification({ type: 'error', message: `Failed to load scan data: ${err.message}` })
    }
    setLoading(false)
  }

  useEffect(() => { loadData() }, [])

  const handleScanAll = async () => {
    setScanning(true)
    try {
      const res = await skillsApi.scanAll(false) // fast scan, no AI review
      const d = res.data
      addNotification({
        type: d.failed > 0 ? 'warning' : 'success',
        message: `Scan complete: ${d.passed} passed, ${d.failed} failed, ${d.errors} errors`,
      })
      await loadData()
    } catch (err) {
      addNotification({ type: 'error', message: `Scan all failed: ${err.message}` })
    }
    setScanning(false)
  }

  const handleUnquarantine = async (skillName) => {
    try {
      await skillsApi.unquarantine(skillName)
      addNotification({ type: 'success', message: `${skillName} restored from quarantine` })
      await loadData()
    } catch (err) {
      addNotification({ type: 'error', message: `Restore failed: ${err.message}` })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 text-sm gap-2">
        <RefreshCw className="w-4 h-4 animate-spin" /> Loading scan data...
      </div>
    )
  }

  const counts = summary?.counts || { total: 0, passed: 0, failed: 0, unscanned: 0 }
  const skills = summary?.skills || []

  // Sort: failed first, then unscanned, then passed
  const sortOrder = { failed: 0, unscanned: 1, passed: 2 }
  const sorted = [...skills].sort((a, b) => {
    const ao = sortOrder[a.scan_status] ?? 1
    const bo = sortOrder[b.scan_status] ?? 1
    if (ao !== bo) return ao - bo
    return (b.risk_score || 0) - (a.risk_score || 0)
  })

  return (
    <div className="h-full overflow-y-auto p-6 scrollbar-thin">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ScanSearch className="w-5 h-5 text-brand-400" />
            <h1 className="text-lg font-semibold text-white">Security Dashboard</h1>
          </div>
          <button
            onClick={handleScanAll}
            disabled={scanning}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-brand-900 hover:bg-brand-800 text-xs text-brand-300 transition-colors disabled:opacity-50"
          >
            {scanning ? (
              <><RefreshCw className="w-3 h-3 animate-spin" /> Scanning...</>
            ) : (
              <><ScanSearch className="w-3 h-3" /> Scan All Skills</>
            )}
          </button>
        </div>

        {/* Summary cards */}
        <div className="grid grid-cols-4 gap-3">
          <CountCard label="Total Skills" count={counts.total} icon={Package} color="text-gray-300" total={counts.total} />
          <CountCard label="Passed" count={counts.passed} icon={ShieldCheck} color="text-green-400" total={counts.total} />
          <CountCard label="Failed" count={counts.failed} icon={ShieldX} color="text-red-400" total={counts.total} />
          <CountCard label="Unscanned" count={counts.unscanned} icon={ShieldQuestion} color="text-gray-500" total={counts.total} />
        </div>

        {/* Skills table */}
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <div className="px-4 py-2.5 border-b border-gray-700 bg-gray-850">
            <h2 className="text-xs font-medium text-gray-400">All Skills</h2>
          </div>
          <div className="divide-y divide-gray-750">
            {sorted.map((skill) => (
              <div key={skill.name} className="flex items-center gap-4 px-4 py-2.5 hover:bg-gray-750 transition-colors">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-white font-medium">{skill.name}</span>
                    {skill.is_bundled && (
                      <span className="text-[9px] px-1 py-0 rounded bg-gray-700 text-gray-500">bundled</span>
                    )}
                    {skill.has_scripts && (
                      <span className="text-[9px] px-1 py-0 rounded bg-amber-900/40 text-amber-500">has scripts</span>
                    )}
                  </div>
                  {skill.scanned_at && (
                    <span className="text-[10px] text-gray-600">
                      Scanned {new Date(skill.scanned_at).toLocaleString()}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {skill.findings_count > 0 && (
                    <span className="text-[10px] text-gray-500">{skill.findings_count} findings</span>
                  )}
                  {skill.risk_score != null && skill.risk_score > 0 && (
                    <span className={`text-[10px] font-mono ${skill.risk_score >= 0.5 ? 'text-red-400' : 'text-amber-400'}`}>
                      risk: {skill.risk_score}
                    </span>
                  )}
                  <StatusBadge status={skill.scan_status} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quarantine section */}
        {quarantined.length > 0 && (
          <div className="bg-red-950/20 rounded-lg border border-red-900/40 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-red-900/30">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <h2 className="text-xs font-medium text-red-400">Quarantined Skills ({quarantined.length})</h2>
            </div>
            <div className="divide-y divide-red-900/20">
              {quarantined.map((q) => (
                <div key={q.name} className="flex items-center justify-between px-4 py-2.5">
                  <div>
                    <span className="text-sm text-red-300">{q.name}</span>
                    {q.description && <p className="text-[10px] text-gray-600 mt-0.5">{q.description}</p>}
                  </div>
                  <button
                    onClick={() => handleUnquarantine(q.name)}
                    className="text-[11px] px-2.5 py-1 rounded bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
                  >
                    Restore
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
