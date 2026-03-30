import React, { useState, useEffect } from 'react'
import { Save, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useStore } from '../store'
import { personalityApi } from '../api/client'

export default function PersonalityEditor() {
  const [activeTab, setActiveTab] = useState('soul')
  const [soulContent, setSoulContent] = useState('')
  const [agentContent, setAgentContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const activeProject = useStore((s) => s.activeProject)
  const addNotification = useStore((s) => s.addNotification)

  const loadPersonality = async () => {
    setLoading(true)
    try {
      const [soulRes, agentRes] = await Promise.all([
        personalityApi.getSoul(activeProject?.id || 'default'),
        personalityApi.getAgent(activeProject?.id || 'default'),
      ])
      setSoulContent(soulRes.data.content || '')
      setAgentContent(agentRes.data.content || '')
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setLoading(false)
  }

  useEffect(() => {
    loadPersonality()
  }, [activeProject])

  const saveSoul = async () => {
    setSaving(true)
    try {
      await personalityApi.updateSoul(soulContent, activeProject?.id || 'default')
      addNotification({ type: 'success', message: 'Soul saved' })
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setSaving(false)
  }

  const saveAgent = async () => {
    setSaving(true)
    try {
      await personalityApi.updateAgent(agentContent, activeProject?.id || 'default')
      addNotification({ type: 'success', message: 'Agent prompt saved' })
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setSaving(false)
  }

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-900 border-b border-gray-800">
        <h1 className="text-xl font-bold text-gray-100">Personality Editor</h1>
        <p className="text-sm text-gray-500 mt-1">Configure the agent's soul and behavioral prompts</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-gray-800">
        <button
          onClick={() => setActiveTab('soul')}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'soul'
              ? 'border-brand-500 text-brand-400'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          Soul (soul.md)
        </button>
        <button
          onClick={() => setActiveTab('agent')}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'agent'
              ? 'border-brand-500 text-brand-400'
              : 'border-transparent text-gray-400 hover:text-gray-300'
          }`}
        >
          Agent Prompt (agent.md)
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Editor */}
        <div className="flex-1 flex flex-col border-r border-gray-800">
          <textarea
            value={activeTab === 'soul' ? soulContent : agentContent}
            onChange={(e) => {
              if (activeTab === 'soul') {
                setSoulContent(e.target.value)
              } else {
                setAgentContent(e.target.value)
              }
            }}
            disabled={loading}
            className="flex-1 w-full resize-none bg-gray-800 text-gray-100 p-4 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50 scrollbar-thin"
            placeholder={activeTab === 'soul'
              ? "Define the agent's core values, personality traits, and principles in Markdown..."
              : "Write detailed behavioral instructions and system prompts in Markdown..."
            }
          />

          {/* Action bar */}
          <div className="px-4 py-3 bg-gray-900 border-t border-gray-800 flex gap-2">
            <button
              onClick={() => loadPersonality()}
              disabled={loading || saving}
              className="flex items-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg disabled:opacity-50"
            >
              <RefreshCw className="w-4 h-4" />
              Reload
            </button>
            <button
              onClick={activeTab === 'soul' ? saveSoul : saveAgent}
              disabled={loading || saving}
              className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm rounded-lg disabled:opacity-50 ml-auto"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>

        {/* Preview */}
        <div className="w-1/2 flex flex-col bg-gray-900 border-l border-gray-800">
          <div className="px-4 py-3 border-b border-gray-800">
            <p className="text-sm font-medium text-gray-300">Preview</p>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              className="prose prose-invert prose-sm max-w-none"
              components={{
                code: ({ node, inline, className, children, ...props }) => {
                  if (inline) {
                    return <code className="bg-gray-800 px-1 py-0.5 rounded text-xs font-mono" {...props}>{children}</code>
                  }
                  return (
                    <pre className="bg-gray-950 rounded-lg p-3 overflow-x-auto">
                      <code className="text-green-300 text-xs font-mono" {...props}>{children}</code>
                    </pre>
                  )
                },
              }}
            >
              {activeTab === 'soul' ? soulContent : agentContent}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  )
}
