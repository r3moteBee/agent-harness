import React, { useState } from 'react'
import { Zap, ShieldCheck } from 'lucide-react'
import Skills from '../components/Skills'
import SkillScanDashboard from '../components/SkillScanDashboard'

export default function SkillsPage() {
  const [tab, setTab] = useState('library')

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center border-b border-gray-800 px-6 pt-4">
        <button
          onClick={() => setTab('library')}
          className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
            tab === 'library'
              ? 'border-brand-400 text-brand-300'
              : 'border-transparent text-gray-500 hover:text-gray-300'
          }`}
        >
          <Zap className="w-3.5 h-3.5" />
          Library
        </button>
        <button
          onClick={() => setTab('security')}
          className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
            tab === 'security'
              ? 'border-brand-400 text-brand-300'
              : 'border-transparent text-gray-500 hover:text-gray-300'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          Security
        </button>
      </div>
      <div className="flex-1 overflow-hidden">
        {tab === 'library' ? <Skills /> : <SkillScanDashboard />}
      </div>
    </div>
  )
}
