# Pantheon Frontend - Complete File Index

**Total Files**: 32  
**Location**: `/sessions/friendly-happy-maxwell/mnt/outputs/pantheon/frontend/`

## Quick Links

- **Start Here**: [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
- **Full Docs**: [README.md](README.md) - Complete documentation
- **File Summary**: [BUILD_SUMMARY.txt](BUILD_SUMMARY.txt) - Detailed inventory
- **Completion Report**: [COMPLETION_REPORT.md](COMPLETION_REPORT.md) - Project status

---

## Configuration Files (7)

| File | Purpose | Key Settings |
|------|---------|--------------|
| `package.json` | Dependencies and scripts | React 18.3, Vite 5.2, Tailwind 3.4 |
| `vite.config.js` | Dev server config | Port 5173, API proxy to :8000 |
| `tailwind.config.js` | Tailwind customization | Dark theme, brand colors |
| `postcss.config.js` | CSS processing | Tailwind, autoprefixer |
| `index.html` | HTML entry point | Root div, CSS import |
| `Dockerfile` | Container build | Multi-stage, Node + Nginx |
| `nginx.conf` | Reverse proxy | SPA routing, gzip |

## Source Code (18)

### Root (3 files)
- `src/main.jsx` - React root with StrictMode
- `src/App.jsx` - Routes to 7 pages + navigation
- `src/index.css` - Tailwind + custom styles

### API Integration (1 file)
- `src/api/client.js` - 7 API modules + WebSocket helper

### State Management (1 file)
- `src/store/index.js` - Zustand store (12 slices)

### Components (8 files)
1. `src/components/Layout.jsx` - Sidebar + nav + notifications
2. `src/components/Chat.jsx` - Chat interface + streaming
3. `src/components/MemoryBrowser.jsx` - Memory tiers
4. `src/components/FileRepository.jsx` - File explorer
5. `src/components/PersonalityEditor.jsx` - Soul/Agent editor
6. `src/components/Settings.jsx` - LLM + secrets config
7. `src/components/TaskMonitor.jsx` - Task scheduler
8. `src/components/Projects.jsx` - Project manager

### Pages (7 files)
- `src/pages/ChatPage.jsx`
- `src/pages/MemoryPage.jsx`
- `src/pages/FilesPage.jsx`
- `src/pages/PersonalityPage.jsx`
- `src/pages/SettingsPage.jsx`
- `src/pages/TasksPage.jsx`
- `src/pages/ProjectsPage.jsx`

## Documentation (3)

- `README.md` - Complete feature docs + API reference
- `QUICKSTART.md` - Setup and first steps
- `BUILD_SUMMARY.txt` - Detailed file breakdown
- `COMPLETION_REPORT.md` - Project completion status
- `INDEX.md` - This file

---

## Features by Page

### Chat
- Real-time WebSocket streaming
- Tool call visualization
- Markdown with syntax highlighting
- Session management
- Keyboard shortcuts

### Memory
- 4 tiers: Episodic, Semantic, Graph, Archival
- Search and filter
- Similarity scores
- Node/edge visualization
- Delete with confirmation

### Files
- Breadcrumb navigation
- Upload/download
- Create folders
- Text preview
- File operations

### Personality
- Dual-pane editor
- Soul and Agent tabs
- Markdown preview
- Save per-project
- Reload functionality

### Settings
- LLM endpoint config
- API key management
- Model selection
- Connection testing
- Secret storage

### Tasks
- Create scheduled tasks
- Real-time logs
- Task status tracking
- Cancel tasks
- Auto-refresh

### Projects
- Create/manage projects
- Set active project
- Project metadata
- Delete projects
- Grid layout

---

## API Integration Summary

### Implemented Endpoints

#### Chat (`chatApi`)
- `send(message, sessionId, projectId)` - Send message
- `getHistory(sessionId, projectId)` - Get chat history
- `getSessions(projectId)` - List sessions

#### Memory (`memoryApi`)
- `store(content, tier, projectId)` - Store memory
- `search(query, projectId)` - Search memories
- `listSemantic(projectId)` - List semantic docs
- `listNotes(projectId)` - List episodic notes
- `listGraphNodes(projectId)` - List graph nodes
- `listGraphEdges(projectId)` - List graph edges
- `deleteNote(noteId)` - Delete note
- `deleteSemantic(docId, projectId)` - Delete doc
- `deleteGraphNode(nodeId, projectId)` - Delete node
- `deleteGraphEdge(edgeId, projectId)` - Delete edge
- Plus create and consolidate operations

#### Files (`filesApi`)
- `list(projectId, path)` - List files/folders
- `read(path, projectId)` - Read file content
- `upload(file, projectId, path)` - Upload file
- `delete(path, projectId)` - Delete file
- `mkdir(path, projectId)` - Create folder
- `downloadUrl(path, projectId)` - Get download link

#### Settings (`settingsApi`)
- `get()` - Get settings
- `update(data)` - Update settings
- `listModels()` - Get available models
- `testConnection()` - Test LLM connection
- `listSecrets()` - List stored secrets
- `setSecret(key, value)` - Save secret
- `deleteSecret(key)` - Delete secret

#### Tasks (`tasksApi`)
- `list(projectId)` - List tasks
- `create(name, description, schedule, projectId)` - Create task
- `cancel(taskId)` - Cancel task
- `getLogs(taskId, projectId)` - Get task logs
- `getAllLogs(projectId)` - Get all logs

#### Personality (`personalityApi`)
- `getSoul(projectId)` - Get soul.md
- `updateSoul(content, projectId)` - Update soul
- `getAgent(projectId)` - Get agent.md
- `updateAgent(content, projectId)` - Update agent

#### Projects (`projectsApi`)
- `list()` - List all projects
- `create(name, description, id)` - Create project
- `get(projectId)` - Get project details
- `update(projectId, name, description)` - Update project
- `delete(projectId)` - Delete project

#### WebSocket
- `createChatSocket(onMessage)` - Real-time chat

---

## State Management (Zustand)

```javascript
// Store slices
activeProject      // Current project
sessionId         // Chat session ID
messages          // Chat history
isStreaming       // Streaming state
streamingContent  // Live message text
currentToolCalls  // Tool execution
projects          // Projects list
settings          // LLM config
sidebarOpen       // Mobile sidebar toggle
notifications     // Toast queue
```

---

## Getting Started

### Installation
```bash
cd frontend
npm install
npm run dev
# App on http://localhost:5173
```

### First Steps
1. Create a project (Projects page)
2. Configure LLM (Settings page)
3. Test connection
4. Start chatting (Chat page)

### Production
```bash
npm run build
docker build -t pantheon-frontend .
docker run -p 80:80 pantheon-frontend
```

---

## Component Relationships

```
App.jsx
  └─ BrowserRouter
      └─ Layout.jsx
          ├─ Sidebar (7 nav items)
          ├─ Notifications
          └─ Routes
              ├─ /chat → ChatPage → Chat.jsx
              ├─ /memory → MemoryPage → MemoryBrowser.jsx
              ├─ /files → FilesPage → FileRepository.jsx
              ├─ /personality → PersonalityPage → PersonalityEditor.jsx
              ├─ /settings → SettingsPage → Settings.jsx
              ├─ /tasks → TasksPage → TaskMonitor.jsx
              └─ /projects → ProjectsPage → Projects.jsx
```

---

## Data Flow

### Chat
1. User types message → Chat.jsx
2. Message stored locally → useStore
3. WebSocket sends to backend
4. Backend responds via WebSocket
5. Response streams in real-time
6. Message added to history

### Memory
1. Load memories → memoryApi
2. Display by tier (episodic/semantic/graph)
3. User searches/deletes
4. API call to backend
5. Refresh local list
6. Toast notification

### Files
1. Load folder contents → filesApi
2. Display in browser
3. User uploads/creates/deletes
4. API call to backend
5. Refresh folder contents
6. Update breadcrumb

### Settings
1. Load current settings → settingsApi
2. User modifies values
3. User clicks Save
4. Update sent to backend
5. Toast notification
6. Settings cached locally

---

## Styling Guide

### Colors
```
bg-gray-950    # Main background
bg-gray-900    # Panels
bg-gray-800    # Surfaces
text-gray-100  # Main text
text-gray-400  # Secondary
bg-brand-600   # Primary action
```

### Layout
```
Responsive:
- Mobile: < 768px (full width)
- Tablet: 768px - 1024px (sidebar visible)
- Desktop: > 1024px (fixed sidebar)
```

### Components
```
rounded-lg     # Card corners
px-4 py-3      # Standard padding
shadow-lg      # Drop shadows
border border-gray-700  # Dividers
```

---

## Performance Tips

1. **State**: Use selector functions → `useStore(s => s.items)`
2. **Lists**: Add keys to mapped elements
3. **Async**: Always handle errors + loading states
4. **Images**: Use lucide icons (SVG, lightweight)
5. **Scrolling**: Use `.scrollbar-thin` for custom scroll

---

## Browser DevTools Tips

1. **Network Tab**: Check API calls to backend
2. **Console**: Look for errors and warnings
3. **React DevTools**: Inspect component state
4. **Storage Tab**: Check localStorage if used
5. **Application Tab**: Verify CSS is loading

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API fails | Check backend running on :8000 |
| Chat not streaming | Verify WebSocket in Network tab |
| Styles broken | Hard refresh (Ctrl+Shift+R) |
| Build errors | Delete node_modules, run npm install |
| Port 5173 busy | Change port in vite.config.js |

---

## Environment Setup

Required:
- Node.js 18+
- npm or yarn
- Backend on http://localhost:8000

Optional:
- Docker (for production)
- React DevTools browser extension

---

## Code Structure

Each component follows this pattern:
```jsx
import { useEffect, useState } from 'react'
import { useStore } from '../store'
import { someApi } from '../api/client'

export default function MyComponent() {
  const [state, setState] = useState(null)
  const activeProject = useStore(s => s.activeProject)
  const addNotification = useStore(s => s.addNotification)
  
  useEffect(() => {
    loadData()
  }, [activeProject])
  
  const loadData = async () => {
    try {
      const res = await someApi.method(activeProject.id)
      setState(res.data)
    } catch (err) {
      addNotification({ type: 'error', message: err.message })
    }
  }
  
  return (/* JSX */)
}
```

---

## File Format Summary

| Extension | Purpose | Count |
|-----------|---------|-------|
| `.jsx` | React components | 18 |
| `.js` | Plain JavaScript | 2 |
| `.json` | Configuration | 1 |
| `.html` | HTML entry | 1 |
| `.css` | Styles | 1 |
| `.conf` | Nginx config | 1 |
| `.md` | Markdown docs | 4 |
| `.txt` | Text files | 1 |
| `Dockerfile` | Container | 1 |

---

## Next Steps

1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `npm install && npm run dev`
3. Visit http://localhost:5173
4. Create a project
5. Configure your LLM
6. Start using Pantheon!

---

**Last Updated**: March 29, 2026  
**Status**: Production Ready
