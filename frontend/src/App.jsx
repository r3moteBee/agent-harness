import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import MemoryPage from './pages/MemoryPage'
import FilesPage from './pages/FilesPage'
import PersonalityPage from './pages/PersonalityPage'
import SettingsPage from './pages/SettingsPage'
import TasksPage from './pages/TasksPage'
import ProjectsPage from './pages/ProjectsPage'
import { useStore } from './store'
import { projectsApi } from './api/client'

export default function App() {
  const setProjects = useStore((s) => s.setProjects)
  const setActiveProject = useStore((s) => s.setActiveProject)

  useEffect(() => {
    projectsApi.list().then((res) => {
      const projects = res.data.projects || []
      setProjects(projects)
      if (projects.length > 0) {
        setActiveProject(projects[0])
      }
    }).catch(console.error)
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="memory" element={<MemoryPage />} />
          <Route path="files" element={<FilesPage />} />
          <Route path="personality" element={<PersonalityPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
