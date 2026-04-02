import React, { useState, useRef, useEffect } from 'react'
import { ChevronRight, Download, Trash2, FolderPlus, Upload, File, Folder, ArrowLeft, RefreshCw } from 'lucide-react'
import { useStore } from '../store'
import { filesApi } from '../api/client'

export default function FileRepository() {
  const [currentPath, setCurrentPath] = useState('')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(false)
  const [fileContent, setFileContent] = useState(null)
  const [previewFile, setPreviewFile] = useState(null)
  const fileInputRef = useRef(null)
  const [folderName, setFolderName] = useState('')
  const [showNewFolder, setShowNewFolder] = useState(false)

  const activeProject = useStore((s) => s.activeProject)
  const addNotification = useStore((s) => s.addNotification)

  const loadFiles = async (path = '') => {
    setLoading(true)
    try {
      const res = await filesApi.list(activeProject?.id || 'default', path)
      // API returns { directories: [...], files: [...] } — merge into one list,
      // directories first, then files, each tagged with is_dir.
      const dirs  = (res.data.directories || []).map(d => ({ ...d, is_dir: true }))
      const files = (res.data.files      || []).map(f => ({ ...f, is_dir: false }))
      setItems([...dirs, ...files])
      setCurrentPath(path)
      setFileContent(null)
      setPreviewFile(null)
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
    setLoading(false)
  }

  useEffect(() => {
    loadFiles()
  }, [activeProject])

  const getBreadcrumbs = () => {
    if (!currentPath) return []
    return currentPath.split('/').filter(p => p)
  }

  const navigateTo = (path) => {
    loadFiles(path)
  }

  const openFolder = (name) => {
    const newPath = currentPath ? `${currentPath}/${name}` : name
    navigateTo(newPath)
  }

  const goBack = () => {
    if (!currentPath) return
    const parts = currentPath.split('/')
    parts.pop()
    const newPath = parts.join('/')
    navigateTo(newPath)
  }

  const deleteItem = async (name, isFolder) => {
    if (!confirm(`Delete ${isFolder ? 'folder' : 'file'} "${name}"?`)) return

    const path = currentPath ? `${currentPath}/${name}` : name
    try {
      await filesApi.delete(path, activeProject?.id || 'default')
      addNotification({ type: 'success', message: 'Deleted successfully' })
      loadFiles(currentPath)
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }

  const previewTextFile = async (name) => {
    const path = currentPath ? `${currentPath}/${name}` : name
    try {
      const res = await filesApi.read(path, activeProject?.id || 'default')
      setFileContent(res.data.content)
      setPreviewFile(name)
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }

  const uploadFile = async (file) => {
    try {
      await filesApi.upload(file, activeProject?.id || 'default', currentPath)
      addNotification({ type: 'success', message: 'File uploaded' })
      loadFiles(currentPath)
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }

  const createFolder = async () => {
    if (!folderName.trim()) return
    const path = currentPath ? `${currentPath}/${folderName}` : folderName
    try {
      await filesApi.mkdir(path, activeProject?.id || 'default')
      addNotification({ type: 'success', message: 'Folder created' })
      setFolderName('')
      setShowNewFolder(false)
      loadFiles(currentPath)
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }

  const isTextFile = (name) => {
    const exts = ['.txt', '.md', '.json', '.js', '.py', '.html', '.css', '.yml', '.yaml']
    return exts.some(ext => name.toLowerCase().endsWith(ext))
  }

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-900 border-b border-gray-800">
        <h1 className="text-xl font-bold text-gray-100">File Repository</h1>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* File browser */}
        <div className="flex-1 flex flex-col border-r border-gray-800">
          {/* Breadcrumb and actions */}
          <div className="px-6 py-3 bg-gray-900 border-b border-gray-800 space-y-3">
            <div className="flex items-center gap-2">
              {currentPath && (
                <button
                  onClick={goBack}
                  className="p-1 hover:bg-gray-800 rounded"
                  title="Go back"
                >
                  <ArrowLeft className="w-4 h-4 text-gray-400" />
                </button>
              )}
              <div className="flex items-center gap-1 text-sm text-gray-400">
                <span>/</span>
                {getBreadcrumbs().map((part, i, arr) => (
                  <React.Fragment key={i}>
                    <button
                      onClick={() => {
                        const path = arr.slice(0, i + 1).join('/')
                        navigateTo(path)
                      }}
                      className="text-brand-400 hover:text-brand-300"
                    >
                      {part}
                    </button>
                    {i < arr.length - 1 && <span>/</span>}
                  </React.Fragment>
                ))}
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 px-3 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm rounded-lg"
              >
                <Upload className="w-4 h-4" />
                Upload
              </button>
              <button
                onClick={() => setShowNewFolder(!showNewFolder)}
                className="flex items-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg"
              >
                <FolderPlus className="w-4 h-4" />
                New Folder
              </button>
              <button
                onClick={() => loadFiles(currentPath)}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg disabled:opacity-50"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    uploadFile(e.target.files[0])
                  }
                }}
                className="hidden"
              />
            </div>

            {/* New folder form */}
            {showNewFolder && (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={folderName}
                  onChange={(e) => setFolderName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') createFolder()
                    if (e.key === 'Escape') {
                      setShowNewFolder(false)
                      setFolderName('')
                    }
                  }}
                  placeholder="Folder name..."
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-brand-500"
                  autoFocus
                />
                <button
                  onClick={createFolder}
                  className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg"
                >
                  Create
                </button>
              </div>
            )}
          </div>

          {/* File list */}
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            {items.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                No files or folders
              </div>
            ) : (
              <div className="divide-y divide-gray-800">
                {items.map((item) => (
                  <div key={item.name} className="flex items-center gap-3 px-6 py-3 hover:bg-gray-800 transition-colors group">
                    <button
                      onClick={() => item.is_dir ? openFolder(item.name) : previewTextFile(item.name)}
                      className="flex-1 flex items-center gap-3 min-w-0"
                    >
                      {item.is_dir ? (
                        <Folder className="w-4 h-4 text-blue-400 flex-shrink-0" />
                      ) : (
                        <File className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      )}
                      <span className="text-sm text-gray-300 truncate">{item.name}</span>
                      {!item.is_dir && item.size && (
                        <span className="text-xs text-gray-600 flex-shrink-0">
                          {(item.size / 1024).toFixed(1)} KB
                        </span>
                      )}
                    </button>

                    {!item.is_dir && (
                      <a
                        href={filesApi.downloadUrl(
                          currentPath ? `${currentPath}/${item.name}` : item.name,
                          activeProject?.id || 'default'
                        )}
                        download
                        className="p-1 text-gray-500 hover:text-green-400 opacity-0 group-hover:opacity-100"
                        title="Download"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    )}

                    <button
                      onClick={() => deleteItem(item.name, item.is_dir)}
                      className="p-1 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Preview pane */}
        {previewFile && fileContent !== null && (
          <div className="w-96 flex flex-col border-l border-gray-800 bg-gray-900">
            <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
              <p className="text-sm font-medium text-gray-300 truncate">{previewFile}</p>
              <button
                onClick={() => {
                  setPreviewFile(null)
                  setFileContent(null)
                }}
                className="p-1 text-gray-500 hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin">
              <pre className="p-4 text-xs text-gray-300 whitespace-pre-wrap break-words">
                {fileContent}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function X(props) {
  return <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M18 6l-12 12M6 6l12 12"/></svg>
}
