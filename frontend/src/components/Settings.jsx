import React, { useState, useEffect } from 'react'
import { Save, Eye, EyeOff, Trash2, Plus, Check, X, RefreshCw } from 'lucide-react'
import { useStore } from '../store'
import { settingsApi } from '../api/client'

function LLMSection() {
  const [settings, setSettings] = useState({ llm_api_url: '', llm_api_key: '', llm_model: '' })
  const [models, setModels] = useState([])
  const [showKey, setShowKey] = useState(false)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testStatus, setTestStatus] = useState(null)
  const addNotification = useStore((s) => s.addNotification)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      const res = await settingsApi.get()
      setSettings({
        llm_api_url: res.data.llm_api_url || '',
        llm_api_key: res.data.llm_api_key || '',
        llm_model: res.data.llm_model || '',
      })
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setLoading(false)
  }

  const fetchModels = async () => {
    setLoading(true)
    try {
      const res = await settingsApi.listModels()
      setModels(res.data.models || [])
      addNotification({ type: 'success', message: 'Models loaded' })
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setLoading(false)
  }

  const testConnection = async () => {
    setTesting(true)
    try {
      await settingsApi.testConnection()
      setTestStatus('success')
      addNotification({ type: 'success', message: 'Connection successful' })
      setTimeout(() => setTestStatus(null), 3000)
    } catch (err) {
      setTestStatus('error')
      addNotification({ type: 'error', message: err.message })
      setTimeout(() => setTestStatus(null), 3000)
    }
    setTesting(false)
  }

  const save = async () => {
    setLoading(true)
    try {
      await settingsApi.update(settings)
      addNotification({ type: 'success', message: 'Settings saved' })
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-gray-200 mb-4">LLM Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">API Endpoint</label>
            <input
              type="text"
              value={settings.llm_api_url}
              onChange={(e) => setSettings({ ...settings, llm_api_url: e.target.value })}
              placeholder="https://api.openai.com/v1"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">API Key</label>
            <div className="flex gap-2">
              <input
                type={showKey ? 'text' : 'password'}
                value={settings.llm_api_key}
                onChange={(e) => setSettings({ ...settings, llm_api_key: e.target.value })}
                placeholder="sk-..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">Model</label>
            <div className="flex gap-2">
              <select
                value={settings.llm_model}
                onChange={(e) => setSettings({ ...settings, llm_model: e.target.value })}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-brand-500"
              >
                <option value="">Select a model...</option>
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
              <button
                onClick={fetchModels}
                disabled={loading}
                className="px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-gray-400 disabled:opacity-50"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={testConnection}
          disabled={testing || loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50"
        >
          {testStatus === 'success' && <Check className="w-4 h-4" />}
          {testStatus === 'error' && <X className="w-4 h-4" />}
          {!testStatus && <RefreshCw className="w-4 h-4" />}
          Test Connection
        </button>
        <button
          onClick={save}
          disabled={loading || testing}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm rounded-lg disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          Save Settings
        </button>
      </div>
    </div>
  )
}

function SecretsSection() {
  const [secrets, setSecrets] = useState([])
  const [newKey, setNewKey] = useState('')
  const [newValue, setNewValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [showValues, setShowValues] = useState({})
  const addNotification = useStore((s) => s.addNotification)

  useEffect(() => {
    loadSecrets()
  }, [])

  const loadSecrets = async () => {
    setLoading(true)
    try {
      const res = await settingsApi.listSecrets()
      setSecrets(res.data.secrets || [])
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setLoading(false)
  }

  const addSecret = async () => {
    if (!newKey.trim() || !newValue.trim()) return
    try {
      await settingsApi.setSecret(newKey, newValue)
      setNewKey('')
      setNewValue('')
      addNotification({ type: 'success', message: 'Secret saved' })
      loadSecrets()
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }

  const deleteSecret = async (key) => {
    if (!confirm(`Delete secret "${key}"?`)) return
    try {
      await settingsApi.deleteSecret(key)
      addNotification({ type: 'success', message: 'Secret deleted' })
      loadSecrets()
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-200">API Secrets & Keys</h3>

      {/* Add new secret */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">Key Name</label>
            <input
              type="text"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              placeholder="TELEGRAM_BOT_TOKEN"
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-2">Value</label>
            <input
              type="password"
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              placeholder="***"
              className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <button
            onClick={addSecret}
            disabled={loading || !newKey.trim() || !newValue.trim()}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Add Secret
          </button>
        </div>
      </div>

      {/* Secrets list */}
      <div className="space-y-2">
        {secrets.length === 0 ? (
          <p className="text-sm text-gray-600 text-center py-4">No secrets configured</p>
        ) : (
          secrets.map((secret) => (
            <div key={secret.key} className="bg-gray-800 rounded-lg p-3 border border-gray-700 flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-mono text-gray-300">{secret.key}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-600">
                    {showValues[secret.key] ? secret.value : '***'.repeat(4)}
                  </span>
                  <button
                    onClick={() => setShowValues({ ...showValues, [secret.key]: !showValues[secret.key] })}
                    className="text-xs text-gray-500 hover:text-gray-400"
                  >
                    {showValues[secret.key] ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
              </div>
              <button
                onClick={() => deleteSecret(secret.key)}
                className="ml-2 p-1 text-gray-500 hover:text-red-400 hover:bg-gray-700 rounded"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default function Settings() {
  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-900 border-b border-gray-800">
        <h1 className="text-xl font-bold text-gray-100">Settings</h1>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="max-w-2xl mx-auto p-6 space-y-8">
          <LLMSection />
          <div className="border-t border-gray-800" />
          <SecretsSection />
        </div>
      </div>
    </div>
  )
}
