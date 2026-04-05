import React, { useState, useEffect } from 'react'
import { Zap, RefreshCw, ChevronDown, ChevronRight, Tag, Brain, Clock, Shield, BookOpen, ToggleLeft, ToggleRight } from 'lucide-react'
import { useStore } from '../store'
import { skillsApi } from '../api/client'

function SkillCard({ skill, projectId, onToggle }) {
  const [expanded, setExpanded] = useState(false)
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(false)

  const isEnabled = !skill.enabled_projects?.length || skill.enabled_projects.includes(projectId)

  const handleExpand = async () => {
    if (!expanded && !details) {
      setLoading(true)
      try {
        const res = await skillsApi.get(skill.name)
        setDetails(res.data)
      } catch (err) {
        console.error('Failed to load skill details:', err)
      }
      setLoading(false)
    }
    setExpanded(!expanded)
  }

  return (
    <div className={`border rounded-lg overflow-hidden ${isEnabled ? 'border-gray-700 bg-gray-800' : 'border-gray-800 bg-gray-900 opacity-60'}`}>
      <div className="flex items-start gap-3 p-4">
        <div className="w-8 h-8 rounded-lg bg-brand-900 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Zap className="w-4 h-4 text-brand-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-white">{skill.name}</h3>
            {skill.is_bundled && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">bundled</span>
            )}
            {skill.schedulable && (
              <Clock className="w-3 h-3 text-amber-400" title="Schedulable" />
            )}
            {skill.project_aware && (
              <Shield className="w-3 h-3 text-green-400" title="Project-aware" />
            )}
          </div>
          <p className="text-xs text-gray-400 mt-1 line-clamp-2">{skill.description}</p>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {skill.tags?.map((tag) => (
              <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-500">
                {tag}
              </span>
            ))}
          </div>
          {(skill.memory_reads?.length > 0 || skill.memory_writes?.length > 0) && (
            <div className="flex items-center gap-2 mt-2 text-[10px] text-gray-500">
              <Brain className="w-3 h-3" />
              {skill.memory_reads?.length > 0 && <span>reads: {skill.memory_reads.join(', ')}</span>}
              {skill.memory_writes?.length > 0 && <span>writes: {skill.memory_writes.join(', ')}</span>}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => onToggle(skill.name, !isEnabled)}
            title={isEnabled ? 'Disable for this project' : 'Enable for this project'}
            className="text-gray-400 hover:text-white transition-colors"
          >
            {isEnabled ? (
              <ToggleRight className="w-5 h-5 text-brand-400" />
            ) : (
              <ToggleLeft className="w-5 h-5" />
            )}
          </button>
          <button
            onClick={handleExpand}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-700 px-4 py-3 bg-gray-850 space-y-3">
          {loading ? (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <RefreshCw className="w-3 h-3 animate-spin" /> Loading...
            </div>
          ) : details ? (
            <>
              <div>
                <h4 className="text-xs font-medium text-gray-400 mb-1">Triggers</h4>
                <div className="flex flex-wrap gap-1">
                  {details.triggers?.map((t, i) => (
                    <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-brand-900 text-brand-300">"{t}"</span>
                  ))}
                </div>
              </div>
              {details.parameters?.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-gray-400 mb-1">Parameters</h4>
                  {details.parameters.map((p, i) => (
                    <div key={i} className="text-xs text-gray-300 ml-2">
                      <span className="font-mono text-green-300">{p.name}</span>
                      <span className="text-gray-500"> ({p.type}){p.required ? ' *' : ''}</span>
                      {p.description && <span className="text-gray-500"> — {p.description}</span>}
                    </div>
                  ))}
                </div>
              )}
              {details.instructions && (
                <div>
                  <h4 className="text-xs font-medium text-gray-400 mb-1 flex items-center gap-1">
                    <BookOpen className="w-3 h-3" /> Instructions
                  </h4>
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap bg-gray-900 rounded p-2 max-h-60 overflow-y-auto scrollbar-thin">
                    {details.instructions}
                  </pre>
                </div>
              )}
              <div className="text-[10px] text-gray-600">
                v{details.version} · {details.author} · {details.skill_dir}
              </div>
            </>
          ) : (
            <p className="text-xs text-gray-500">No details available</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function Skills() {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)
  const [reloading, setReloading] = useState(false)
  const activeProject = useStore((s) => s.activeProject)
  const addNotification = useStore((s) => s.addNotification)

  const projectId = activeProject?.id || 'default'

  const loadSkills = async () => {
    try {
      const res = await skillsApi.list(projectId)
      setSkills(res.data.skills || [])
    } catch (err) {
      addNotification({ type: 'error', message: `Failed to load skills: ${err.message}` })
    }
    setLoading(false)
  }

  useEffect(() => {
    loadSkills()
  }, [projectId])

  const handleReload = async () => {
    setReloading(true)
    try {
      const res = await skillsApi.reload()
      addNotification({ type: 'success', message: `Reloaded ${res.data.count} skills` })
      await loadSkills()
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setReloading(false)
  }

  const handleToggle = async (skillName, enabled) => {
    try {
      await skillsApi.toggle(skillName, projectId, enabled)
      addNotification({ type: 'success', message: `${skillName} ${enabled ? 'enabled' : 'disabled'}` })
      await loadSkills()
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6 scrollbar-thin">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-brand-400" />
            <h1 className="text-lg font-semibold text-white">Skills Library</h1>
            <span className="text-xs text-gray-500">{skills.length} skills</span>
          </div>
          <button
            onClick={handleReload}
            disabled={reloading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gray-800 hover:bg-gray-700 text-xs text-gray-300 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${reloading ? 'animate-spin' : ''}`} />
            Reload
          </button>
        </div>

        <p className="text-sm text-gray-400 mb-6">
          Skills extend agent capabilities with specialised procedures. Use <code className="text-brand-300 bg-gray-800 px-1 rounded">/skill-name</code> in chat to invoke explicitly,
          or enable Auto-Skill discovery in the chat header to let the agent match skills automatically.
        </p>

        {loading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <RefreshCw className="w-4 h-4 animate-spin" /> Loading skills...
          </div>
        ) : skills.length === 0 ? (
          <div className="text-center py-12 text-gray-600">
            <Zap className="w-8 h-8 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No skills found.</p>
            <p className="text-xs mt-1">Add skill directories to <code>skills/</code> or <code>data/skills/</code>.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {skills.map((skill) => (
              <SkillCard
                key={skill.name}
                skill={skill}
                projectId={projectId}
                onToggle={handleToggle}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
